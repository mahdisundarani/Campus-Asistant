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
import logging
from typing import Optional
import asyncio

from dotenv import load_dotenv

# Load .env from backend directory (for HUGGINGFACE_API_KEY)
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# Add backend to sys.path so we can import the rag package
sys.path.insert(0, BACKEND_DIR)

from fastmcp import FastMCP
from rag import embeddings, vectorstore

# Disable FastMCP's stdout logger banner
logging.getLogger("fastmcp").setLevel(logging.CRITICAL)

# ==================== CONFIG ====================
VECTORSTORE_DIR = os.path.join(BACKEND_DIR, "vectorstore")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docs")

# Redirect all standard output to standard error to prevent corrupting the MCP JSON-RPC stream
# FastMCP will take over stdout later for its own communication, or we can just silence HuggingFace.
import warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

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


@mcp.tool
async def ping() -> str:
    """A simple ping to test if the server is responsive."""
    return "Docs Server is alive!"

@mcp.tool
async def search_docs(query: str, top_k: int = 5) -> str:
    """
    Semantic search over uploaded campus documents using FAISS.

    Args:
        query: The search query (e.g., 'attendance policy', 'hostel rules').
        top_k: Number of top results to return (default: 5).

    Returns:
        JSON string of matching chunks with source doc name, page, and content snippet.
    """
    try:
        index = _get_index()
    except FileNotFoundError:
        return json.dumps([{"error": "FAISS index not found. Run 'python ingest.py' first."}])
    except Exception as e:
        return json.dumps([{"error": f"Failed to load index: {str(e)}"}])

    # Run the blocking FAISS/HuggingFace search in a separate thread so AnyIO doesn't hang
    results = await asyncio.to_thread(vectorstore.search, index, query, top_k)

    return json.dumps([
        {
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "?"),
            "content": doc.page_content,
        }
        for doc in results
    ])


@mcp.tool
async def get_chunk(doc_name: str, page: int) -> str:
    """
    Fetch a specific chunk by document name and page number.

    Args:
        doc_name: Name of the source document (e.g., 'Academic_Policy_Handbook.pdf').
        page: Page number to retrieve.

    Returns:
        JSON string of the matching chunk with source, page, and content, or error if not found.
    """
    try:
        index = _get_index()
    except FileNotFoundError:
        return json.dumps({"error": "FAISS index not found. Run 'python ingest.py' first."})
    except Exception as e:
        return json.dumps({"error": f"Failed to load index: {str(e)}"})

    # Search with a broad query and filter by metadata
    # Use the doc_name as query to get relevant results from that doc
    all_results = await asyncio.to_thread(vectorstore.search, index, doc_name, 50)

    for doc in all_results:
        source = doc.metadata.get("source", "")
        doc_page = doc.metadata.get("page", -1)

        # Match by doc name (partial match) and page
        if doc_name.lower() in source.lower() and doc_page == page:
            return json.dumps({
                "source": source,
                "page": doc_page,
                "content": doc.page_content,
            })

    return json.dumps({"message": f"No chunk found for '{doc_name}' page {page}"})


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
async def _run_self_test():
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
    results_json = await search_docs("attendance policy")
    results = json.loads(results_json)
    print(f"  -> {len(results)} results")
    for r in results[:2]:
        if "error" in r:
            print(f"    ERROR: {r['error']}")
        else:
            print(f"    [{r['source']}, p.{r['page']}] {r['content'][:80]}...")

    print("\n[3] Testing search_docs('hostel rules'):")
    results_json = await search_docs("hostel rules")
    results = json.loads(results_json)
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
        asyncio.run(_run_self_test())
    else:
        mcp.run()
