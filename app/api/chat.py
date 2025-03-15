from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.services.llm_service import llm_service
import logging
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse, summary="Generate a chat response")
async def chat(request: ChatRequest):
    """
    Generate a response from the LLM based on the provided messages.
    
    - **messages**: List of messages in the conversation
    - **model**: (Optional) The model to use for the response
    - **temperature**: (Optional) The temperature to use for the response
    - **max_tokens**: (Optional) The maximum number of tokens to generate
    - **stream**: (Optional) Whether to stream the response
    """
    try:
        response = await llm_service.generate_response(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.post("/chat/system", response_model=ChatResponse, summary="Generate a response with a system message")
async def chat_with_system(
    system_message: str,
    user_message: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = None
):
    """
    Generate a response with a system message prepended to the conversation.
    
    - **system_message**: The system message to prepend
    - **user_message**: The user message
    - **model**: (Optional) The model to use for the response
    - **temperature**: (Optional) The temperature to use for the response
    - **max_tokens**: (Optional) The maximum number of tokens to generate
    """
    try:
        messages = [
            Message(role="system", content=system_message),
            Message(role="user", content=user_message)
        ]
        
        request = ChatRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response = await llm_service.generate_response(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat_with_system endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}") 