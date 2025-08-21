import asyncio
import logging
import openai
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, List, Optional
import aiohttp
from contextlib import asynccontextmanager

from app.core.config import settings
from app.schemas.chat import Message, ChatRequest, ChatResponse
from app.utils.client_manager import client_manager

logger = logging.getLogger(__name__)

@dataclass
class LLMService:
    """Service for interacting with various LLM APIs with a unified interface."""

    provider: str = field(default_factory=lambda: settings.LLM_PROVIDER.lower())
    model: str = field(default_factory=lambda: settings.LLM_MODEL)
    timeout: int = field(default_factory=lambda: settings.API_REQUEST_TIMEOUT)

    def __post_init__(self) -> None:
        """Initialize the LLM service with optimized client management."""
        # For Ollama compatibility, store the base URL
        if self.provider == "ollama":
            self.ollama_base_url = settings.OLLAMA_BASE_URL
        logger.info(f"Initialized LLM service with provider: {self.provider} (using connection pooling)")
    
    def get_client(self, provider: str = None):
        """Get the appropriate client for the given provider using connection pooling."""
        provider = provider or self.provider
        
        if provider == "openai":
            return client_manager.get_openai_client()
        elif provider == "anthropic":
            return client_manager.get_anthropic_client()
        elif provider == "gemini":
            return client_manager.get_gemini_client()
        elif provider == "ollama":
            return client_manager.get_ollama_client()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
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
            client = self.get_client("openai")

            response = await client.chat.completions.create(
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
            client = self.get_client("anthropic")

            response = await client.messages.create(
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
        """Handle Ollama API response with optional web search support."""
        try:
            import ollama
            import json
            from app.services.search_service import search_service, get_search_tool_definition
            
            model = request.model or self.model
            formatted_messages = self.format_messages(request.messages)
            # Use persistent Ollama client from client manager
            ollama_client = self.get_client("ollama")
            
            # Check if web search is enabled and model supports tools
            tools = []
            if request.enable_search and settings.EXA_SEARCH_ENABLED and search_service.enabled:
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
                
                # Check if the model wants to use tools
                if response.get('message', {}).get('tool_calls'):
                    tool_results = []
                    for tool_call in response['message']['tool_calls']:
                        if tool_call.get('function', {}).get('name') == "web_search":
                            # Execute web search
                            args = tool_call['function'].get('arguments', {})
                            if isinstance(args, str):
                                args = json.loads(args)
                            
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
                            "content": response['message'].get('content', '')
                        })
                        formatted_messages.append({
                            "role": "user",
                            "content": "Search Results:\n" + "\n".join(tool_results)
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
                # Standard call without tools
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
            content = response.get('message', {}).get('content', '')
            
            # Create usage info if available
            usage = {}
            if 'eval_count' in response:
                usage['completion_tokens'] = response['eval_count']
            if 'prompt_eval_count' in response:
                usage['prompt_tokens'] = response['prompt_eval_count']
            if usage:
                usage['total_tokens'] = usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0)
            
            assistant_message = Message(role="assistant", content=content)
            return ChatResponse(message=assistant_message, model=model, usage=usage)
            
        except ImportError as e:
            if "search_service" in str(e):
                logger.warning("Search service not available, falling back to standard response")
                # Fall back to standard Ollama response without search
                return await self._handle_ollama_response_without_search(request)
            raise
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def _handle_ollama_response_without_search(self, request: ChatRequest) -> ChatResponse:
        """Fallback Ollama handler without search capabilities."""
        try:
            import ollama
            
            model = request.model or self.model
            formatted_messages = self.format_messages(request.messages)
            ollama_client = self.get_client("ollama")
            
            response = await ollama_client.chat(
                model=model,
                messages=formatted_messages,
                options={
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens or -1,
                },
                stream=False
            )
            
            content = response.get('message', {}).get('content', '')
            usage = {}
            if 'eval_count' in response:
                usage['completion_tokens'] = response['eval_count']
            if 'prompt_eval_count' in response:
                usage['prompt_tokens'] = response['prompt_eval_count']
            if usage:
                usage['total_tokens'] = usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0)
            
            assistant_message = Message(role="assistant", content=content)
            return ChatResponse(message=assistant_message, model=model, usage=usage)
            
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Ollama API error: {str(e)}")

    async def _handle_gemini_response(self, request: ChatRequest) -> ChatResponse:
        """Handle Gemini API response."""
        try:
            model = request.model or self.model
            conversation = "\n".join(f"{m.role}: {m.content}" for m in request.messages)
            client = self.get_client("gemini")
            
            if hasattr(client, "generate_content_async"):
                result = await client.generate_content_async(
                    conversation,
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    },
                    stream=request.stream,
                )
            else:
                result = await asyncio.to_thread(
                    client.generate_content,
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
            # Use provider from request if specified, otherwise use default
            provider = request.provider or self.provider
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
            # Use provider from request if specified, otherwise use default
            provider = request.provider or self.provider
            model = request.model or self.model
            formatted_messages = self.format_messages(request.messages)

            if provider == "openai":
                client = self.get_client("openai")
                stream = await client.chat.completions.create(
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
                        
            elif provider == "anthropic":
                import anthropic
                client = self.get_client("anthropic")
                response = await client.messages.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens or 1024,
                    stream=True,
                )
                async for block in response:
                    if hasattr(block, "text") and block.text:
                        yield block.text
                        
            elif provider == "ollama":
                import ollama
                
                model = request.model or self.model
                formatted_messages = self.format_messages(request.messages)
                
                # Set the host if different from default
                if self.ollama_base_url != "http://localhost:11434":
                    ollama_client = ollama.AsyncClient(host=self.ollama_base_url)
                else:
                    ollama_client = ollama.AsyncClient()
                
                # Stream from Ollama
                stream = await ollama_client.chat(
                    model=model,
                    messages=formatted_messages,
                    options={
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens or -1,
                    },
                    stream=True
                )
                
                async for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']
                        
            else:  # gemini
                conversation = "\n".join(f"{m.role}: {m.content}" for m in request.messages)
                client = self.get_client("gemini")
                if hasattr(client, "generate_content_async"):
                    result = await client.generate_content_async(
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
                        client.generate_content,
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
