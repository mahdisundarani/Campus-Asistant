# AGENTS.md — AI Agent Instructions for Campus Assistant

> Context, rules, and coding standards for AI agents working on this codebase.

---

## Project Overview

**Campus Assistant** is a fully implemented enterprise-grade web app for university students and administrators. Students ask questions about campus policies, timetables, deadlines, and notices via a streaming AI chat. Admins manage content through a comprehensive control panel. The system uses RAG + LangGraph multi-agent orchestration + three MCP tool servers.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), Tailwind CSS v4 |
| Backend | FastAPI (Python 3.11+) |
| Auth | Supabase Auth (JWT tokens) |
| Orchestration | LangGraph (LangChain) |
| LLM | Google Gemini 2.5 Flash (`langchain-google-genai`) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (Inference API) |
| Vector Store | FAISS (local file) |
| MCP | Local MCP servers (`mcp` SDK + FastMCP) |
| Storage | Local filesystem (`./data/`) |

---

## Project Structure

```
Campus-Assistant/
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Chat page (streaming, typewriter effect)
│   │   ├── login/               # Login page (neon glassmorphic design)
│   │   ├── signup/              # Signup page
│   │   ├── admin/               # Admin control panel (6 tabs)
│   │   └── components/
│   │       ├── ChatInterface.tsx
│   │       └── Sidebar.tsx
│   └── lib/
│       ├── supabase.ts
│       └── api-client.ts        # apiFetch() — authenticated wrapper
├── backend/
│   ├── main.py                  # FastAPI app entry + all endpoints
│   ├── graph.py                 # LangGraph graph (nodes + edges)
│   ├── mcp_client.py            # Async MCP client wrappers
│   ├── agents/
│   │   ├── supervisor.py        # Intent classification + deterministic routing
│   │   ├── rag_agent.py         # RAG: Docs MCP → FAISS search → citations
│   │   ├── timetable_agent.py   # Timetable: clarification gate + MCP calls
│   │   ├── notice_agent.py      # Notices MCP queries
│   │   └── response_writer.py   # Final answer synthesis + citation formatting
│   ├── rag/
│   │   ├── pipeline.py          # Ingest + search orchestrator
│   │   ├── parser.py            # PDF/DOCX text extraction
│   │   ├── chunker.py           # Overlapping text chunks
│   │   ├── embeddings.py        # HuggingFace embedding calls
│   │   └── vectorstore.py       # FAISS save/load/search
│   ├── ingest.py                # CLI: rebuild the index
│   └── .env                     # Keys (do NOT commit)
├── mcp-servers/
│   ├── docs/server.py           # FastMCP: search_docs, get_chunk
│   ├── timetable/server.py      # FastMCP: get_timetable, get_deadlines (per-group)
│   └── notices/server.py        # FastMCP: get_latest_notices
└── data/
    ├── docs/                    # PDFs and DOCX files
    ├── timetable/               # timetable_CS-A.csv, deadlines.csv, etc.
    ├── notices/                 # notices.json
    └── index/                   # FAISS vectorstore files
```

---

## Commands

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
npm run build
npm run lint
```

### Backend
```bash
cd backend
.venv\Scripts\activate                          # Windows
.venv/bin/activate                              # Linux/Mac

pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
python ingest.py                                # Rebuild FAISS index
```

---

## Coding Rules

### General
- **TypeScript** for all frontend code, **Python** for all backend code
- All functions must have docstrings (Python) or JSDoc (TypeScript)
- Use `async/await` for all asynchronous operations
- Never hardcode API URLs — use environment variables
- Never commit `.env` or `.env.local` files

### Frontend (Next.js)
- Use **App Router** (never Pages Router)
- Use **Tailwind CSS** for all styling — no inline styles
- Components go in `app/components/`
- Always use `"use client"` directive for interactive components
- API calls go through `apiFetch()` in `lib/api-client.ts` — it attaches the Supabase session token automatically
- Auth state is managed via `supabase.auth.getSession()` — do not store tokens directly in `localStorage`

### Backend (FastAPI)
- Admin-only endpoints use `Depends(require_admin)`
- Auth-required endpoints use `Depends(get_current_user)`
- Files are stored locally: `../data/docs/`, `../data/timetable/`, `../data/notices/`
- CORS is configured for `http://localhost:3000` only
- Environment variables are loaded via `python-dotenv`
- Always use `os.makedirs(..., exist_ok=True)` before writing files
- Path traversal protection: always validate filenames before `os.remove()`

### Timetable System (Per-Group Files)
- Each student group gets its own CSV: `timetable_CS-A.csv`, `timetable_CS-B.csv`, etc.
- A shared fallback `timetable.csv` also exists for group-agnostic uploads
- The MCP server checks for group-specific file first, falls back to shared file
- Upload endpoint accepts optional `group` form field (saved as `timetable_{GROUP}.csv`)

### RAG Pipeline
- Chunk size: 400–800 tokens, overlap: 80–120 tokens
- Always preserve metadata: `source` (filename), `page` (number), tags
- Citations are **required** for all document-based answers
- If retrieval is empty: respond *"I don't have this information in the uploaded documents"*

### LangGraph Agents
- Each agent is a **separate module** in `backend/agents/`
- All agents share `GraphState` TypedDict defined in `graph.py`
- **Supervisor** deterministically routes short section replies (e.g., "cs-a") to the timetable agent
- **Timetable Agent** has a clarification gate: if `student_group` is missing → return clarification, do not call MCP
- **Response Writer** has a fast-path: if `clarification_needed` in context → return question directly, skip LLM

### MCP Servers
- Each server is a standalone FastMCP process in `mcp-servers/`
- Backend is the MCP **client** — it spawns servers as subprocesses via stdio transport
- Per request: new session opened → tool called → session closed (no persistent connection)
- Suppress FastMCP stdout banner: set `FASTMCP_LOG_LEVEL=CRITICAL` in `server_env`

---

## Environment Variables

### `backend/.env`
```env
SUPABASE_URL=<supabase-project-url>
SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key>
GOOGLE_API_KEY=<google-gemini-api-key>
HUGGINGFACE_API_KEY=<huggingface-api-key>
```

### `frontend/.env.local`
```env
NEXT_PUBLIC_SUPABASE_URL=<supabase-project-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<supabase-anon-key>
```

---

## Architecture Notes

- **Auth flow**: Frontend → Supabase Auth → JWT → `Authorization: Bearer <token>` header → backend validates via Supabase REST
- **Chat flow**: User message → `/chat` SSE endpoint → LangGraph graph → agents call MCP tools → Response Writer → streamed tokens
- **Streaming**: Backend uses `StreamingResponse` with `asyncio.Queue`; frontend uses `ReadableStream` with a 5ms typewriter delay per character
- **Ingestion flow**: Admin uploads file → `/upload` → saved to `./data/docs/` → `/rebuild-index` → parse → chunk → embed → FAISS index written
- **Timetable per-group**: Admin specifies group name on upload → saved as `timetable_{GROUP}.csv` → MCP server looks up group-specific file first

---

## Do NOT

- Do not use `var` in TypeScript — use `const` or `let`
- Do not use Pages Router — this project uses App Router
- Do not install Qdrant or Docker — use FAISS (local file-based)
- Do not make direct Supabase DB connections from the frontend — always go through the backend API for admin operations
- Do not generate document-based answers without citations
- Do not skip `try/catch` around API calls
- **Do not install Python packages globally** — always use `.venv\Scripts\pip install` (Windows)
- Do not delete `deadlines.csv` when deleting a group timetable — they are separate files
