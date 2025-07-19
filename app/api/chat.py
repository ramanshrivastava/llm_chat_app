from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.agents.langgraph_agent import langgraph_agent
from app.services.llm_service import llm_service
import logging

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
        response = await langgraph_agent.invoke(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.post(
    "/chat/system",
    response_model=ChatResponse,
    summary="Generate a response with a system message",
)
async def chat_with_system(
    system_message: str,
    user_message: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
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
            Message(role="user", content=user_message),
        ]

        request = ChatRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = await langgraph_agent.invoke(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat_with_system endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.post("/chat/stream", summary="Stream a chat response")
async def chat_stream(request: ChatRequest):
    """Stream tokens from the LLM using OpenAI-compatible SSE."""

    async def event_generator():
        # send initial role event as OpenAI does
        yield (
            "data: "
            + json.dumps({"choices": [{"delta": {"role": "assistant"}}]})
            + "\n\n"
        )
        async for chunk in llm_service.stream_response(request):
            data = json.dumps({"choices": [{"delta": {"content": chunk}}]})
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
