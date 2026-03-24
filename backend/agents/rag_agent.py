"""
rag_agent.py — RAG Agent for document-based questions.

Calls the Docs MCP Server via mcp_client to search the FAISS index
for relevant document chunks, then stores them in the shared state.
"""

import json
from agents.state import GraphState
import asyncio
from agents.state import GraphState
from rag import embeddings, vectorstore


async def rag_node(state: GraphState) -> dict:
    """
    Search campus documents via the Docs MCP Server.

    Returns:
        Updated state with 'context' and 'sources' populated from FAISS results.
    """
    query = state["query"]
    context = list(state.get("context", []))
    sources = list(state.get("sources", []))

    # Basic metadata filter extraction (Proper AI Engineer touch)
    # In a real app, this would come from the User Profile or a dedicated extraction agent.
    search_filter = {}
    query_lower = query.lower()
    
    if "cs" in query_lower:
        search_filter["department"] = "CS"
    if "year 1" in query_lower or "1st year" in query_lower:
        search_filter["year"] = "1"
    elif "year 2" in query_lower or "2nd year" in query_lower:
        search_filter["year"] = "2"

    print(f"[RAG Agent] Searching docs (Filter: {search_filter}) for: '{query[:60]}...'")

    try:
        # Load the index
        emb_model = embeddings.get_embeddings()
        index = vectorstore.load_index(emb_model)
        
        # Search the index with the generated metadata filter
        docs = vectorstore.search(index, query, top_k=5, filter=search_filter if search_filter else None)

        for doc in docs:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            content = doc.page_content

            # Build enriched context entry with any available tags
            context_entry = {
                "tool": "search_docs (direct)",
                "source": source,
                "page": page,
                "content": content,
            }
            if doc.metadata.get("department"):
                context_entry["department"] = doc.metadata["department"]
            if doc.metadata.get("year"):
                context_entry["year"] = doc.metadata["year"]
            if doc.metadata.get("course"):
                context_entry["course"] = doc.metadata["course"]

            context.append(context_entry)
            sources.append({"doc": source, "page": page})

        print(f"[RAG Agent] Found {len(docs)} chunks using tags filter: {search_filter}")

    except Exception as e:
        print(f"[RAG Agent] Error: {e}")
        context.append({
            "tool": "search_docs",
            "content": f"Failed to search documents: {str(e)}",
        })

    return {"context": context, "sources": sources}
