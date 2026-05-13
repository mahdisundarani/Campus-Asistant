"""
rag — Retrieval-Augmented Generation pipeline for Campus Assistant.

Usage:
    from rag import ingest_documents, load_index, search_documents

    # Ingest (run once):
    ingest_documents("data/docs")

    # On server startup:
    load_index()

    # Per query:
    results = search_documents("What is the attendance policy?")
"""

from .pipeline import ingest_documents, load_index, search_documents

__all__ = ["ingest_documents", "load_index", "search_documents"]
