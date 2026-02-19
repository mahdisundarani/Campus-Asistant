"""
embeddings.py — HuggingFace Inference API embeddings.

Uses the HuggingFace API (no local model download) to generate
text embeddings for documents and queries.
"""

import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings


def get_embeddings() -> HuggingFaceEndpointEmbeddings:
    """
    Create and return a HuggingFace Inference API embedding model.

    Uses the HUGGINGFACE_API_KEY from environment variables.
    Model: sentence-transformers/all-MiniLM-L6-v2

    Returns:
        HuggingFaceEndpointEmbeddings instance.
    """
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY not set in .env")

    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=api_key,
    )
