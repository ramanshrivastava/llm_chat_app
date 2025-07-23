import openai
from typing import List, Dict, AsyncGenerator
import logging

from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.chat import Message, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with various LLM APIs with a unified interface."""

    def __init__(self) -> None:
        """Initialize the LLM service based on the configured provider."""
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL

        if self.provider == "openai":
            self.client = openai.AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_ENDPOINT,
            )
        elif self.provider == "anthropic":
            try:
                import anthropic
            except Exception as e:  # pragma: no cover - optional dependency
                raise ImportError(
                    "anthropic package is required for Anthropic provider"
                ) from e

            self.client = anthropic.AsyncAnthropic(api_key=settings.LLM_API_KEY)
        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
            except Exception as e:  # pragma: no cover - optional dependency
                raise ImportError("google-generativeai package is required for Gemini provider") from e

            genai.configure(api_key=settings.LLM_API_KEY)
            self.client = genai.GenerativeModel(self.model)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for the OpenAI API."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate a response from the LLM."""
        try:
            # Use the model from the request if provided, otherwise use the default
            model = request.model or self.model

            # Format the messages for the API
            formatted_messages = self.format_messages(request.messages)

            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=request.stream,
                )
                content = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens or 1024,
                    stream=request.stream,
                )
                content = "".join(
                    block.text for block in getattr(response, "content", [])
                )
                usage = {}
            else:  # gemini
                conversation = "\n".join(m.content for m in request.messages)
                result = await run_in_threadpool(
                    self.client.generate_content,
                    conversation,
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    },
                    stream=request.stream,
                )
                content = getattr(result, "text", str(result))
                usage = {}

            assistant_message = Message(role="assistant", content=content)

            return ChatResponse(message=assistant_message, model=model, usage=usage)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    async def stream_response(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM as it is generated."""
        # Use the model from the request if provided, otherwise use the default
        model = request.model or self.model

        formatted_messages = self.format_messages(request.messages)

        if self.provider == "openai":
            stream = await self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        elif self.provider == "anthropic":
            response = await self.client.messages.create(
                model=model,
                messages=formatted_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 1024,
                stream=True,
            )
            async for block in getattr(response, "content", []):
                if getattr(block, "text", ""):
                    yield block.text
        else:  # gemini
            conversation = "\n".join(m.content for m in request.messages)
            def _stream() -> list[str]:
                result = self.client.generate_content(
                    conversation,
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    },
                    stream=True,
                )
                return [
                    chunk.text
                    for chunk in getattr(result, "iter", lambda: [])()
                    if getattr(chunk, "text", None)
                ]

            for text in await run_in_threadpool(_stream):
                yield text


# Create a global instance of the LLM service
llm_service = LLMService() 
