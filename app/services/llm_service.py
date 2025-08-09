import asyncio
import logging
import openai
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, List, Optional
import aiohttp
from contextlib import asynccontextmanager

from app.core.config import settings
from app.schemas.chat import Message, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

@dataclass
class LLMService:
    """Service for interacting with various LLM APIs with a unified interface."""

    provider: str = field(default_factory=lambda: settings.LLM_PROVIDER.lower())
    model: str = field(default_factory=lambda: settings.LLM_MODEL)
    timeout: int = field(default_factory=lambda: settings.API_REQUEST_TIMEOUT)

    def __post_init__(self) -> None:
        """Initialize the LLM client based on the configured provider."""
        try:
            if self.provider == "openai":
                self.client = openai.AsyncOpenAI(
                    api_key=settings.LLM_API_KEY,
                    base_url=settings.LLM_API_ENDPOINT,
                    timeout=self.timeout,
                )
            elif self.provider == "anthropic":
                try:
                    import anthropic
                except ImportError as e:
                    raise ImportError("anthropic package is required for Anthropic provider") from e

                self.client = anthropic.AsyncAnthropic(
                    api_key=settings.LLM_API_KEY,
                    timeout=self.timeout
                )
            elif self.provider == "gemini":
                try:
                    import google.generativeai as genai
                except ImportError as e:
                    raise ImportError("google-generativeai package is required for Gemini provider") from e

                genai.configure(api_key=settings.LLM_API_KEY)
                self.client = genai.GenerativeModel(self.model)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
                
            logger.info(f"Initialized LLM service with provider: {self.provider}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {str(e)}")
            raise
    
    def format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for the API."""
        formatted = []
        for msg in messages:
            if msg.role not in ["user", "assistant", "system"]:
                logger.warning(f"Unknown message role: {msg.role}, defaulting to 'user'")
                role = "user"
            else:
                role = msg.role
            
            formatted.append({"role": role, "content": msg.content})
        
        return formatted
    
    async def _handle_openai_response(self, request: ChatRequest) -> ChatResponse:
        """Handle OpenAI API response."""
        try:
            model = request.model or self.model
            formatted_messages = self.format_messages(request.messages)

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
            
            assistant_message = Message(role="assistant", content=content)
            return ChatResponse(message=assistant_message, model=model, usage=usage)
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            raise Exception("Rate limit exceeded. Please try again later.")
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise Exception("Authentication failed. Please check your API key.")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {str(e)}")
            raise

    async def _handle_anthropic_response(self, request: ChatRequest) -> ChatResponse:
        """Handle Anthropic API response."""
        try:
            import anthropic
            
            model = request.model or self.model
            formatted_messages = self.format_messages(request.messages)

            response = await self.client.messages.create(
                model=model,
                messages=formatted_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 1024,
                stream=request.stream,
            )
            
            content = "".join(
                block.text for block in getattr(response, "content", [])
                if hasattr(block, "text")
            )
            
            assistant_message = Message(role="assistant", content=content)
            return ChatResponse(message=assistant_message, model=model, usage={})
            
        except anthropic.RateLimitError as e:
            logger.error(f"Anthropic rate limit exceeded: {str(e)}")
            raise Exception("Rate limit exceeded. Please try again later.")
        except anthropic.AuthenticationError as e:
            logger.error(f"Anthropic authentication error: {str(e)}")
            raise Exception("Authentication failed. Please check your API key.")
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Anthropic error: {str(e)}")
            raise

    async def _handle_gemini_response(self, request: ChatRequest) -> ChatResponse:
        """Handle Gemini API response."""
        try:
            model = request.model or self.model
            conversation = "\n".join(f"{m.role}: {m.content}" for m in request.messages)
            
            if hasattr(self.client, "generate_content_async"):
                result = await self.client.generate_content_async(
                    conversation,
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    },
                    stream=request.stream,
                )
            else:
                result = await asyncio.to_thread(
                    self.client.generate_content,
                    conversation,
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    },
                    stream=request.stream,
                )
            
            content = getattr(result, "text", str(result))
            assistant_message = Message(role="assistant", content=content)
            return ChatResponse(message=assistant_message, model=model, usage={})
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate a response from the LLM with proper error handling."""
        try:
            logger.info(f"Generating response using {self.provider} provider")
            
            if self.provider == "openai":
                return await self._handle_openai_response(request)
            elif self.provider == "anthropic":
                return await self._handle_anthropic_response(request)
            elif self.provider == "gemini":
                return await self._handle_gemini_response(request)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    async def stream_response(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM as it is generated."""
        try:
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
                import anthropic
                response = await self.client.messages.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens or 1024,
                    stream=True,
                )
                async for block in response:
                    if hasattr(block, "text") and block.text:
                        yield block.text
                        
            else:  # gemini
                conversation = "\n".join(f"{m.role}: {m.content}" for m in request.messages)
                if hasattr(self.client, "generate_content_async"):
                    result = await self.client.generate_content_async(
                        conversation,
                        generation_config={
                            "temperature": request.temperature,
                            "max_output_tokens": request.max_tokens,
                        },
                        stream=True,
                    )
                    async for chunk in result:
                        text = getattr(chunk, "text", None)
                        if text:
                            yield text
                else:
                    # Fallback for non-async Gemini
                    result = await asyncio.to_thread(
                        self.client.generate_content,
                        conversation,
                        generation_config={
                            "temperature": request.temperature,
                            "max_output_tokens": request.max_tokens,
                        },
                        stream=True,
                    )
                    for chunk in getattr(result, "iter", lambda: [])():
                        text = getattr(chunk, "text", None)
                        if text:
                            yield text
                            
        except Exception as e:
            logger.error(f"Error in stream_response: {str(e)}")
            yield f"Error: {str(e)}"


# Create a global instance of the LLM service
llm_service = LLMService() 
