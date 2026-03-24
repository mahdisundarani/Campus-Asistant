"""
graph.py — LangGraph StateGraph definition for the Campus Assistant.

Defines the multi-agent pipeline:
  Supervisor → (RAG | Timetable | Planner | General) → Response Writer → END

The compiled graph is exported as `campus_graph` for use by main.py.
"""

from langgraph.graph import StateGraph, END
from agents.state import GraphState
from agents.supervisor import supervisor_node
from agents.rag_agent import rag_node
from agents.timetable_agent import timetable_node
from agents.planner_agent import planner_node
from agents.notices_agent import notices_node
from agents.response_writer import response_writer_node


def route_by_intent(state: GraphState) -> str:
    """
    Conditional edge function: routes to the correct agent based on intent.

    Returns the name of the next node to execute.
    """
    intent = state.get("intent", "general")

    if intent == "rag":
        return "rag_agent"
    elif intent in ("timetable", "deadline"):
        return "timetable_agent"
    elif intent == "planner":
        return "planner_agent"
    elif intent == "notices":
        return "notices_agent"
    else:
        # "general" or unknown — skip straight to response writer
        return "response_writer"


def build_graph() -> StateGraph:
    """Build and compile the Campus Assistant LangGraph."""

    graph = StateGraph(GraphState)

    # ==================== ADD NODES ====================
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag_agent", rag_node)
    graph.add_node("timetable_agent", timetable_node)
    graph.add_node("planner_agent", planner_node)
    graph.add_node("notices_agent", notices_node)
    graph.add_node("response_writer", response_writer_node)

    # ==================== ENTRY POINT ====================
    graph.set_entry_point("supervisor")

    # ==================== CONDITIONAL ROUTING ====================
    # Supervisor classifies intent → routes to the right specialist
    graph.add_conditional_edges(
        "supervisor",
        route_by_intent,
        {
            "rag_agent": "rag_agent",
            "timetable_agent": "timetable_agent",
            "planner_agent": "planner_agent",
            "notices_agent": "notices_agent",
            "response_writer": "response_writer",
        },
    )

    # ==================== SPECIALIST → RESPONSE WRITER ====================
    graph.add_edge("rag_agent", "response_writer")
    graph.add_edge("timetable_agent", "response_writer")
    graph.add_edge("planner_agent", "response_writer")
    graph.add_edge("notices_agent", "response_writer")

    # ==================== RESPONSE WRITER → END ====================
    graph.add_edge("response_writer", END)

    return graph.compile()


# Export the compiled graph
campus_graph = build_graph()
