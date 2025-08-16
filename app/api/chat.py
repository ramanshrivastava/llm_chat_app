from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
import logging
import time

from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.agents.langgraph_agent import langgraph_agent
from app.services.llm_service import llm_service
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple rate limiting store (in production, use Redis)
_rate_limit_store: Dict[str, Dict[str, Any]] = {}

def rate_limit_check(request: Request) -> None:
    """Simple rate limiting based on client IP."""
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = {"count": 0, "window_start": current_time}
    
    client_data = _rate_limit_store[client_ip]
    
    # Reset window if expired
    if current_time - client_data["window_start"] > settings.RATE_LIMIT_WINDOW:
        client_data["count"] = 0
        client_data["window_start"] = current_time
    
    # Check rate limit
    if client_data["count"] >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    client_data["count"] += 1

class ChatController:
    """Controller handling chat related operations with improved error handling."""

    def __init__(self) -> None:
        self.agent = langgraph_agent
        self.service = llm_service

    async def generate(self, request: ChatRequest, thread_id: str = "default") -> ChatResponse:
        """Generate a chat response using the configured agent."""
        try:
            # Validate input
            if not request.messages:
                raise HTTPException(status_code=400, detail="Messages cannot be empty")
            
            if len(request.messages) > 50:  # Reasonable limit
                raise HTTPException(status_code=400, detail="Too many messages in conversation")
            
            # Check for excessively long messages
            for message in request.messages:
                if len(message.content) > 10000:  # 10k character limit
                    raise HTTPException(status_code=400, detail="Message content too long")
            
            logger.info(f"Generating response for {len(request.messages)} messages, thread: {thread_id}")
            response = await self.agent.invoke(request, thread_id=thread_id)
            logger.info(f"Response generated successfully for thread: {thread_id}")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate response. Please try again."
            )

    async def generate_with_system(
        self,
        system_message: str,
        user_message: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        thread_id: str = "default",
    ) -> ChatResponse:
        """Generate a response with a system message."""
        try:
            # Validate inputs
            if not system_message.strip():
                raise HTTPException(status_code=400, detail="System message cannot be empty")
            if not user_message.strip():
                raise HTTPException(status_code=400, detail="User message cannot be empty")
            if len(system_message) > 5000:
                raise HTTPException(status_code=400, detail="System message too long")
            if len(user_message) > 10000:
                raise HTTPException(status_code=400, detail="User message too long")
            
            messages = [
                Message(role="system", content=system_message.strip()),
                Message(role="user", content=user_message.strip()),
            ]

            request = ChatRequest(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return await self.agent.invoke(request, thread_id=thread_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in generate_with_system: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to generate response with system message"
            )

    async def stream(self, request: ChatRequest) -> StreamingResponse:
        """Stream a response from the LLM service."""
        try:
            # Validate input (similar to generate method)
            if not request.messages:
                raise HTTPException(status_code=400, detail="Messages cannot be empty")

            async def event_generator():
                try:
                    # Send initial role message
                    yield (
                        "data: "
                        + json.dumps({"choices": [{"delta": {"role": "assistant"}}]})
                        + "\n\n"
                    )
                    
                    # Stream response chunks
                    async for chunk in self.service.stream_response(request):
                        if chunk:  # Only yield non-empty chunks
                            data = json.dumps({"choices": [{"delta": {"content": chunk}}]})
                            yield f"data: {data}\n\n"
                    
                    # Send completion signal
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in stream generator: {str(e)}", exc_info=True)
                    error_data = json.dumps({
                        "error": {"message": "Stream interrupted", "type": "server_error"}
                    })
                    yield f"data: {error_data}\n\n"

            return StreamingResponse(
                event_generator(), 
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting up stream: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to setup response stream"
            )


controller = ChatController()


@router.post("/chat", response_model=ChatResponse, summary="Generate a chat response")
async def chat(request: ChatRequest, req: Request = None):
    """
    Generate a response from the LLM based on the provided messages.

    - **messages**: List of messages in the conversation (max 50 messages)
    - **model**: (Optional) The model to use for the response
    - **temperature**: (Optional) The temperature to use for the response (0.0-2.0)
    - **max_tokens**: (Optional) The maximum number of tokens to generate
    - **stream**: (Optional) Whether to stream the response
    
    Headers:
    - **X-Thread-ID**: (Optional) Unique thread ID for conversation memory
    """
    # Apply rate limiting
    if req:
        rate_limit_check(req)
    
    # Extract thread_id from headers or use client IP as default
    thread_id = "default"
    if req:
        # Try to get from header first
        thread_id = req.headers.get("X-Thread-ID", None)
        if not thread_id:
            # Use client IP as fallback for thread identification
            thread_id = f"client_{req.client.host}" if req.client else "default"
    
    return await controller.generate(request, thread_id=thread_id)


@router.post(
    "/chat/system",
    response_model=ChatResponse,
    summary="Generate a response with a system message",
)
async def chat_with_system(
    system_message: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    req: Request = None,
):
    """
    Generate a response with a system message prepended to the conversation.

    - **system_message**: The system message to prepend (max 5000 characters)
    - **user_message**: The user message (max 10000 characters)
    - **model**: (Optional) The model to use for the response
    - **temperature**: (Optional) The temperature to use for the response (0.0-2.0)
    - **max_tokens**: (Optional) The maximum number of tokens to generate
    """
    # Apply rate limiting
    if req:
        rate_limit_check(req)
    
    # Validate temperature range
    if not 0.0 <= temperature <= 2.0:
        raise HTTPException(status_code=400, detail="Temperature must be between 0.0 and 2.0")
    
    return await controller.generate_with_system(
        system_message,
        user_message,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


@router.post("/chat/stream", summary="Stream a chat response")
async def chat_stream(request: ChatRequest, req: Request = None):
    """
    Stream tokens from the LLM using OpenAI-compatible Server-Sent Events.
    
    - **messages**: List of messages in the conversation (max 50 messages)
    - **model**: (Optional) The model to use for the response
    - **temperature**: (Optional) The temperature to use for the response (0.0-2.0)
    - **max_tokens**: (Optional) The maximum number of tokens to generate
    """
    # Apply rate limiting
    if req:
        rate_limit_check(req)
    
    return await controller.stream(request)
