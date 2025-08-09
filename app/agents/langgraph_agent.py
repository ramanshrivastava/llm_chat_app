from __future__ import annotations

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict
import logging

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the LangGraph agent."""
    request: ChatRequest
    response: ChatResponse

class LangGraphAgent:
    """LangGraph powered agent wrapping the existing LLMService."""

    def __init__(self) -> None:
        """Initialize the LangGraph agent with proper graph setup."""
        try:
            self._graph = StateGraph(AgentState)
            self._graph.add_node("llm_call", self._llm_node)
            self._graph.set_entry_point("llm_call")
            self._graph.add_edge("llm_call", END)
            self._compiled = self._graph.compile()
            logger.info("LangGraph agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph agent: {str(e)}")
            raise

    async def _llm_node(self, state: AgentState) -> AgentState:
        """Process LLM request through the service layer."""
        try:
            request = state["request"]
            response = await llm_service.generate_response(request)
            return {"request": request, "response": response}
        except Exception as e:
            logger.error(f"Error in LLM node: {str(e)}")
            raise

    async def invoke(self, request: ChatRequest) -> ChatResponse:
        """Invoke the agent with a chat request."""
        try:
            logger.debug(f"Invoking agent with {len(request.messages)} messages")
            result = await self._compiled.ainvoke({"request": request})
            return result["response"]
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise

# Global instance for easy reuse
langgraph_agent = LangGraphAgent()
