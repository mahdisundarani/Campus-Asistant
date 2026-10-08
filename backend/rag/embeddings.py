"""
embeddings.py — HuggingFace Inference API embeddings.

Uses the HuggingFace API (no local model download) to generate
text embeddings for documents and queries.
"""

import os
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


def get_embeddings() -> FastEmbedEmbeddings:
    """
    Create and return a local FastEmbed embedding model.

    Runs locally using FastEmbed (no PyTorch, very lightweight, completely free).
    Model: sentence-transformers/all-MiniLM-L6-v2 (default in FastEmbed)

    Returns:
        FastEmbedEmbeddings instance.
    """
    return FastEmbedEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
    )
