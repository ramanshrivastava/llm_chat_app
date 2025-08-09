import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import types
import json
import time

# Insert a stub for the agent module so tests don't depend on langgraph
agent_stub = types.ModuleType("app.agents.langgraph_agent")
class DummyAgent:
    async def invoke(self, request):
        raise NotImplementedError
agent_stub.langgraph_agent = DummyAgent()
sys.modules.setdefault("app.agents.langgraph_agent", agent_stub)

from app.main import app  # noqa: E402
from app.schemas.chat import Message, ChatResponse  # noqa: E402

client = TestClient(app)


class TestBasicEndpoints:
    """Test basic application endpoints."""

    def test_root_page_contains_elements(self):
        """Test that root page loads with expected elements."""
        resp = client.get("/")
        assert resp.status_code == 200
        text = resp.text
        assert "LLM Chat App" in text
        assert 'id="chatMessages"' in text
        assert 'id="sendButton"' in text
        assert 'id="userInput"' in text
        assert 'id="modelSelect"' in text

    def test_health_check(self):
        """Test health check endpoint."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "provider" in data

    def test_404_error(self):
        """Test 404 error handling."""
        resp = client.get("/nonexistent")
        assert resp.status_code == 404


class TestChatEndpoints:
    """Test chat API endpoints."""

    def test_chat_endpoint_success(self):
        """Test successful chat endpoint call."""
        mock_response = ChatResponse(
            message=Message(role="assistant", content="Hello!"),
            model="gpt-4"
        )
        with patch("app.api.chat.langgraph_agent.invoke", new=AsyncMock(return_value=mock_response)):
            resp = client.post("/api/chat", json={
                "messages": [{"role": "user", "content": "Hi"}]
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"]["content"] == "Hello!"
        assert data["model"] == "gpt-4"

    def test_chat_endpoint_empty_messages(self):
        """Test chat endpoint with empty messages."""
        resp = client.post("/api/chat", json={"messages": []})
        assert resp.status_code == 400
        assert "Messages cannot be empty" in resp.json()["detail"]

    def test_chat_endpoint_too_many_messages(self):
        """Test chat endpoint with too many messages."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(51)]
        resp = client.post("/api/chat", json={"messages": messages})
        assert resp.status_code == 400
        assert "Too many messages" in resp.json()["detail"]

    def test_chat_endpoint_message_too_long(self):
        """Test chat endpoint with excessively long message."""
        long_content = "x" * 10001  # Exceeds 10k limit
        resp = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": long_content}]
        })
        assert resp.status_code == 400
        assert "Message content too long" in resp.json()["detail"]

    def test_chat_endpoint_invalid_temperature(self):
        """Test chat endpoint with invalid temperature."""
        resp = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": 3.0  # Above max
        })
        assert resp.status_code == 422  # Pydantic validation error

    def test_chat_endpoint_agent_error(self):
        """Test chat endpoint when agent raises error."""
        with patch("app.api.chat.langgraph_agent.invoke", side_effect=Exception("Agent error")):
            resp = client.post("/api/chat", json={
                "messages": [{"role": "user", "content": "Hi"}]
            })
        assert resp.status_code == 500
        assert "Failed to generate response" in resp.json()["detail"]


class TestChatWithSystemEndpoint:
    """Test chat with system message endpoint."""

    def test_chat_with_system_success(self):
        """Test successful chat with system message."""
        mock_response = ChatResponse(
            message=Message(role="assistant", content="System response"),
            model="gpt-4"
        )
        with patch("app.api.chat.langgraph_agent.invoke", new=AsyncMock(return_value=mock_response)):
            resp = client.post("/api/chat/system", params={
                "system_message": "You are a helpful assistant",
                "user_message": "Hello"
            })
        assert resp.status_code == 200
        assert resp.json()["message"]["content"] == "System response"

    def test_chat_with_system_empty_messages(self):
        """Test system endpoint with empty messages."""
        resp = client.post("/api/chat/system", params={
            "system_message": "",
            "user_message": "Hello"
        })
        assert resp.status_code == 400
        assert "System message cannot be empty" in resp.json()["detail"]

    def test_chat_with_system_invalid_temperature(self):
        """Test system endpoint with invalid temperature."""
        resp = client.post("/api/chat/system", params={
            "system_message": "System",
            "user_message": "Hello",
            "temperature": -1.0
        })
        assert resp.status_code == 400
        assert "Temperature must be between" in resp.json()["detail"]

    def test_chat_with_system_long_messages(self):
        """Test system endpoint with long messages."""
        long_system = "x" * 5001
        resp = client.post("/api/chat/system", params={
            "system_message": long_system,
            "user_message": "Hello"
        })
        assert resp.status_code == 400
        assert "System message too long" in resp.json()["detail"]


class TestChatStreamEndpoint:
    """Test chat streaming endpoint."""

    def test_chat_stream_success(self):
        """Test successful streaming response."""
        async def fake_stream(_request):
            for part in ["Hello", " ", "World"]:
                yield part

        with patch("app.api.chat.llm_service.stream_response", new=fake_stream):
            resp = client.post("/api/chat/stream", json={
                "messages": [{"role": "user", "content": "Hi"}]
            })
        assert resp.status_code == 200
        text = resp.text
        assert "Hello" in text
        assert "World" in text
        assert "[DONE]" in text

    def test_chat_stream_empty_messages(self):
        """Test streaming with empty messages."""
        resp = client.post("/api/chat/stream", json={"messages": []})
        assert resp.status_code == 400
        assert "Messages cannot be empty" in resp.json()["detail"]

    def test_chat_stream_service_error(self):
        """Test streaming when service raises error."""
        async def error_stream(_request):
            raise Exception("Stream error")
            yield "Won't reach here"  # pragma: no cover

        with patch("app.api.chat.llm_service.stream_response", new=error_stream):
            resp = client.post("/api/chat/stream", json={
                "messages": [{"role": "user", "content": "Hi"}]
            })
        assert resp.status_code == 200  # Stream starts successfully
        # Error should be in the stream content
        text = resp.text
        assert "error" in text.lower()


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_basic(self):
        """Test basic rate limiting behavior."""
        # Make requests rapidly to trigger rate limit
        mock_response = ChatResponse(
            message=Message(role="assistant", content="Hi"),
            model="gpt-4"
        )
        
        with patch("app.api.chat.langgraph_agent.invoke", new=AsyncMock(return_value=mock_response)):
            # First request should succeed
            resp = client.post("/api/chat", json={
                "messages": [{"role": "user", "content": "Hi"}]
            })
            assert resp.status_code == 200

            # Simulate many rapid requests by patching the rate limit store
            with patch("app.api.chat._rate_limit_store", {"127.0.0.1": {"count": 100, "window_start": time.time()}}):
                resp = client.post("/api/chat", json={
                    "messages": [{"role": "user", "content": "Hi"}]
                })
                assert resp.status_code == 429
                assert "Rate limit exceeded" in resp.json()["detail"]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        resp = client.post("/api/chat", data="invalid json")
        assert resp.status_code == 422  # Unprocessable entity

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 422

    def test_invalid_message_roles(self):
        """Test handling of invalid message roles."""
        resp = client.post("/api/chat", json={
            "messages": [{"role": "invalid_role", "content": "Hi"}]
        })
        assert resp.status_code == 422


@pytest.fixture
def mock_settings():
    """Fixture to mock settings for tests."""
    with patch('app.core.config.settings') as mock:
        mock.RATE_LIMIT_REQUESTS = 5
        mock.RATE_LIMIT_WINDOW = 60
        yield mock
