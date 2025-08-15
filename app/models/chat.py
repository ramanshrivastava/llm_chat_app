from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Conversation(BaseModel):
    """Model for storing chat conversations."""
    __tablename__ = "conversations"
    
    user_id = Column(String, nullable=True)  # Optional user tracking
    title = Column(String(255), nullable=True)
    model = Column(String(100), nullable=False)
    total_tokens = Column(Integer, default=0)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(BaseModel):
    """Model for storing individual chat messages."""
    __tablename__ = "chat_messages"
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)  # Store additional data like function calls
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class UsageLog(BaseModel):
    """Model for tracking API usage and costs."""
    __tablename__ = "usage_logs"
    
    user_id = Column(String, nullable=True)
    endpoint = Column(String(255), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)