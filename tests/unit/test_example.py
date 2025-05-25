import pytest
import sys
from pathlib import Path

# Ensure the 'app' package is importable when tests are run directly
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.schemas.chat import Message, ChatRequest, ChatResponse

def test_message_schema():
    """Test the Message schema."""
    message = Message(role="user", content="Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"
    assert message.timestamp is not None

def test_chat_request_schema():
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

def test_chat_response_schema():
    """Test the ChatResponse schema."""
    message = Message(role="assistant", content="Hello, how can I help you?")
    response = ChatResponse(message=message, model="gpt-4")
    assert response.message.role == "assistant"
    assert response.message.content == "Hello, how can I help you?"
    assert response.model == "gpt-4"
    assert response.usage is None
