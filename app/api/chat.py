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
