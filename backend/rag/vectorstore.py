"""
vectorstore.py — FAISS vector store management.

Handles creating, saving, loading, and searching the FAISS index.
"""

import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from flashrank import Ranker, RerankRequest


# Use /tmp on Render, otherwise local vectorstore directory
IF_RENDER = os.getenv("RENDER") is not None
if IF_RENDER:
    VECTORSTORE_DIR = "/tmp/vectorstore"
else:
    VECTORSTORE_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore")

CHUNKS_PATH = os.path.join(VECTORSTORE_DIR, "chunks.pkl")



def create_index(chunks: list[Document], embeddings) -> FAISS:
    """
    Create a FAISS index from document chunks.

    Args:
        chunks: List of LangChain Documents with page_content and metadata.
        embeddings: Embedding model instance.

    Returns:
        FAISS vector store instance.
    """
    index = FAISS.from_documents(chunks, embeddings)
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
    # Save raw chunks for BM25 (needed since BM25 isn't naturally persistent like FAISS)
    if hasattr(index, 'docstore'):
        # LangChain FAISS stores docs in docstore._dict
        chunks = list(index.docstore._dict.values())
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(chunks, f)


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
    return index


def get_bm25_retriever(path: str = VECTORSTORE_DIR) -> BM25Retriever:
    """Load saved chunks and initialize a BM25 retriever."""
    if not os.path.exists(CHUNKS_PATH):
        print(f"[RAG Core] WARNING: BM25 chunks not found at {CHUNKS_PATH}")
        return None
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)
    print(f"[RAG Core] BM25 indexing {len(chunks)} chunks...")
    return BM25Retriever.from_documents(chunks)


def rerank_results(query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
    """Use FlashRank to rerank the retrieved documents."""
    if not docs:
        return []
        
    ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir=os.path.join(VECTORSTORE_DIR, "flashrank_cache"))
    
    passages = []
    for i, doc in enumerate(docs):
        passages.append({
            "id": i,
            "text": doc.page_content,
            "meta": doc.metadata
        })
        
    rerank_request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(rerank_request)
    
    # Take top_k from reranked results
    final_docs = []
    for res in results[:top_k]:
        # results entries are dicts with {id, text, meta, score}
        final_docs.append(Document(
            page_content=res["text"],
            metadata=res["meta"]
        ))
    return final_docs


def search(index: FAISS, query: str, top_k: int = 5, filter: dict = None, use_hybrid: bool = True, bm25_retriever: BM25Retriever = None) -> list[Document]:
    """
    Search with optional Hybrid (BM25 + FAISS) and Reranking logic.
    """
    # 1. Dense Search (FAISS)
    dense_results = index.similarity_search(query, k=15, filter=filter)
    
    if not use_hybrid:
        return dense_results[:top_k]
        
    # 2. Sparse Search (BM25)
    # Use provided retriever or lazy-load
    bm25 = bm25_retriever if bm25_retriever else get_bm25_retriever()
    sparse_results = []
    if bm25:
        sparse_results = bm25.invoke(query)[:15]
        
    # 3. Merge (Simple deduplication by content hash)
    seen_content = set()
    combined = []
    for doc in dense_results + sparse_results:
        # Basic dedup
        content_hash = hash(doc.page_content)
        if content_hash not in seen_content:
            combined.append(doc)
            seen_content.add(content_hash)
            
    # 4. Rerank
    print(f"[RAG Core] Reranking {len(combined)} hybrid candidates for query...")
    final_results = rerank_results(query, combined, top_k=top_k)
    return final_results
