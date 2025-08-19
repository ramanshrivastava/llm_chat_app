import asyncio
import logging
import json
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
            elif self.provider == "ollama":
                # Ollama client is initialized on demand in _handle_ollama_response
                self.ollama_base_url = settings.OLLAMA_BASE_URL
                self.client = None  # Will be created when needed
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

    async def _handle_ollama_response(self, request: ChatRequest) -> ChatResponse:
        """Handle Ollama API response with tool calling support."""
        try:
            import ollama
            from app.services.search_service import search_service, get_search_tool_definition
            
            model = request.model or self.model
            formatted_messages = self.format_messages(request.messages)
            
            # Initialize Ollama client
            if self.ollama_base_url != "http://localhost:11434":
                ollama_client = ollama.AsyncClient(host=self.ollama_base_url)
            else:
                ollama_client = ollama.AsyncClient()
            
            # Check if web search is enabled and model supports tools
            tools = []
            if settings.EXA_SEARCH_ENABLED and search_service.enabled:
                # Only add tools for models that support function calling
                if "gpt-oss" in model.lower() or "llama" in model.lower():
                    tools.append(get_search_tool_definition())
            
            # Make the API call with or without tools
            if tools:
                response = await ollama_client.chat(
                    model=model,
                    messages=formatted_messages,
                    tools=tools,
                    options={
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens or -1,
                    },
                    stream=False
                )
                
                # Handle tool calls if present
                if hasattr(response, 'message') and hasattr(response.message, 'tool_calls'):
                    tool_results = []
                    for tool_call in response.message.tool_calls:
                        if tool_call.function.name == "web_search":
                            # Execute web search
                            args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                            search_results = await search_service.search(
                                query=args.get("query", ""),
                                num_results=args.get("num_results", 5),
                                category=args.get("category"),
                                include_domains=args.get("include_domains"),
                                exclude_domains=args.get("exclude_domains")
                            )
                            
                            # Format results for context
                            search_context = search_service.format_for_llm(search_results)
                            tool_results.append(search_context)
                    
                    # If tools were called, make another request with the results
                    if tool_results:
                        # Add tool results to messages
                        formatted_messages.append({
                            "role": "assistant",
                            "content": response.message.content or ""
                        })
                        formatted_messages.append({
                            "role": "system",
                            "content": "\n\n".join(tool_results)
                        })
                        
                        # Get final response with search context
                        response = await ollama_client.chat(
                            model=model,
                            messages=formatted_messages,
                            options={
                                "temperature": request.temperature,
                                "num_predict": request.max_tokens or -1,
                            },
                            stream=False
                        )
            else:
                response = await ollama_client.chat(
                    model=model,
                    messages=formatted_messages,
                    options={
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens or -1,
                    },
                    stream=False
                )
            
            # Extract content from response
            content = response.message.content if hasattr(response, 'message') else str(response)
            
            # Get token usage if available
            usage = {}
            if hasattr(response, 'eval_count'):
                usage["completion_tokens"] = response.eval_count
            if hasattr(response, 'prompt_eval_count'):
                usage["prompt_tokens"] = response.prompt_eval_count
                usage["total_tokens"] = usage.get("completion_tokens", 0) + usage["prompt_tokens"]
            
            assistant_message = Message(role="assistant", content=content)
            return ChatResponse(message=assistant_message, model=model, usage=usage)
            
        except ImportError as e:
            logger.error(f"Ollama package not installed: {str(e)}")
            raise Exception("Ollama package is required. Run: pip install ollama")
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Ollama API error: {str(e)}")
    
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
            # Check for provider override in request
            provider = request.provider if hasattr(request, 'provider') and request.provider else self.provider
            logger.info(f"Generating response using {provider} provider")
            
            if provider == "openai":
                return await self._handle_openai_response(request)
            elif provider == "anthropic":
                return await self._handle_anthropic_response(request)
            elif provider == "gemini":
                return await self._handle_gemini_response(request)
            elif provider == "ollama":
                return await self._handle_ollama_response(request)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
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
