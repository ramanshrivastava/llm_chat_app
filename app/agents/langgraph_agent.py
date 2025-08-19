from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, TypedDict, List, Optional, Annotated
from operator import add
import logging
from datetime import datetime

from app.schemas.chat import ChatRequest, ChatResponse, Message

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """Enhanced state for the LangGraph agent with proper tracking."""
    # Core request/response
    request: ChatRequest
    response: Optional[ChatResponse]
    
    # Conversation history with automatic merging
    messages: Annotated[List[Message], add]
    
    # Metadata for tracking
    timestamp: str
    model_used: Optional[str]
    total_tokens: int
    error: Optional[str]
    
    # Processing flags
    is_streaming: bool
    processing_complete: bool

class LangGraphAgent:
    """LangGraph powered agent with enhanced state management and memory."""

    def __init__(self, use_memory: bool = True) -> None:
        """
        Initialize the LangGraph agent with proper graph setup.
        
        Args:
            use_memory: Enable conversation memory and checkpointing
        """
        try:
            # Initialize memory for conversation persistence
            self.memory = MemorySaver() if use_memory else None
            
            # Build the state graph
            self._graph = StateGraph(AgentState)
            
            # Add processing nodes
            self._graph.add_node("initialize", self._initialize_state)
            self._graph.add_node("llm_call", self._llm_node)
            self._graph.add_node("finalize", self._finalize_response)
            
            # Define the flow
            self._graph.set_entry_point("initialize")
            self._graph.add_edge("initialize", "llm_call")
            self._graph.add_edge("llm_call", "finalize")
            self._graph.add_edge("finalize", END)
            
            # Compile with optional memory
            if self.memory:
                self._compiled = self._graph.compile(checkpointer=self.memory)
                logger.info("LangGraph agent initialized with memory support")
            else:
                self._compiled = self._graph.compile()
                logger.info("LangGraph agent initialized without memory")
                
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph agent: {str(e)}")
            raise

    async def _initialize_state(self, state: AgentState) -> Dict[str, Any]:
        """Initialize and validate the state before processing."""
        try:
            request = state.get("request")
            if not request:
                raise ValueError("Request is required in state")
            
            # Initialize state with defaults
            updates = {
                "timestamp": datetime.now().isoformat(),
                "messages": request.messages,  # Will be merged with existing
                "is_streaming": request.stream,
                "processing_complete": False,
                "total_tokens": state.get("total_tokens", 0),
                "error": None,
            }
            
            logger.debug(f"State initialized at {updates['timestamp']}")
            return updates
            
        except Exception as e:
            logger.error(f"Error initializing state: {str(e)}")
            return {"error": str(e), "processing_complete": True}

    async def _llm_node(self, state: AgentState) -> Dict[str, Any]:
        """Process LLM request through the service layer with error handling."""
        try:
            # Skip if there was an initialization error
            if state.get("error"):
                return {"processing_complete": True}
                
            from app.services.llm_service import llm_service
            request = state["request"]
            
            # Generate response
            response = await llm_service.generate_response(request)
            
            # Extract token usage if available
            tokens_used = 0
            if response.usage:
                tokens_used = response.usage.get("total_tokens", 0)
            
            # Update state with response
            updates = {
                "response": response,
                "model_used": response.model or request.model,
                "total_tokens": state.get("total_tokens", 0) + tokens_used,
            }
            
            logger.info(f"LLM response generated using {updates['model_used']}")
            return updates
            
        except Exception as e:
            logger.error(f"Error in LLM node: {str(e)}")
            return {
                "error": str(e),
                "processing_complete": True,
            }
    
    async def _finalize_response(self, state: AgentState) -> Dict[str, Any]:
        """Finalize the response and update state."""
        try:
            # Validate response exists
            if not state.get("response") and not state.get("error"):
                logger.warning("No response generated and no error captured")
                return {
                    "error": "No response generated",
                    "processing_complete": True,
                }
            
            # Check for sensitive patterns (basic filtering)
            if state.get("response"):
                response = state["response"]
                content = response.message.content if response.message else ""
                
                # Basic sensitive pattern detection
                sensitive_patterns = [
                    "sk-",  # OpenAI API keys
                    "api_key",
                    "password",
                    "secret",
                ]
                
                for pattern in sensitive_patterns:
                    if pattern.lower() in content.lower():
                        logger.warning(f"Potentially sensitive content detected: {pattern}")
                        # You could filter or mask here if needed
                        break
                
                # Calculate processing time
                start_time = datetime.fromisoformat(state["timestamp"])
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Response processed in {processing_time:.2f} seconds")
            
            return {"processing_complete": True}
            
        except Exception as e:
            logger.error(f"Error finalizing response: {str(e)}")
            return {
                "error": str(e),
                "processing_complete": True,
            }

    async def invoke(self, request: ChatRequest, thread_id: str = "default") -> ChatResponse:
        """
        Invoke the agent with a chat request.
        
        Args:
            request: The chat request to process
            thread_id: Unique identifier for conversation thread (for memory)
            
        Returns:
            ChatResponse with the generated response
            
        Raises:
            Exception: If there's an error during processing
        """
        try:
            logger.debug(f"Invoking agent with {len(request.messages)} messages, thread: {thread_id}")
            
            # Prepare initial state
            initial_state = {
                "request": request,
                "messages": [],  # Will be populated/merged by the graph
                "total_tokens": 0,
                "is_streaming": request.stream,
                "processing_complete": False,
            }
            
            # Configure with thread_id if memory is enabled
            config = None
            if self.memory:
                config = {"configurable": {"thread_id": thread_id}}
            
            # Invoke the graph
            result = await self._compiled.ainvoke(initial_state, config)
            
            # Check for errors
            if result.get("error"):
                raise Exception(f"Processing error: {result['error']}")
            
            # Ensure we have a response
            if not result.get("response"):
                raise Exception("No response generated")
            
            logger.info(f"Successfully processed request for thread {thread_id}, "
                       f"tokens used: {result.get('total_tokens', 0)}")
            
            return result["response"]
            
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise

# Global instance for easy reuse
langgraph_agent = LangGraphAgent()
