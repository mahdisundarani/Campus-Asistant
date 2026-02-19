"""
pipeline.py — RAG pipeline orchestrator.

Ties together parsing, chunking, embedding, and vector store
into two main operations: ingest and search.
"""

from langchain_core.documents import Document
from . import parser, chunker, embeddings, vectorstore


# Module-level index cache (loaded once, reused for all searches)
_index = None


def ingest_documents(docs_dir: str) -> None:
    """
    Full ingestion pipeline: parse all PDFs → chunk → embed → save FAISS index.

    Args:
        docs_dir: Path to directory containing PDF files.
    """
    print("=" * 50)
    print("Starting document ingestion...")
    print("=" * 50)

    # Step 1: Parse
    print("\n[1/4] Parsing PDFs...")
    pages = parser.parse_all_pdfs(docs_dir)
    if not pages:
        print("No pages found. Make sure PDFs exist in:", docs_dir)
        return

    # Step 2: Chunk
    print("\n[2/4] Chunking text...")
    chunks = chunker.chunk_documents(pages)

    # Step 3: Embed + create index
    print("\n[3/4] Embedding chunks (via HuggingFace API)...")
    embedding_model = embeddings.get_embeddings()
    index = vectorstore.create_index(chunks, embedding_model)

    # Step 4: Save
    print("\n[4/4] Saving index to disk...")
    vectorstore.save_index(index)

    print("\n" + "=" * 50)
    print(f"Ingestion complete! {len(pages)} pages → {len(chunks)} chunks indexed.")
    print("=" * 50)


def load_index() -> None:
    """
    Load the FAISS index from disk into memory.
    Call this once on server startup.
    """
    global _index
    embedding_model = embeddings.get_embeddings()
    _index = vectorstore.load_index(embedding_model)


def search_documents(query: str, top_k: int = 5) -> list[Document]:
    """
    Search the loaded FAISS index for relevant chunks.

    Args:
        query: User's question.
        top_k: Number of results to return.

    Returns:
        List of LangChain Documents with page_content and metadata.

    Raises:
        RuntimeError: If index hasn't been loaded yet.
    """
    global _index
    if _index is None:
        raise RuntimeError("Index not loaded. Call load_index() first.")

    return vectorstore.search(_index, query, top_k)
