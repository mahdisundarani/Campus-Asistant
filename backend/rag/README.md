# RAG Pipeline — Campus Assistant

This folder (`backend/rag/`) contains the complete Retrieval-Augmented Generation pipeline.

---

## 1. Directory Structure

| File | Purpose |
|---|---|
| **`__init__.py`** | Exposes `rag.ingest_documents`, `rag.load_index`, and `rag.search_documents` for clean imports. |
| **`pipeline.py`** | **Orchestrator**. Contains the main logic for ingestion and search. |
| **`parser.py`** | Extracts text from PDF files using `pdfplumber`. |
| **`chunker.py`** | Splits long text into smaller chunks (600 chars) with overlap. |
| **`embeddings.py`** | Converts text to vectors using HuggingFace `all-MiniLM-L6-v2`. |
| **`vectorstore.py`** | Manages the FAISS index (save/load/search). |

---

## 2. Ingestion Flow (Build)
*Run via `python ingest.py`*

1.  **Parse (`parser.py`)**: Reads all PDFs in `data/docs/` and extracts text page-by-page.
2.  **Chunk (`chunker.py`)**: Breaks pages into overlapping chunks to fit context windows.
    *   *Metadata*: Preserves source filename + page number.
3.  **Embed (`embeddings.py`)**: Sends chunks to HuggingFace Inference API to get vectors.
4.  **Index (`vectorstore.py`)**: Saves vectors into a local FAISS index (`backend/vectorstore/`).

---

## 3. Retrieval Flow (Search)
*Run via `/chat` endpoint*

1.  **User Query**: "Where is the library?"
2.  **Embed Query**: Converts query to vector (same model).
3.  **Search (`vectorstore.py`)**: Finds top-5 most similar chunks by cosine similarity.
4.  **Return**: Returns text chunks + metadata (Source: `Guide.pdf`, Page: 3).

---

## 4. Usage

```python
from rag import ingest_documents, load_index, search_documents

# 1. Build Index (Run once)
ingest_documents("../data/docs")

# 2. Load Index (On server start)
load_index()

# 3. Search (Per request)
results = search_documents("What is the attendance policy?")
for doc in results:
    print(f"File: {doc.metadata['source']}, Page: {doc.metadata['page']}")
    print(doc.page_content)
```
