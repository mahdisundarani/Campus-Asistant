"""
vectorstore.py — FAISS vector store management.

Handles creating, saving, loading, and searching the FAISS index.
"""

import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


VECTORSTORE_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore")


def create_index(chunks: list[Document], embeddings) -> FAISS:
    """
    Create a FAISS index from document chunks.

    Args:
        chunks: List of LangChain Documents with page_content and metadata.
        embeddings: Embedding model instance.

    Returns:
        FAISS vector store instance.
    """
    print(f"  Creating FAISS index from {len(chunks)} chunks...")
    index = FAISS.from_documents(chunks, embeddings)
    print("  → FAISS index created")
    return index


def save_index(index: FAISS, path: str = VECTORSTORE_DIR) -> None:
    """
    Save the FAISS index to disk.

    Args:
        index: FAISS vector store instance.
        path: Directory to save index files.
    """
    os.makedirs(path, exist_ok=True)
    index.save_local(path)
    print(f"  → Index saved to {path}")


def load_index(embeddings, path: str = VECTORSTORE_DIR) -> FAISS:
    """
    Load a FAISS index from disk.

    Args:
        embeddings: Embedding model instance (must match the one used to create the index).
        path: Directory containing index files.

    Returns:
        FAISS vector store instance.

    Raises:
        FileNotFoundError: If index files don't exist.
    """
    if not os.path.exists(os.path.join(path, "index.faiss")):
        raise FileNotFoundError(
            f"No FAISS index found at {path}. Run 'python ingest.py' first."
        )

    index = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    print(f"  → Index loaded from {path}")
    return index


def search(index: FAISS, query: str, top_k: int = 5) -> list[Document]:
    """
    Search the FAISS index for relevant document chunks.

    Args:
        index: FAISS vector store instance.
        query: User's search query.
        top_k: Number of top results to return.

    Returns:
        List of LangChain Documents with page_content and metadata (source, page).
    """
    results = index.similarity_search(query, k=top_k)
    return results
