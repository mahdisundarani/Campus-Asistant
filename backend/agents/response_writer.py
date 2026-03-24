"""
response_writer.py — Response Writer Agent for final answer formatting.

Takes the accumulated context and sources from previous agents,
and uses Gemini to produce a well-formatted markdown answer.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from agents.state import GraphState


llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    temperature=0.3,
    max_retries=3,    # Auto-retry transient OpenRouter/Gemini 500s
)

SYSTEM_PROMPT = """You are a helpful campus assistant for Greenfield University.
Answer student questions based on the context provided below.

**Formatting Rules:**
- Use **Markdown** for all answers.
- Use `## Headers` for sections.
- Use `* bullet points` or `- bullet points` for lists.
- Use `**bold**` for key terms.
- For document-based answers, include citations with the document name and page number.
- For schedule/deadline answers, format the data clearly into tables or lists.
- For study plans, organize by day with clear time blocks and priorities.
- Be concise but thorough.

**Important:**
- If the context indicates this is a general conversation query (e.g., greetings, thanks), respond politely and naturally without mentioning documents.
- If the context contains error messages, acknowledge the issue politely and let the student know you're having trouble fetching that data.
- Use the context to answer the question. If the context contains related or partially relevant information, use it to construct the best possible answer. Combine information from multiple context chunks if needed.
- Only say "I don't have this information in the uploaded documents." if the context is completely unrelated to the question and contains no useful information at all.
- Never make up factual university information that isn't supported by the context.

Context:
{context}
"""


async def response_writer_node(state: GraphState) -> dict:
    """
    Generate the final markdown response using Gemini.

    Reads the 'context' and 'query' from state, calls Gemini,
    and writes the result to 'response'.

    Special case: if any context item has tool='clarification_needed',
    we return the clarification question directly without calling the LLM.

    Returns:
        Updated state with 'response' set to the LLM-generated answer.
    """
    query = state["query"]
    context_items = state.get("context", [])

    # --- CLARIFICATION FAST-PATH ---
    # If the timetable agent set a clarification_needed block, bypass the LLM
    # and return a crisp question immediately. This prevents the LLM from
    # hallucinating "I don't have that information" instead of asking.
    for item in context_items:
        if isinstance(item, dict) and item.get("tool") == "clarification_needed":
            return {"response": "Which section are you in — **CS-A** or **CS-B**? Please let me know and I'll pull up your timetable right away!"}

    # Build context string from all gathered data
    context_parts = []
    for item in context_items:
        if isinstance(item, dict):
            tool = item.get("tool", "unknown")
            content = item.get("content", "")
            source = item.get("source", "")
            page = item.get("page", "")

            if source and page:
                context_parts.append(f"[{tool}: {source}, Page {page}]\n{content}")
            else:
                context_parts.append(f"[{tool}]\n{content}")
        else:
            context_parts.append(str(item))

    # Handle empty context (general queries)
    if not context_parts:
        context_str = "No specific context retrieved. This appears to be a general conversation query."
    else:
        context_str = "\n\n---\n\n".join(context_parts)

    # Build messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context_str)),
    ]

    history = state.get("history", [])
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    print(f"[Response Writer] Generating response ({len(context_parts)} context items)")

    response = await llm.ainvoke(messages)

    print(f"[Response Writer] Response generated ({len(response.content)} chars)")

    return {"response": response.content}
