"""
pipeline.py — RAG pipeline orchestrator.

Ties together parsing, chunking, embedding, and vector store
into two main operations: ingest and search.
"""

from langchain_core.documents import Document
from . import parser, chunker, embeddings, vectorstore


# Module-level index cache (loaded once, reused for all searches)
_index = None
_bm25 = None


def ingest_documents(docs_dir: str, tags_map: dict = None) -> None:
    """
    Full ingestion pipeline: parse all PDFs -> chunk -> embed -> upload to Qdrant.

    Args:
        docs_dir: Path to directory containing PDF files.
        tags_map: Optional dict mapping filenames to tag dicts {department, year, course}.
    """
    print("=" * 50)
    print("Starting document ingestion...")
    print("=" * 50)

    # Step 1: Parse
    print("\n[1/3] Parsing PDFs...")
    pages = parser.parse_all_pdfs(docs_dir)
    if not pages:
        print("No pages found. Make sure PDFs exist in:", docs_dir)
        return

    # Step 2: Chunk (with optional tag injection)
    print("\n[2/3] Chunking text...")
    chunks = chunker.chunk_documents(pages, tags_map=tags_map)

    # Step 3: Embed + upload to Qdrant (create_index handles saving BM25 chunks too)
    print("\n[3/3] Embedding and uploading to Qdrant...")
    embedding_model = embeddings.get_embeddings()
    vectorstore.create_index(chunks, embedding_model)

    print("\n" + "=" * 50)
    print(f"Ingestion complete! {len(pages)} pages -> {len(chunks)} chunks uploaded to Qdrant.")
    print("=" * 50)


def load_index() -> None:
    """
    Connect to Qdrant collection and load BM25 chunks into memory.
    Call this once on server startup.
    """
    global _index, _bm25
    embedding_model = embeddings.get_embeddings()
    _index = vectorstore.load_index(embedding_model)
    _bm25 = vectorstore.get_bm25_retriever()


def search_documents(query: str, top_k: int = 5, filter: dict = None) -> list[Document]:
    """
    Search the loaded indices for relevant chunks with optional filtering.
    """
    global _index, _bm25
    if _index is None:
        raise RuntimeError("Index not loaded. Call load_index() first.")

    return vectorstore.search(_index, query, top_k, filter=filter, bm25_retriever=_bm25)
