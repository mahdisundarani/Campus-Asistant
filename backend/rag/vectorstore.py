"""
vectorstore.py — Qdrant vector store management.

Handles creating, connecting to, and searching the Qdrant collection.
Replaces the previous FAISS-based implementation.
"""

import os
import pickle
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from flashrank import Ranker, RerankRequest


VECTORSTORE_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore")
CHUNKS_PATH = os.path.join(VECTORSTORE_DIR, "chunks.pkl")

# Qdrant config — read from environment
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "campus_assistant")

# all-MiniLM-L6-v2 produces 384-dimensional vectors
EMBEDDING_DIM = 384


def _get_client() -> QdrantClient:
    """Create and return a Qdrant client."""
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def create_index(chunks: list[Document], embeddings) -> QdrantVectorStore:
    """
    Upload document chunks to Qdrant and return the vector store.

    This replaces FAISS.from_documents(). Qdrant stores data on its
    server persistently — no separate 'save' step needed.

    Args:
        chunks: List of LangChain Documents with page_content and metadata.
        embeddings: Embedding model instance.

    Returns:
        QdrantVectorStore instance.
    """
    client = _get_client()

    # Recreate the collection fresh on every ingest
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"[Qdrant] Deleting existing collection '{COLLECTION_NAME}'...")
        client.delete_collection(COLLECTION_NAME)

    print(f"[Qdrant] Creating collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM})...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    # Embed + upload all chunks to Qdrant
    store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
    )
    print(f"[Qdrant] Uploaded {len(chunks)} chunks to '{COLLECTION_NAME}'.")

    # Save raw chunks for BM25 (BM25 is still file-based)
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)
    print(f"[Qdrant] BM25 chunks saved to {CHUNKS_PATH}.")

    return store


def load_index(embeddings) -> QdrantVectorStore:
    """
    Connect to the existing Qdrant collection.

    This replaces FAISS.load_local(). With Qdrant, data lives on the
    server permanently — just connect and start querying.

    Args:
        embeddings: Embedding model instance (must match the one used during ingest).

    Returns:
        QdrantVectorStore instance.

    Raises:
        RuntimeError: If the Qdrant collection doesn't exist yet.
    """
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        raise RuntimeError(
            f"Qdrant collection '{COLLECTION_NAME}' not found. "
            "Run 'python ingest.py' first to upload your documents."
        )

    store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    print(f"[Qdrant] Connected to collection '{COLLECTION_NAME}'.")
    return store


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

    ranker = Ranker(
        model_name="ms-marco-MiniLM-L-12-v2",
        cache_dir=os.path.join(VECTORSTORE_DIR, "flashrank_cache")
    )

    passages = [
        {"id": i, "text": doc.page_content, "meta": doc.metadata}
        for i, doc in enumerate(docs)
    ]

    rerank_request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(rerank_request)

    return [
        Document(page_content=res["text"], metadata=res["meta"])
        for res in results[:top_k]
    ]


def search(
    index: QdrantVectorStore,
    query: str,
    top_k: int = 5,
    filter: dict = None,
    use_hybrid: bool = True,
    bm25_retriever: BM25Retriever = None
) -> list[Document]:
    """
    Search with optional Hybrid (BM25 + Qdrant dense) and Reranking logic.

    Args:
        index: QdrantVectorStore instance.
        query: Search query string.
        top_k: Number of final results to return.
        filter: Optional dict like {"department": "CSE"} for metadata filtering.
        use_hybrid: Whether to combine BM25 with dense search.
        bm25_retriever: Pre-loaded BM25 retriever (avoids reloading each call).

    Returns:
        List of top-k Documents after reranking.
    """
    # Build Qdrant metadata filter if provided
    qdrant_filter = None
    if filter:
        conditions = [
            FieldCondition(key=f"metadata.{k}", match=MatchValue(value=v))
            for k, v in filter.items()
        ]
        qdrant_filter = Filter(must=conditions)

    # 1. Dense Search (Qdrant)
    dense_results = index.similarity_search(query, k=15, filter=qdrant_filter)

    if not use_hybrid:
        return dense_results[:top_k]

    # 2. Sparse Search (BM25)
    bm25 = bm25_retriever if bm25_retriever else get_bm25_retriever()
    sparse_results = []
    if bm25:
        sparse_results = bm25.invoke(query)[:15]

    # 3. Merge with deduplication
    seen_content = set()
    combined = []
    for doc in dense_results + sparse_results:
        content_hash = hash(doc.page_content)
        if content_hash not in seen_content:
            combined.append(doc)
            seen_content.add(content_hash)

    # 4. Rerank
    print(f"[RAG Core] Reranking {len(combined)} hybrid candidates for query...")
    return rerank_results(query, combined, top_k=top_k)
