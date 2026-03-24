"""
timetable_agent.py — Timetable Agent for schedule and deadline questions.

Uses Gemini to extract parameters (day, group, course_id) from natural language,
then calls the Timetable MCP Server via mcp_client.
"""

import os
import json
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from agents.state import GraphState
import mcp_client


llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    temperature=0.0,
    max_retries=3,    # Auto-retry transient OpenRouter/Gemini 500s
)

# ==================== TIMETABLE PARAMETER EXTRACTION ====================

TIMETABLE_EXTRACT_PROMPT = """Extract the following from the user's question about a class timetable.
Respond with ONLY a JSON object, no other text.

{
  "day": "<day of week or null>",
  "student_group": "<CS-A or CS-B or null>"
}

Rules:
- day must be one of: Monday, Tuesday, Wednesday, Thursday, Friday, or null if not specified.
- student_group must be CS-A or CS-B, or null if not specified.
- If the user says "today", resolve it to the actual day based on the conversation or leave null.
- IMPORTANT: If the user's message or ANY previous message in the conversation history mentions CS-A, cs-a, CSA, CS-B, cs-b, CSB, group A, group B, Section A, or Section B, you MUST extract that as the student_group. Never return null for student_group if it appears ANYWHERE in the history.
- If the user's message is a short follow-up like just "cs-a" or "monday" with no other context, use the conversation history to fill in the other missing field.
- If the user asks a follow up question like "What about Tuesday?", and previously asked about "CS-A", then return {"day": "Tuesday", "student_group": "CS-A"}.

Examples:
- "What classes does CS-A have on Monday?" → {"day": "Monday", "student_group": "CS-A"}
- "What is my timetable for Wednesday?" → {"day": "Wednesday", "student_group": null}
- "Show me the Friday schedule" → {"day": "Friday", "student_group": null}
- "What classes do I have?" → {"day": null, "student_group": null}
- "cs-a" (with prior history asking about Monday) → {"day": "Monday", "student_group": "CS-A"}
"""

# ==================== DEADLINE PARAMETER EXTRACTION ====================

DEADLINE_EXTRACT_PROMPT = """Extract the course ID from the user's question about deadlines.
Respond with ONLY a JSON object, no other text.

{
  "course_id": "<course code like CS401 or null>"
}

Rules:
- course_id should be in format like CS401, CS402, CS403, CS404, CS405 etc.
- If the user mentions a course name, map it to the ID:
  - Machine Learning / ML → CS401
  - Computer Networks → CS402
  - Database Systems / DBMS → CS403
  - Software Engineering / SE → CS404
  - Operating Systems / OS → CS405
- If no specific course is mentioned, use null (returns all deadlines).

Examples:
- "When is the CS401 assignment due?" → {"course_id": "CS401"}
- "What are the ML deadlines?" → {"course_id": "CS401"}
- "Show me all upcoming deadlines" → {"course_id": null}
- "When is the Database Systems exam?" → {"course_id": "CS403"}
"""


async def _extract_timetable_params(query: str, history: list[dict] = None) -> dict:
    """Use Gemini to extract day and student_group from query."""
    messages = [
        SystemMessage(content=TIMETABLE_EXTRACT_PROMPT),
    ]
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
                
    messages.append(HumanMessage(content=query))
    response = await llm.ainvoke(messages)
    try:
        text = response.content.strip()
        # Find the first { and last } to extract JSON
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        return {"day": None, "student_group": None}
    except (json.JSONDecodeError, IndexError):
        print(f"[Timetable Agent] Failed to parse params: {response.content}")
        return {"day": None, "student_group": None}


async def _extract_deadline_params(query: str, history: list[dict] = None) -> dict:
    """Use Gemini to extract course_id from query."""
    messages = [
        SystemMessage(content=DEADLINE_EXTRACT_PROMPT),
    ]
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
                
    messages.append(HumanMessage(content=query))
    response = await llm.ainvoke(messages)
    try:
        text = response.content.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        return {"course_id": None}
    except (json.JSONDecodeError, IndexError):
        print(f"[Timetable Agent] Failed to parse deadline params: {response.content}")
        return {"course_id": None}


async def timetable_node(state: GraphState) -> dict:
    """
    Handle timetable and deadline queries via Timetable MCP Server.

    For intent "timetable": extracts day + group → calls get_timetable()
    For intent "deadline": extracts course_id → calls get_deadlines()

    If student_group is unknown, sets a clarification context block
    so the response writer asks the user to specify their group.

    Returns:
        Updated state with 'context' and 'sources' populated.
    """
    query = state["query"]
    intent = state["intent"]
    context = list(state.get("context", []))
    sources = list(state.get("sources", []))

    try:
        if intent == "deadline":
            # ===== DEADLINE PATH =====
            params = await _extract_deadline_params(query, state.get("history", []))
            course_id = params.get("course_id")

            print(f"[Timetable Agent] Getting deadlines (course_id={course_id})")

            result_str = await mcp_client.get_deadlines(course_id)
            context.append({
                "tool": "get_deadlines",
                "course_id": course_id,
                "content": result_str,
            })
            sources.append({"doc": "Timetable API (Deadlines)", "page": "Live Data"})

        else:
            # ===== TIMETABLE PATH =====
            params = await _extract_timetable_params(query, state.get("history", []))
            day = params.get("day")       # May be None → will ask clarification
            group = params.get("student_group")  # May be None → MUST ask clarification

            print(f"[Timetable Agent] Extracted params: day={day}, group={group}")

            # --- CLARIFICATION GATE ---
            # If group is missing we CANNOT look up the schedule — ask the user.
            if not group:
                clarification_day = f" on {day}" if day else ""
                context.append({
                    "tool": "clarification_needed",
                    "content": (
                        f"The user asked about their lectures{clarification_day} but did not specify which class section they are in. "
                        "Ask the user: 'Which section are you in — CS-A or CS-B?' "
                        "Do NOT attempt to answer the timetable question until the section is confirmed."
                    ),
                })
                return {"context": context, "sources": sources}

            # If day is still missing, default to a reasonable fallback
            if not day:
                day = "Monday"
                print("[Timetable Agent] Day not specified, defaulting to Monday.")

            print(f"[Timetable Agent] Getting timetable (day={day}, group={group})")

            result_str = await mcp_client.get_timetable(day, group)
            context.append({
                "tool": "get_timetable",
                "day": day,
                "student_group": group,
                "content": result_str,
            })
            sources.append({"doc": f"Timetable API ({day})", "page": "Live Data"})

    except Exception as e:
        print(f"[Timetable Agent] Error: {e}")
        context.append({
            "tool": "timetable_error",
            "content": f"Failed to fetch timetable data: {str(e)}",
        })

    return {"context": context, "sources": sources}
