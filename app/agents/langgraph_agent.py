from __future__ import annotations

from langgraph.graph import StateGraph
from langgraph.pregel import Node
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service

class LangGraphAgent:
    """LangGraph powered agent wrapping the existing LLMService."""

    def __init__(self) -> None:
        self._graph = StateGraph()
        self._graph.add_node("llm_call", Node(self._llm_node))
        self._graph.set_entry_point("llm_call")
        self._compiled = self._graph.compile()

    async def _llm_node(self, state: dict) -> dict:
        request: ChatRequest = state["request"]
        response = await llm_service.generate_response(request)
        return {"response": response}

    async def invoke(self, request: ChatRequest) -> ChatResponse:
        result = await self._compiled.invoke({"request": request})
        return result["response"]

# Global instance for easy reuse
langgraph_agent = LangGraphAgent()
