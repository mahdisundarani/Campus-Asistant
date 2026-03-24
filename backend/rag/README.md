# RAG Pipeline — Campus Assistant

**Location**: `backend/rag/`

Modular RAG (Retrieval-Augmented Generation) package responsible for ingesting campus documents into a FAISS vector store and retrieving relevant chunks at query time.

---

## Files

| File | Role |
|---|---|
| `__init__.py` | Exports `ingest_documents`, `load_index`, `search_documents` |
| `pipeline.py` | Orchestrates ingest (build) and search (retrieve) flows |
| `parser.py` | Extracts text from PDF files page-by-page via `pdfplumber`; DOCX via `python-docx` |
| `chunker.py` | Splits extracted text into overlapping chunks (~600 chars, ~100 overlap) preserving metadata |
| `embeddings.py` | Converts text to vectors via HuggingFace Inference API (`all-MiniLM-L6-v2`) |
| `vectorstore.py` | Manages the FAISS index: create, save to disk, load from disk, similarity search |

---

## Ingestion Flow

Run once after uploading new documents, or via the Admin → Rebuild Engine button:

```bash
cd backend && python ingest.py
```

```
data/docs/ (PDFs, DOCX)
    │
    ▼ parser.py       → Extract text per page
    ▼ chunker.py      → Split into overlapping chunks
    ▼ embeddings.py   → Embed chunks (HuggingFace API)
    ▼ vectorstore.py  → Save FAISS index to backend/vectorstore/
```

---

## Retrieval Flow

Called by the RAG Agent via `mcp_client.search_docs()`:

```
User query
    ▼ embeddings.py   → Embed query
    ▼ vectorstore.py  → Top-5 similarity search
    ▼                 → Return chunks with source + page metadata
```

---

## Usage

```python
from rag import ingest_documents, load_index, search_documents

# Build index (run once)
ingest_documents("../data/docs")

# Load on server start
load_index()

# Search per request
results = search_documents("What is the attendance policy?")
for doc in results:
    print(f"[{doc.metadata['source']}, p.{doc.metadata['page']}]")
    print(doc.page_content)
```

---

## Chunk Metadata

Each stored chunk carries:
- `source` — original filename (e.g., `Academic_Policy_Handbook.pdf`)
- `page` — page number within the document
- `department`, `year`, `course` — admin-supplied tags at upload time

Tags enable filtered retrieval: e.g., return only chunks tagged `CS` + `Year 2`.
