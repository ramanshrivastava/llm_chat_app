from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.models.chat import Conversation, ChatMessage, UsageLog


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation operations."""
    
    def __init__(self, db_session: Session):
        super().__init__(Conversation, db_session)
    
    def get_user_conversations(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Conversation]:
        """Get conversations for a specific user."""
        return (
            self.db_session.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_with_messages(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation with all its messages."""
        return (
            self.db_session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
    
    def update_token_count(self, conversation_id: str, tokens: int) -> None:
        """Update the total token count for a conversation."""
        conversation = self.get(conversation_id)
        if conversation:
            conversation.total_tokens += tokens
            self.db_session.commit()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for chat message operations."""
    
    def __init__(self, db_session: Session):
        super().__init__(ChatMessage, db_session)
    
    def get_conversation_messages(
        self, 
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get all messages for a conversation."""
        query = (
            self.db_session.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_recent_messages(
        self,
        conversation_id: str,
        count: int = 10
    ) -> List[ChatMessage]:
        """Get the most recent messages from a conversation."""
        return (
            self.db_session.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(count)
            .all()
        )[::-1]  # Reverse to get chronological order
    
    def bulk_create(self, messages: List[Dict[str, Any]]) -> List[ChatMessage]:
        """Create multiple messages at once."""
        db_messages = [ChatMessage(**msg) for msg in messages]
        self.db_session.add_all(db_messages)
        self.db_session.commit()
        return db_messages


class UsageLogRepository(BaseRepository[UsageLog]):
    """Repository for usage tracking operations."""
    
    def __init__(self, db_session: Session):
        super().__init__(UsageLog, db_session)
    
    def get_user_usage(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        query = self.db_session.query(
            func.sum(UsageLog.total_tokens).label("total_tokens"),
            func.sum(UsageLog.estimated_cost).label("total_cost"),
            func.count(UsageLog.id).label("request_count"),
            func.avg(UsageLog.response_time_ms).label("avg_response_time")
        ).filter(UsageLog.user_id == user_id)
        
        if start_date:
            query = query.filter(UsageLog.created_at >= start_date)
        if end_date:
            query = query.filter(UsageLog.created_at <= end_date)
        
        result = query.first()
        
        return {
            "total_tokens": result.total_tokens or 0,
            "total_cost": result.total_cost or 0.0,
            "request_count": result.request_count or 0,
            "avg_response_time_ms": result.avg_response_time or 0
        }
    
    def get_model_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage breakdown by model."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = (
            self.db_session.query(
                UsageLog.model,
                func.count(UsageLog.id).label("request_count"),
                func.sum(UsageLog.total_tokens).label("total_tokens"),
                func.sum(UsageLog.estimated_cost).label("total_cost")
            )
            .filter(UsageLog.created_at >= start_date)
            .group_by(UsageLog.model)
            .all()
        )
        
        return [
            {
                "model": r.model,
                "request_count": r.request_count,
                "total_tokens": r.total_tokens or 0,
                "total_cost": r.total_cost or 0.0
            }
            for r in results
        ]
    
    def log_usage(
        self,
        endpoint: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        response_time_ms: int,
        status_code: int,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> UsageLog:
        """Log API usage."""
        total_tokens = prompt_tokens + completion_tokens
        
        # Estimate cost based on model (simplified example)
        cost_per_1k_tokens = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
            "claude-3": 0.015,
        }
        rate = cost_per_1k_tokens.get(model, 0.01)
        estimated_cost = (total_tokens / 1000) * rate
        
        return self.create(
            user_id=user_id,
            endpoint=endpoint,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            response_time_ms=response_time_ms,
            status_code=status_code,
            error_message=error_message
        )