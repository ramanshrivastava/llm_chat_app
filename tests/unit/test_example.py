import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.schemas.chat import Message, ChatRequest, ChatResponse, ChatHistory
from app.services.llm_service import LLMService
from app.core.config import Settings


class TestSchemas:
    """Test the Pydantic schemas."""

    def test_message_schema(self):
        """Test the Message schema."""
        message = Message(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.timestamp is not None
        assert isinstance(message.timestamp, datetime)

    def test_message_schema_with_timestamp(self):
        """Test Message schema with custom timestamp."""
        custom_time = datetime.now()
        message = Message(role="assistant", content="Hi!", timestamp=custom_time)
        assert message.timestamp == custom_time

    def test_chat_request_schema(self):
        """Test the ChatRequest schema."""
        messages = [
            Message(role="user", content="Hello, world!")
        ]
        request = ChatRequest(messages=messages)
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert request.messages[0].content == "Hello, world!"
        assert request.temperature == 0.7
        assert request.stream is False
        assert request.model is None
        assert request.max_tokens is None

    def test_chat_request_with_custom_params(self):
        """Test ChatRequest with custom parameters."""
        messages = [Message(role="user", content="Test")]
        request = ChatRequest(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=100,
            stream=True
        )
        assert request.model == "gpt-3.5-turbo"
        assert request.temperature == 0.5
        assert request.max_tokens == 100
        assert request.stream is True

    def test_chat_request_temperature_validation(self):
        """Test temperature validation in ChatRequest."""
        messages = [Message(role="user", content="Test")]
        
        # Valid temperatures
        ChatRequest(messages=messages, temperature=0.0)
        ChatRequest(messages=messages, temperature=1.0)
        ChatRequest(messages=messages, temperature=2.0)
        
        # Invalid temperatures should raise validation error
        with pytest.raises(Exception):
            ChatRequest(messages=messages, temperature=-0.1)
        with pytest.raises(Exception):
            ChatRequest(messages=messages, temperature=2.1)

    def test_chat_response_schema(self):
        """Test the ChatResponse schema."""
        message = Message(role="assistant", content="Hello, how can I help you?")
        response = ChatResponse(message=message, model="gpt-4")
        assert response.message.role == "assistant"
        assert response.message.content == "Hello, how can I help you?"
        assert response.model == "gpt-4"
        assert response.usage is None

    def test_chat_response_with_usage(self):
        """Test ChatResponse with usage information."""
        message = Message(role="assistant", content="Response")
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        response = ChatResponse(message=message, model="gpt-4", usage=usage)
        assert response.usage == usage

    def test_chat_history_schema(self):
        """Test the ChatHistory schema."""
        history = ChatHistory(id="test-123", title="Test Chat")
        assert history.id == "test-123"
        assert history.title == "Test Chat"
        assert len(history.messages) == 0
        assert isinstance(history.created_at, datetime)
        assert isinstance(history.updated_at, datetime)


class TestLLMService:
    """Test the LLM service functionality."""

    def test_llm_service_initialization(self):
        """Test LLM service initialization."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.API_REQUEST_TIMEOUT = 60
            mock_settings.LLM_API_KEY = "test-key-1234567890"
            mock_settings.LLM_API_ENDPOINT = "https://api.openai.com/v1"
            
            with patch('openai.AsyncOpenAI') as mock_openai:
                service = LLMService()
                assert service.provider == "openai"
                assert service.model == "gpt-4"
                mock_openai.assert_called_once()

    def test_format_messages(self):
        """Test message formatting."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.API_REQUEST_TIMEOUT = 60
            mock_settings.LLM_API_KEY = "test-key-1234567890"
            mock_settings.LLM_API_ENDPOINT = "https://api.openai.com/v1"
            
            with patch('openai.AsyncOpenAI'):
                service = LLMService()
                messages = [
                    Message(role="user", content="Hello"),
                    Message(role="assistant", content="Hi there!"),
                ]
                formatted = service.format_messages(messages)
                
                expected = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ]
                assert formatted == expected

    def test_format_messages_with_invalid_role(self):
        """Test message formatting with invalid role."""
        with pytest.raises(ValidationError):
            Message(role="unknown", content="Test")


class TestConfiguration:
    """Test configuration validation."""

    def test_settings_validation(self):
        """Test settings validation with valid values."""
        with patch.dict('os.environ', {
            'LLM_API_KEY': 'test-key-1234567890',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation',
            'LLM_PROVIDER': 'openai',
            'LOG_LEVEL': 'INFO'
        }):
            # This should not raise an exception
            settings = Settings()
            assert settings.LLM_PROVIDER == 'openai'
            assert settings.LOG_LEVEL == 'INFO'

    def test_settings_invalid_provider(self):
        """Test settings validation with invalid provider."""
        with patch.dict('os.environ', {
            'LLM_API_KEY': 'test-key-1234567890',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation',
            'LLM_PROVIDER': 'invalid-provider',
        }):
            with pytest.raises(Exception):
                Settings()

    def test_settings_short_api_key(self):
        """Test settings validation with short API key."""
        with patch.dict('os.environ', {
            'LLM_API_KEY': 'short',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough-for-validation',
        }):
            with pytest.raises(Exception):
                Settings()

    def test_settings_short_secret_key(self):
        """Test settings validation with short secret key."""
        with patch.dict('os.environ', {
            'LLM_API_KEY': 'test-key-1234567890',
            'SECRET_KEY': 'short',
        }):
            with pytest.raises(Exception):
                Settings()
