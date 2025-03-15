import openai
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.chat import Message, ChatRequest, ChatResponse
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.client = openai.OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_ENDPOINT
        )
        self.model = settings.LLM_MODEL
    
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
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=request.stream
            )
            
            # Extract the response message
            assistant_message = Message(
                role="assistant",
                content=response.choices[0].message.content
            )
            
            # Create the response object
            return ChatResponse(
                message=assistant_message,
                model=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

# Create a global instance of the LLM service
llm_service = LLMService() 