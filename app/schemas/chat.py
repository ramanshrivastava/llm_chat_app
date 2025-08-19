from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Message(BaseModel):
    """Schema for a chat message."""
    role: Literal["user", "assistant", "system"] = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="The timestamp of the message")

class ChatRequest(BaseModel):
    """Schema for a chat request."""
    messages: List[Message] = Field(..., description="The list of messages in the conversation")
    model: Optional[str] = Field(None, description="The model to use for the response")
    temperature: Optional[float] = Field(0.7, description="The temperature to use for the response", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description="The maximum number of tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    provider: Optional[str] = Field(None, description="Override the default provider (e.g., 'ollama' for local models)")

class ChatResponse(BaseModel):
    """Schema for a chat response."""
    message: Message = Field(..., description="The response message")
    model: str = Field(..., description="The model used for the response")
    usage: Optional[dict] = Field(None, description="The token usage information")

class ChatHistory(BaseModel):
    """Schema for chat history."""
    id: str = Field(..., description="The unique identifier for the chat")
    title: Optional[str] = Field(None, description="The title of the chat")
    messages: List[Message] = Field(default_factory=list, description="The list of messages in the chat")
    created_at: datetime = Field(default_factory=datetime.now, description="The creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="The last update timestamp") 