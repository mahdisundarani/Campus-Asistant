"""
planner_agent.py — Planner Agent for study plan generation.

Fetches both timetable data AND document context via MCP,
then uses Gemini to produce a structured study plan.
"""

import json
from agents.state import GraphState
import mcp_client


async def planner_node(state: GraphState) -> dict:
    """
    Generate a study plan by fetching data from both MCP servers.

    1. Gets the full week's timetable from Timetable MCP
    2. Gets all upcoming deadlines from Timetable MCP
    3. Stores both in context for the Response Writer to use

    Returns:
        Updated state with 'context' and 'sources' populated.
    """
    query = state["query"]
    context = list(state.get("context", []))
    sources = list(state.get("sources", []))

    print(f"[Planner Agent] Building study plan for: '{query[:60]}...'")

    try:
        # Fetch timetable for all weekdays
        all_days_data = []
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            try:
                result = await mcp_client.get_timetable(day)
                all_days_data.append(f"--- {day} ---\n{result}")
            except Exception as e:
                all_days_data.append(f"--- {day} ---\nError: {e}")

        timetable_context = "\n\n".join(all_days_data)
        context.append({
            "tool": "get_timetable (all days)",
            "content": timetable_context,
        })
        sources.append({"doc": "Timetable API (Full Week)", "page": "Live Data"})

        # Fetch all deadlines
        try:
            deadlines_result = await mcp_client.get_deadlines()
            context.append({
                "tool": "get_deadlines (all)",
                "content": deadlines_result,
            })
            sources.append({"doc": "Timetable API (All Deadlines)", "page": "Live Data"})
        except Exception as e:
            print(f"[Planner Agent] Error fetching deadlines: {e}")
            context.append({
                "tool": "get_deadlines",
                "content": f"Error fetching deadlines: {e}",
            })

        # Optionally search for relevant academic docs
        try:
            docs_result = await mcp_client.search_docs(query, top_k=3)
            if docs_result:
                context.append({
                    "tool": "search_docs (planner context)",
                    "content": docs_result,
                })
                sources.append({"doc": "Campus Documents", "page": "Various"})
        except Exception as e:
            print(f"[Planner Agent] Docs search failed (non-critical): {e}")

        print(f"[Planner Agent] Assembled context from {len(context)} sources")

    except Exception as e:
        print(f"[Planner Agent] Error: {e}")
        context.append({
            "tool": "planner_error",
            "content": f"Failed to build study plan context: {str(e)}",
        })

    return {"context": context, "sources": sources}
