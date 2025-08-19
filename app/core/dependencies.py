from __future__ import annotations
from functools import lru_cache
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request
import time
import logging

from app.core.config import Settings
from app.services.llm_service import LLMService
from app.agents.langgraph_agent import LangGraphAgent


logger = logging.getLogger(__name__)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache()
def get_llm_service(settings: Annotated[Settings, Depends(get_settings)]) -> LLMService:
    """Get cached LLM service instance."""
    from app.services.llm_service import llm_service
    return llm_service


@lru_cache()
def get_langgraph_agent(settings: Annotated[Settings, Depends(get_settings)]) -> LangGraphAgent:
    """Get cached LangGraph agent instance."""
    from app.agents.langgraph_agent import langgraph_agent
    return langgraph_agent


class RateLimiter:
    """Rate limiter dependency."""
    
    def __init__(self):
        self._store = {}
    
    async def __call__(
        self, 
        request: Request,
        settings: Annotated[Settings, Depends(get_settings)]
    ) -> None:
        """Check rate limit for the current request."""
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip not in self._store:
            self._store[client_ip] = {"count": 0, "window_start": current_time}
        
        client_data = self._store[client_ip]
        
        if current_time - client_data["window_start"] > settings.RATE_LIMIT_WINDOW:
            client_data["count"] = 0
            client_data["window_start"] = current_time
        
        if client_data["count"] >= settings.RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        client_data["count"] += 1


rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return rate_limiter


async def verify_api_key(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)]
) -> Optional[str]:
    """Verify API key from headers if required."""
    if settings.APP_ENV == "production":
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key required"
            )
        # In production, verify against actual API key storage
        # For now, just return the key
        return api_key
    return None
