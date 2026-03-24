"""
supervisor.py — Supervisor Agent for intent classification.

Uses Gemini to classify the user's query into one of:
  - "rag"       → document/policy questions (search FAISS index)
  - "timetable" → class schedule questions
  - "deadline"  → assignment/exam deadline questions
  - "planner"   → study plan / schedule planning requests
  - "general"   → greetings, off-topic, or general conversation
"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from agents.state import GraphState


# Use the same Gemini model as the rest of the app
llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    temperature=0.0,  # Deterministic classification
    max_retries=3,    # Auto-retry transient OpenRouter/Gemini 500s
)

CLASSIFIER_PROMPT = """You are an intent classifier for a university campus assistant chatbot.

Given a student's question AND the conversation history, classify it into EXACTLY ONE of these categories:

- "rag" — Questions about university policies, rules, regulations, handbooks, hostel rules, academic policies, campus facilities, department info, academic calendar, and holidays. Anything that would be found in official university PDF documents.
- "timetable" — Questions about class schedules, lecture timings, rooms, faculty, what classes are on a specific day. Anything about the weekly timetable.
- "deadline" — Questions about assignment due dates, exam dates, project submissions, upcoming deadlines.
- "planner" — Requests to create a study plan, organize a week, plan exam preparation, or combine schedule + academic info into a plan.
- "notices" — Questions about campus news, announcements, latest notifications, university events, hackathons, maintenance work, or recent updates from the management.
- "general" — Greetings (hi, hello), thanks, off-topic questions, or anything that doesn't fit the above categories.

IMPORTANT RULES:
1. Respond with ONLY the category label (one word), nothing else.
2. If a query mentions both schedule AND deadlines, classify as "planner".
3. If a query asks about a course's content/syllabus, classify as "rag" (it's in the handbook).
4. If a query asks about a course's timing/room, classify as "timetable".
5. "When is X due?" or "What are the deadlines?" → "deadline"
6. "What classes do I have on Monday?" → "timetable"
7. "What is the attendance policy?" → "rag"
8. "What dates are in the academic calendar?" or "When are the holidays?" → "rag"
9. CRITICAL: If the previous assistant message asked "Which section are you in — CS-A or CS-B?", then the user's reply (even if it's just "cs-a", "CS-B", "cs b", "section a", "A") is ALWAYS "timetable".
10. CRITICAL: Short follow-up messages like "cs-a", "monday", "tuesday" should inherit the intent from the conversation history, not be classified as "general".

Examples:
- "What is the attendance policy?" → rag
- "Tell me about hostel rules" → rag
- "What classes does CS-A have on Monday?" → timetable
- "Who teaches Machine Learning?" → timetable
- "When is the CS401 assignment due?" → deadline
- "What are the upcoming deadlines?" → deadline
- "Help me plan my study week" → planner
- "How should I prepare for mid-semester exams?" → planner
- "What are the latest announcements?" → notices
- "Are there any hackathons coming up?" → notices
- "Hello!" → general
- "Thanks for the help" → general
- "cs-a" (after the bot asked which section) → timetable
- "CS-B" (after the bot asked which section) → timetable
"""


# Keywords that signal the assistant just asked which section the student is in
_SECTION_CLARIFICATION_PHRASES = [
    "which section are you in",
    "cs-a or cs-b",
    "cs-a or cs-b?",
    "section are you in",
]

# Short tokens that a user sends as a section reply
_SECTION_TOKENS = {"cs-a", "cs-b", "csa", "csb", "section a", "section b", "group a", "group b", "a", "b"}


def _last_assistant_asked_for_section(history: list[dict]) -> bool:
    """Return True if the most recent assistant message asked for CS-A or CS-B."""
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            content = msg.get("content", "").lower()
            return any(phrase in content for phrase in _SECTION_CLARIFICATION_PHRASES)
    return False


async def supervisor_node(state: GraphState) -> dict:
    """
    Classify the user's intent using Gemini.

    Includes a deterministic pre-check: if the assistant's last message asked
    for the student's section and the current message is a section reply,
    always route to 'timetable' without an LLM call.

    Returns:
        Updated state with 'intent' field set.
    """
    query = state["query"]
    history = state.get("history", [])

    # ── DETERMINISTIC PRE-CHECK ──────────────────────────────────────────────
    # If the bot just asked "CS-A or CS-B?" and the reply looks like a section
    # answer, skip the LLM completely.
    query_lower = query.strip().lower()
    if _last_assistant_asked_for_section(history) and query_lower in _SECTION_TOKENS:
        print(f"[Supervisor] Section follow-up detected ('{query}') -> Intent: timetable")
        return {"intent": "timetable"}

    # ── LLM CLASSIFICATION ───────────────────────────────────────────────────
    messages = [
        SystemMessage(content=CLASSIFIER_PROMPT),
    ]

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=f"Classify this query: \"{query}\""))

    response = await llm.ainvoke(messages)
    intent = response.content.strip().lower().strip('"').strip("'")

    # Validate — fall back to "general" if Gemini returns something unexpected
    valid_intents = {"rag", "timetable", "deadline", "planner", "notices", "general"}
    if intent not in valid_intents:
        print(f"[Supervisor] Unexpected intent '{intent}', defaulting to 'general'")
        intent = "general"

    print(f"[Supervisor] Query: '{query[:60]}...' -> Intent: {intent}")

    return {"intent": intent}
