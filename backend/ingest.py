"""
ingest.py — CLI script to run the RAG ingestion pipeline.

Parses all PDFs in ../data/docs, chunks them, generates embeddings,
and saves the FAISS index to ./vectorstore/

Usage:
    cd backend
    python ingest.py
"""

import os
import json
from dotenv import load_dotenv
load_dotenv()

from rag import ingest_documents

if __name__ == "__main__":
    # Load tags from doc_tags.json if it exists
    tags_map = {}
    if os.path.exists("doc_tags.json"):
        try:
            with open("doc_tags.json", "r") as f:
                tags_map = json.load(f)
            print(f"Loaded tags for {len(tags_map)} documents.")
        except Exception as e:
            print(f"Warning: Could not load doc_tags.json: {e}")

    ingest_documents("../data/docs", tags_map=tags_map)
