"""
notices_agent.py — Notices Agent for fetching campus announcements.

This agent calls the Notices MCP server to get the latest news 
and announcements relevant to the user's query.
"""

import json
from agents.state import GraphState
from mcp_client import get_latest_notices


async def notices_node(state: GraphState) -> dict:
    """
    Fetch campus notices via the Notices MCP Server.

    Returns:
        Updated state with 'context' and 'sources' populated from notices.
    """
    query = state["query"]
    context = list(state.get("context", []))
    sources = list(state.get("sources", []))

    # Basic department extraction (simplified for demo)
    dept_filter = None
    query_lower = query.lower()
    if "cs" in query_lower:
        dept_filter = "CS"
    elif "it" in query_lower:
        dept_filter = "IT"

    print(f"[Notices Agent] Fetching latest notices (Filter: {dept_filter}) for: '{query[:60]}...'")

    try:
        # Call the MCP server tool
        notices_json = await get_latest_notices(department=dept_filter, limit=3)
        notices = json.loads(notices_json)

        if not notices:
            print("[Notices Agent] No relevant notices found.")
            context.append({
                "tool": "get_latest_notices",
                "content": "No recent campus announcements found for this category.",
            })
        else:
            for n in notices:
                content = f"Title: {n.get('title')}\nDate: {n.get('date')}\nContent: {n.get('content')}"
                context.append({
                    "tool": "get_latest_notices",
                    "source": "Campus Notices Board",
                    "content": content,
                })
                sources.append({"doc": "Campus Notices", "page": n.get("date")})

            print(f"[Notices Agent] Found {len(notices)} notices.")

    except Exception as e:
        print(f"[Notices Agent] Error calling MCP: {e}")
        context.append({
            "tool": "get_latest_notices",
            "content": f"Failed to fetch campus announcements: {str(e)}",
        })

    return {"context": context, "sources": sources}
