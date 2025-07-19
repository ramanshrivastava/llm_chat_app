from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import types

# Insert a stub for the agent module so tests don't depend on langgraph
agent_stub = types.ModuleType("app.agents.langgraph_agent")
class DummyAgent:
    async def invoke(self, request):
        raise NotImplementedError
agent_stub.langgraph_agent = DummyAgent()
sys.modules.setdefault("app.agents.langgraph_agent", agent_stub)

from app.main import app
from app.schemas.chat import Message, ChatResponse

client = TestClient(app)


def test_root_page_contains_elements():
    resp = client.get("/")
    assert resp.status_code == 200
    text = resp.text
    assert "LLM Chat App" in text
    assert 'id="chatMessages"' in text
    assert 'id="sendButton"' in text


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_chat_endpoint():
    mock_response = ChatResponse(message=Message(role="assistant", content="Hi"), model="gpt-4")
    with patch("app.api.chat.langgraph_agent.invoke", new=AsyncMock(return_value=mock_response)):
        resp = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Hi"}]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]["content"] == "Hi"
    assert data["model"] == "gpt-4"


def test_chat_with_system():
    mock_response = ChatResponse(message=Message(role="assistant", content="Hi"), model="gpt-4")
    with patch("app.api.chat.langgraph_agent.invoke", new=AsyncMock(return_value=mock_response)):
        resp = client.post(
            "/api/chat/system",
            params={"system_message": "sys", "user_message": "hello"},
        )
    assert resp.status_code == 200
    assert resp.json()["message"]["content"] == "Hi"


def test_chat_stream():
    async def fake_stream(_request):
        for part in ["Hello", "World"]:
            yield part
    with patch("app.api.chat.llm_service.stream_response", new=fake_stream):
        resp = client.post("/api/chat/stream", json={"messages": [{"role": "user", "content": "Hi"}]})
    assert resp.status_code == 200
    text = resp.text
    assert "Hello" in text
    assert "World" in text
    assert "[DONE]" in text
