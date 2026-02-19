"""
ingest.py — CLI script to run the RAG ingestion pipeline.

Parses all PDFs in ../data/docs, chunks them, generates embeddings,
and saves the FAISS index to ./vectorstore/

Usage:
    cd backend
    python ingest.py
"""

from dotenv import load_dotenv
load_dotenv()

from rag import ingest_documents

if __name__ == "__main__":
    ingest_documents("../data/docs")
