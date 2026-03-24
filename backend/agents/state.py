"""
state.py — Shared state definition for the LangGraph multi-agent system.

GraphState is a TypedDict passed between all nodes in the graph.
Each node reads from and writes to this shared state.
"""

from typing import TypedDict, Literal, Optional


class GraphState(TypedDict):
    """Shared state for the Campus Assistant LangGraph pipeline."""

    # Input
    query: str                          # Original user question
    history: list[dict]                 # Chat history from the frontend

    # Routing
    intent: str                         # Classified intent: "rag", "timetable", "deadline", "planner", "notices", "general"

    # Data (populated by specialist agents)
    context: list[dict]                 # Retrieved chunks / MCP tool results
    sources: list[dict]                 # Citation sources for the frontend

    # Output
    response: str                       # Final LLM-generated answer
