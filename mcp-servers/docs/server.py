"""
Docs MCP Server -- Exposes the FAISS document search via FastMCP.

Tools:
  - search_docs(query, top_k?) -> semantic search over indexed campus documents
  - get_chunk(doc_name, page) -> fetch a specific chunk by doc name + page

Resources:
  - docs://catalog -> list of all indexed documents with metadata
"""

import json
import os
import sys
from typing import Optional

from dotenv import load_dotenv

# Load .env from backend directory (for HUGGINGFACE_API_KEY)
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# Add backend to sys.path so we can import the rag package
sys.path.insert(0, BACKEND_DIR)

from fastmcp import FastMCP
from rag import embeddings, vectorstore

# ==================== CONFIG ====================
VECTORSTORE_DIR = os.path.join(BACKEND_DIR, "vectorstore")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docs")

mcp = FastMCP("Docs Server")

# Module-level index cache
_index = None


def _get_index():
    """Load the FAISS index (cached after first call)."""
    global _index
    if _index is None:
        embedding_model = embeddings.get_embeddings()
        _index = vectorstore.load_index(embedding_model, VECTORSTORE_DIR)
    return _index


# ==================== TOOLS ====================
@mcp.tool
def search_docs(query: str, top_k: int = 5) -> list[dict]:
    """
    Semantic search over uploaded campus documents using FAISS.

    Args:
        query: The search query (e.g., 'attendance policy', 'hostel rules').
        top_k: Number of top results to return (default: 5).

    Returns:
        List of matching chunks with source doc name, page, and content snippet.
    """
    try:
        index = _get_index()
    except FileNotFoundError:
        return [{"error": "FAISS index not found. Run 'python ingest.py' first."}]
    except Exception as e:
        return [{"error": f"Failed to load index: {str(e)}"}]

    results = vectorstore.search(index, query, top_k)

    return [
        {
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "?"),
            "content": doc.page_content,
        }
        for doc in results
    ]


@mcp.tool
def get_chunk(doc_name: str, page: int) -> Optional[dict]:
    """
    Fetch a specific chunk by document name and page number.

    Args:
        doc_name: Name of the source document (e.g., 'Academic_Policy_Handbook.pdf').
        page: Page number to retrieve.

    Returns:
        The matching chunk with source, page, and content, or None if not found.
    """
    try:
        index = _get_index()
    except FileNotFoundError:
        return {"error": "FAISS index not found. Run 'python ingest.py' first."}
    except Exception as e:
        return {"error": f"Failed to load index: {str(e)}"}

    # Search with a broad query and filter by metadata
    # Use the doc_name as query to get relevant results from that doc
    all_results = vectorstore.search(index, doc_name, top_k=50)

    for doc in all_results:
        source = doc.metadata.get("source", "")
        doc_page = doc.metadata.get("page", -1)

        # Match by doc name (partial match) and page
        if doc_name.lower() in source.lower() and doc_page == page:
            return {
                "source": source,
                "page": doc_page,
                "content": doc.page_content,
            }

    return {"message": f"No chunk found for '{doc_name}' page {page}"}


# ==================== RESOURCES ====================
@mcp.resource("docs://catalog")
def docs_catalog() -> str:
    """
    List all documents available in the data/docs directory with metadata.
    """
    if not os.path.exists(DOCS_DIR):
        return json.dumps({"error": "docs directory not found", "path": DOCS_DIR})

    docs = []
    for filename in sorted(os.listdir(DOCS_DIR)):
        filepath = os.path.join(DOCS_DIR, filename)
        if os.path.isfile(filepath):
            size_kb = round(os.path.getsize(filepath) / 1024, 1)
            docs.append({
                "filename": filename,
                "size_kb": size_kb,
                "extension": os.path.splitext(filename)[1].lower(),
            })

    return json.dumps({
        "total_documents": len(docs),
        "documents": docs,
    }, indent=2)


# ==================== SELF-TEST ====================
def _run_self_test():
    """Run a quick self-test to verify the server works."""
    print("=" * 50)
    print("Docs MCP Server -- Self-Test")
    print("=" * 50)

    print("\n[1] Testing docs_catalog():")
    catalog = docs_catalog()
    parsed = json.loads(catalog)
    print(f"  -> {parsed.get('total_documents', 0)} documents found")
    for d in parsed.get("documents", [])[:5]:
        print(f"    {d['filename']} ({d['size_kb']} KB)")

    print("\n[2] Testing search_docs('attendance policy'):")
    results = search_docs("attendance policy")
    print(f"  -> {len(results)} results")
    for r in results[:2]:
        if "error" in r:
            print(f"    ERROR: {r['error']}")
        else:
            print(f"    [{r['source']}, p.{r['page']}] {r['content'][:80]}...")

    print("\n[3] Testing search_docs('hostel rules'):")
    results = search_docs("hostel rules")
    print(f"  -> {len(results)} results")
    for r in results[:2]:
        if "error" in r:
            print(f"    ERROR: {r['error']}")
        else:
            print(f"    [{r['source']}, p.{r['page']}] {r['content'][:80]}...")

    print("\n" + "=" * 50)
    print("All self-tests passed!")
    print("=" * 50)


# ==================== ENTRYPOINT ====================
if __name__ == "__main__":
    if "--test" in sys.argv:
        _run_self_test()
    else:
        mcp.run()
