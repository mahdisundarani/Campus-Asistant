# AGENTS.md — AI Agent Instructions for Campus Assistant

> This file provides context, rules, and coding standards for AI agents working on this project.

---

## Project Overview

**Campus Assistant** is a web app that answers campus questions using RAG + LangGraph multi-agent orchestration + MCP tool servers. Students can ask about policies, timetables, deadlines, and get study plans. Admins can upload documents and manage the knowledge base.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router) + Tailwind CSS |
| Backend | FastAPI (Python 3.11+) |
| Auth | Supabase Auth (JWT tokens) |
| Orchestration | LangGraph (LangChain) |
| LLM | Google Gemini 2.5 Flash (via `langchain-google-genai`) |
| Embeddings | OpenAI `text-embedding-ada-002` or HuggingFace `all-MiniLM-L6-v2` |
| Vector Store | FAISS (local) |
| MCP | Local MCP servers (Python `mcp` SDK) |
| Storage | Local filesystem (`./data/`) |

---

## Project Structure

```
Campus-Assistant/
├── frontend/              # Next.js app (App Router)
│   ├── app/
│   │   ├── page.tsx       # Main chat page (auth-guarded)
│   │   ├── login/         # Login page
│   │   ├── signup/        # Signup page
│   │   ├── admin/         # Admin dashboard
│   │   └── components/    # Reusable components
│   └── lib/               # Supabase client, utils
├── backend/               # FastAPI server
│   ├── main.py            # App entry, all endpoints
│   ├── rag/               # RAG pipeline (modular package)
│   │   ├── __init__.py    # Exports: ingest_documents, load_index, search_documents
│   │   ├── pipeline.py    # Orchestrator (ingest + search)
│   │   ├── parser.py      # PDF/DOCX parsing
│   │   ├── chunker.py     # Text chunking
│   │   ├── embeddings.py  # HuggingFace embeddings
│   │   └── vectorstore.py # FAISS index management
│   ├── graph.py           # LangGraph agent graph
│   ├── agents/            # Individual agent modules
│   ├── mcp_client.py      # MCP client wrappers
│   ├── ingest.py          # CLI ingestion script
│   ├── check_env.py       # Diagnostic: test all API keys & connections
│   ├── vectorstore/       # FAISS index (generated)
│   ├── .venv/             # Python virtual environment (do NOT commit)
│   └── .env               # Environment variables (do NOT commit)
├── mcp-servers/           # Local MCP servers
│   ├── docs/              # Document search MCP server
│   ├── timetable/         # Timetable MCP server
│   └── notices/           # Notices MCP server (optional)
├── data/
│   ├── docs/              # Uploaded PDFs/DOCX
│   ├── timetable/         # Uploaded CSV files
│   └── index/             # FAISS index files
└── eval/                  # Evaluation dataset + runner
```

---

## Commands

### Frontend
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server on http://localhost:3000
npm run build        # Production build
npm run lint         # Run ESLint
```

### Backend
```bash
cd backend

# ⚠️ CRITICAL: Always install packages in the LOCAL virtual environment!
.venv\Scripts\pip install -r requirements.txt                  # Install deps (Windows)
# OR on Linux/Mac: .venv/bin/pip install -r requirements.txt

python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload   # Start dev server
python ingest.py                                              # Run document ingestion
```

### MCP Servers
```bash
cd mcp-servers/docs && python server.py      # Start Docs MCP server
cd mcp-servers/timetable && python server.py # Start Timetable MCP server
```

---

## Coding Rules

### General
- Use **TypeScript** for all frontend code, **Python** for all backend code
- All new functions must have **docstrings** (Python) or **JSDoc comments** (TypeScript)
- Use **async/await** for all asynchronous operations
- Never hardcode API URLs — use environment variables
- Never commit `.env` files or API keys

### Frontend (Next.js)
- Use the **App Router** (not Pages Router)
- Use **Tailwind CSS** for all styling — no inline styles or CSS modules
- Components go in `app/components/`
- Always use `"use client"` directive for client-side components
- Store auth token in `localStorage` under the key `"token"`
- API base URL: `http://localhost:8000` (backend)
- Always send `Authorization: Bearer <token>` header with API requests

### Backend (FastAPI)
- All endpoints requiring auth must use `Depends(get_current_user)`
- Use **Pydantic models** for all request/response schemas
- Files are stored locally in `./data/docs/` and `./data/timetable/`
- CORS is configured for `http://localhost:3000` only
- Environment variables are loaded via `python-dotenv` at the top of `main.py`
- Use `os.makedirs(..., exist_ok=True)` before writing files

### RAG Pipeline
- Chunk size: **400–800 tokens**, overlap: **80–120 tokens**
- Use `RecursiveCharacterTextSplitter` from LangChain
- Always preserve document metadata: `doc_id`, `title`, `page_number`, `tags`
- Citations are **required** for all document-based answers (doc name, page, section)
- If retrieval returns no results, the response must say: *"I don't have this information in the uploaded documents"*

### LangGraph Agents
- Each agent is a **separate Python module** in `backend/agents/`
- All agents share a `GraphState` TypedDict (defined in `graph.py`)
- Supervisor agent classifies intent and routes to specialists
- Response Writer agent always includes citations when docs were used
- The graph is invoked from the `/chat` endpoint in `main.py`

### MCP Servers
- Each MCP server is in its own directory under `mcp-servers/`
- Use the Python `mcp` SDK
- The backend is the **MCP client** — it calls MCP tools when agents need them
- Tools follow naming: `docs.search()`, `timetable.get()`, `deadlines.get()`

---

## Environment Variables

### Backend (`backend/.env`)
```env
SUPABASE_URL=<supabase-project-url>
SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key>
GOOGLE_API_KEY=<google-gemini-api-key>
HUGGINGFACE_API_KEY=<huggingface-api-key>
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_SUPABASE_URL=<supabase-project-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<supabase-anon-key>
```

---

## Architecture Notes

- **Auth flow**: Frontend calls Supabase Auth → gets JWT → sends to backend in `Authorization` header → backend validates via Supabase REST API
- **Chat flow**: User message → `/chat` endpoint → LangGraph graph → agents call MCP tools → Response Writer → return `{ response, sources }`
- **Ingestion flow**: Admin uploads file → `/upload` → file saved to `./data/docs/` → run `ingest.py` or `/rebuild-index` → parse → chunk → embed → save FAISS index
- **MCP flow**: LangGraph agent needs data → backend MCP client calls MCP server tool → result fed back into graph state

---

## Testing Conventions

- Evaluation dataset: 50–80 campus questions in `eval/questions.json`
- Run evaluation: `python eval/runner.py`
- Metrics tracked: correctness (1–5), citation accuracy, latency (ms), tool call success rate
- Runtime logs: per-query latency, token usage, MCP tools called, docs cited

---

## Do NOT

- Do not use `var` in TypeScript — use `const` or `let`
- Do not use the Pages Router — this project uses App Router
- Do not install Qdrant or Docker unless explicitly asked — use FAISS (local)
- Do not use direct database connections — all auth goes through Supabase REST API
- Do not generate answers without citations when documents are involved
- Do not skip error handling — always wrap API calls in try/catch
- **Do not install Python packages globally** — always use `.venv\Scripts\pip install` (Windows) or `.venv/bin/pip install` (Linux/Mac)
