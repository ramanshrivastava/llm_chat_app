"""
Client manager for handling connection pooling and singleton patterns for LLM providers.
This module provides optimized, reusable clients with connection pooling to improve performance.
"""

import logging
import httpx
import openai
from typing import Optional, Dict, Any
from threading import Lock

from app.core.config import settings

logger = logging.getLogger(__name__)

class ClientManager:
    """Singleton manager for LLM provider clients with connection pooling."""
    
    _instance = None
    _lock = Lock()
    _clients: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            logger.info("Initializing ClientManager with connection pooling")
    
    def _get_http_limits(self) -> httpx.Limits:
        """Get optimized HTTP connection limits for API clients."""
        return httpx.Limits(
            max_connections=settings.HTTP_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE,
            keepalive_expiry=settings.HTTP_KEEPALIVE_EXPIRY
        )
    
    def _get_http_timeout(self) -> httpx.Timeout:
        """Get optimized timeout configuration."""
        return httpx.Timeout(
            connect=settings.HTTP_CONNECTION_TIMEOUT,
            read=settings.API_REQUEST_TIMEOUT,
            write=settings.HTTP_CONNECTION_TIMEOUT,
            pool=settings.HTTP_CONNECTION_TIMEOUT
        )
    
    def get_openai_client(self) -> openai.AsyncOpenAI:
        """Get or create a persistent OpenAI client with connection pooling."""
        if "openai" not in self._clients:
            logger.info("Creating OpenAI client with connection pooling")
            
            # Create httpx client with connection pooling
            http_client = httpx.AsyncClient(
                limits=self._get_http_limits(),
                timeout=self._get_http_timeout()
            )
            
            self._clients["openai"] = openai.AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_ENDPOINT,
                http_client=http_client
            )
            logger.info(f"OpenAI client initialized with max_connections={settings.HTTP_MAX_CONNECTIONS}, "
                       f"max_keepalive={settings.HTTP_MAX_KEEPALIVE}")
        
        return self._clients["openai"]
    
    def get_anthropic_client(self):
        """Get or create a persistent Anthropic client with connection pooling."""
        if "anthropic" not in self._clients:
            try:
                import anthropic
                logger.info("Creating Anthropic client with connection pooling")
                
                # Create httpx client with connection pooling
                http_client = httpx.AsyncClient(
                    limits=self._get_http_limits(),
                    timeout=self._get_http_timeout()
                )
                
                self._clients["anthropic"] = anthropic.AsyncAnthropic(
                    api_key=settings.LLM_API_KEY,
                    http_client=http_client
                )
                logger.info(f"Anthropic client initialized with connection pooling")
            except ImportError as e:
                raise ImportError("anthropic package is required for Anthropic provider") from e
        
        return self._clients["anthropic"]
    
    def get_ollama_client(self):
        """Get or create a persistent Ollama client."""
        if "ollama" not in self._clients:
            try:
                import ollama
                logger.info("Creating Ollama client with connection pooling")
                
                # Ollama client handles connection pooling internally
                if settings.OLLAMA_BASE_URL != "http://localhost:11434":
                    self._clients["ollama"] = ollama.AsyncClient(
                        host=settings.OLLAMA_BASE_URL,
                        timeout=settings.API_REQUEST_TIMEOUT
                    )
                else:
                    self._clients["ollama"] = ollama.AsyncClient(
                        timeout=settings.API_REQUEST_TIMEOUT
                    )
                logger.info(f"Ollama client initialized for {settings.OLLAMA_BASE_URL}")
            except ImportError as e:
                raise ImportError("ollama package is required for Ollama provider") from e
        
        return self._clients["ollama"]
    
    def get_gemini_client(self):
        """Get or create a persistent Gemini client."""
        if "gemini" not in self._clients:
            try:
                import google.generativeai as genai
                logger.info("Creating Gemini client")
                
                genai.configure(api_key=settings.LLM_API_KEY)
                self._clients["gemini"] = genai.GenerativeModel(settings.LLM_MODEL)
                logger.info(f"Gemini client initialized with model {settings.LLM_MODEL}")
            except ImportError as e:
                raise ImportError("google-generativeai package is required for Gemini provider") from e
        
        return self._clients["gemini"]
    
    async def close_all_clients(self):
        """Close all HTTP clients and clean up resources."""
        logger.info("Closing all LLM clients")
        
        for provider, client in self._clients.items():
            try:
                if provider == "openai" and hasattr(client, 'close'):
                    await client.close()
                elif provider == "anthropic" and hasattr(client, 'close'):
                    await client.close()
                elif provider == "ollama" and hasattr(client, 'close'):
                    await client.close()
                # Gemini doesn't need explicit closing
                logger.debug(f"Closed {provider} client")
            except Exception as e:
                logger.warning(f"Error closing {provider} client: {e}")
        
        self._clients.clear()
        logger.info("All LLM clients closed")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get statistics about active clients."""
        stats = {
            "active_clients": list(self._clients.keys()),
            "client_count": len(self._clients),
            "connection_pool_config": {
                "max_connections": settings.HTTP_MAX_CONNECTIONS,
                "max_keepalive": settings.HTTP_MAX_KEEPALIVE,
                "keepalive_expiry": settings.HTTP_KEEPALIVE_EXPIRY,
                "connection_timeout": settings.HTTP_CONNECTION_TIMEOUT
            }
        }
        return stats

# Global singleton instance
client_manager = ClientManager()