# Campus Assistant — Technical Plan

> Full implementation plan covering RAG, MCP, LangGraph, Backend, Frontend, and Evaluation.

---

## 1. Project Goal

Build a campus assistant web app that can:
- Answer student questions with **citations** (policy, attendance, exams, hostel)
- Check **timetables and deadlines** using tools
- Generate **study plans**
- Use **MCP** as the connector layer for tools and data sources
- Use **LangGraph** for multi-agent orchestration

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Frontend                      │
│            Next.js + Tailwind CSS               │
│   Chat UI (streaming) │ Admin Dashboard         │
└──────────────────┬──────────────────────────────┘
                   │ HTTP (REST)
┌──────────────────▼──────────────────────────────┐
│                Backend (FastAPI)                 │
│  Auth (JWT)  │  /chat  │  /upload  │  /admin    │
│              │         │           │            │
│         LangGraph Orchestration Engine          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │Super │ │Retri │ │Timet │ │Plann │ │Respo │ │
│  │visor │ │ever  │ │able  │ │er    │ │Writer│ │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──────┘ └──────┘ │
│     │  MCP Client  │        │                   │
└─────┼──────────────┼────────┼───────────────────┘
      │              │        │
┌─────▼──┐    ┌──────▼──┐  ┌──▼────────┐
│Docs MCP│    │Timetable│  │Notices MCP│
│Server  │    │MCP Srvr │  │(optional) │
└────┬───┘    └────┬────┘  └───────────┘
     │             │
┌────▼─────────────▼──────────────────────────────┐
│              Local Data Layer                    │
│  ./data/docs  │  ./data/timetable  │  FAISS     │
│  ./data/index │  SQLite (logs)     │  Vectors   │
└─────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js + Tailwind CSS |
| Backend | FastAPI (Python) |
| Auth | Supabase Auth (JWT) |
| Orchestration | LangGraph (LangChain) |
| LLM | OpenAI GPT-4 / GPT-3.5 (or Gemini) |
| Embeddings | OpenAI `text-embedding-ada-002` or HuggingFace `all-MiniLM-L6-v2` |
| Vector Store | FAISS (local file) or Qdrant (local Docker) |
| MCP | Local MCP servers (Python, `mcp` SDK) |
| Storage | Local folders: `./data/docs`, `./data/timetable`, `./data/index` |
| Metadata/Logs | SQLite (optional) or in-memory |

---

## 4. RAG Pipeline

### 4.1 Ingestion (runs on upload / rebuild)

```
PDF/DOCX → Parse per-page text → Chunk (400-800 tokens, 80-120 overlap) → Embed → Store in FAISS
```

| Step | Details | Library |
|---|---|---|
| Parse | Extract text per page from PDF/DOCX | `pdfplumber`, `python-docx` |
| Metadata | Store: `doc_id`, `title`, `tags`, `page_number` | Python dict / SQLite |
| Chunk | 400–800 tokens, 80–120 overlap, preserve headings | `langchain.text_splitter.RecursiveCharacterTextSplitter` |
| Embed | Generate vector for each chunk | OpenAI or `sentence-transformers` |
| Index | Store vectors + metadata in FAISS | `faiss-cpu` |

### 4.2 Retrieval (runs per query)

```
User query → Embed → FAISS similarity search (top-k) → Return chunks + citations
```

| Step | Details |
|---|---|
| Embed query | Same model used for ingestion |
| Search | FAISS cosine similarity, top-k = 5 |
| Return | Chunk text + `doc_title` + `page` + `section` |
| Empty result | If top-k is empty → response must state "data not found in uploaded documents" |

---

## 5. MCP Servers

### 5.1 Docs MCP Server (`mcp-servers/docs/`)

| Item | Details |
|---|---|
| **Tools** | `docs.search(query, filters)` — semantic search over FAISS |
| | `docs.get_chunk(doc_id, chunk_id)` — fetch specific chunk |
| **Resources** | List of available docs, metadata, tags |
| **Implementation** | Python, uses `mcp` SDK, reads from FAISS index |

### 5.2 Timetable MCP Server (`mcp-servers/timetable/`)

| Item | Details |
|---|---|
| **Tools** | `timetable.get(day, student_group)` — schedule for a day |
| | `deadlines.get(course_id)` — upcoming deadlines |
| **Resources** | Timetable CSV versions, last updated timestamp |
| **Implementation** | Python, reads from `./data/timetable/*.csv` |

### 5.3 Notices MCP Server (`mcp-servers/notices/`) *(optional)*

| Item | Details |
|---|---|
| **Tools** | `notices.latest(department, limit)` |
| **Resources** | Notice feed items |

---

## 6. Backend Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Health check |
| `GET` | `/me` | JWT | Current user info |
| `POST` | `/chat` | JWT | Main chat — runs LangGraph pipeline |
| `POST` | `/upload` | JWT (admin) | Upload PDF/DOCX to `./data/docs` |
| `POST` | `/upload-timetable` | JWT (admin) | Upload timetable CSV to `./data/timetable` |
| `POST` | `/rebuild-index` | JWT (admin) | Re-chunk, re-embed, update FAISS index |
| `GET` | `/admin/logs` | JWT (admin) | View query logs (latency, tools, sources) |

### `/chat` Endpoint Flow (detailed)

```python
@app.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    # 1. Build initial state
    state = {
        "messages": request.history + [{"role": "user", "content": request.message}],
        "user_profile": get_user_profile(user),
        "intent": "",
        "retrieved_chunks": [],
        "tool_results": [],
        "final_answer": ""
    }
    
    # 2. Run LangGraph
    result = await graph.ainvoke(state)
    
    # 3. Return response
    return {
        "response": result["final_answer"],
        "sources": [
            {"doc": c["doc_title"], "page": c["page"], "section": c["section"]}
            for c in result["retrieved_chunks"]
        ]
    }
```

---

## 7. Frontend Pages

| Page | Path | Description |
|---|---|---|
| Login | `/login` | Email/password auth via Supabase |
| Signup | `/signup` | New user registration |
| Chat | `/` | Main chat interface with streaming responses |
| Admin | `/admin` | Upload docs, upload timetable CSV, rebuild index, view logs |

### Chat UI Features
- Streaming responses (SSE or chunked transfer)
- Citations displayed below answers (doc name, page, section)
- Conversation history maintained client-side
- "Thinking..." indicator during processing

---

## 8. Evaluation & Observability

### Offline Evaluation
- Create **50–80 campus questions** with expected answer + expected source doc
- Metrics:
  - Correctness (manual 1–5 scale)
  - Citation accuracy (correct doc + page)
  - Latency (ms)
  - Tool call success rate

### Runtime Logging (per query)
- Total latency
- Token usage
- MCP server tools called
- Documents cited
- Store in SQLite or JSON logs

---

## 9. File Structure (Target)

```
Campus-Assistant/
├── frontend/                    # Next.js app
│   ├── app/
│   │   ├── page.tsx             # Main chat page
│   │   ├── login/page.tsx       # Login
│   │   ├── signup/page.tsx      # Signup
│   │   ├── admin/page.tsx       # Admin dashboard
│   │   └── components/
│   │       └── ChatInterface.tsx
│   └── ...
├── backend/
│   ├── main.py                  # FastAPI app, endpoints
│   ├── rag.py                   # RAG pipeline: ingest, search, embed
│   ├── graph.py                 # LangGraph definition (agents + edges)
│   ├── agents/
│   │   ├── supervisor.py        # Supervisor agent
│   │   ├── retriever.py         # RAG retriever agent
│   │   ├── timetable.py         # Timetable agent
│   │   ├── planner.py           # Study planner agent
│   │   ├── writer.py            # Response writer agent
│   │   └── safety.py            # Safety/scope agent (optional)
│   ├── mcp_client.py            # MCP client wrapper functions
│   ├── ingest.py                # CLI: parse → chunk → embed → save FAISS
│   ├── vectorstore/             # FAISS index files (generated)
│   ├── requirements.txt
│   └── .env
├── mcp-servers/
│   ├── docs/
│   │   └── server.py            # Docs MCP server
│   ├── timetable/
│   │   └── server.py            # Timetable MCP server
│   └── notices/                 # (optional)
│       └── server.py
├── data/
│   ├── docs/                    # Uploaded PDFs/DOCX
│   ├── timetable/               # Uploaded CSV files
│   └── index/                   # FAISS index files
├── eval/
│   ├── questions.json           # 50-80 test questions
│   └── runner.py                # Evaluation script
├── agent.md
├── technical-plan.md
├── progress.md
└── Project.pdf
```

---

## 10. Implementation Schedule (6 Weeks)

| Week | Focus | Deliverables |
|---|---|---|
| **Week 1** | UI + Auth + Backend shell | ✅ Chat UI, Login/Signup, Logout, `/chat` stub, `/upload`, Admin page |
| **Week 2** | RAG Pipeline | Ingestion, chunking, embeddings, FAISS index, basic RAG answers with citations |
| **Week 3** | MCP Servers | Docs MCP server, Timetable MCP server, backend MCP client wrappers |
| **Week 4** | LangGraph Agents | Supervisor + 3 specialist agents, tool calling integrated into graph, `/chat` fully wired |
| **Week 5** | Admin + Evaluation | Doc tagging, timetable CSV upload, rebuild index, logs view, eval dataset + runner |
| **Week 6** | Polish + Deliverables | Streaming responses, Notices MCP (optional), architecture diagram, project report, demo video (5-8 min) |

---

## 11. Key Dependencies (to install)

```txt
# Backend
fastapi
uvicorn
python-multipart
python-dotenv
langchain
langgraph
langchain-openai          # or langchain-google-genai
faiss-cpu
pdfplumber
python-docx
sentence-transformers     # if using HuggingFace embeddings
openai                    # if using OpenAI
mcp                       # MCP SDK
```

---

## 12. Environment Variables Needed

```env
# Existing
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...

# New (add to backend/.env)
OPENAI_API_KEY=...          # or GEMINI_API_KEY
EMBEDDING_MODEL=text-embedding-ada-002   # or all-MiniLM-L6-v2
LLM_MODEL=gpt-4o-mini
```
