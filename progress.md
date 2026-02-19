# Campus Assistant — Progress Tracker

> Last updated: 2026-02-19

---

## Week 1 — UI, Auth & Backend Shell ✅

- [x] **Login page** (`/login`) — email/password with Supabase Auth
- [x] **Signup page** (`/signup`) — email/password registration
- [x] **Chat UI** — `ChatInterface.tsx` sends messages to `/chat`
- [x] **Logout button** — clears token, redirects to `/login`
- [x] **Auth guard** — redirects to login if no token
- [x] **Admin upload page** (`/admin`) — basic file upload form
- [x] **FastAPI app** with CORS
- [x] **JWT auth** via Supabase — `get_current_user()` validates tokens
- [x] **Health endpoint** (`GET /`)
- [x] **Current user endpoint** (`GET /me`)
- [x] **File upload endpoint** (`POST /upload`) — saves to `./data/docs`
- [x] **Chat endpoint** (`POST /chat`) — wired with RAG + Gemini LLM
- [x] **Local storage** (`./data/docs`) created

---

## Week 2 — RAG Pipeline ✅

- [x] PDF parsing — extract text per page (`pdfplumber`)
- [x] DOCX parsing — extract text (`python-docx`)
- [x] Metadata storage — `source`, `page` preserved in chunk metadata
- [x] Chunking — 500 tokens, 100 overlap (`RecursiveCharacterTextSplitter`)
- [x] Embedding generation — HuggingFace `all-MiniLM-L6-v2` (via `langchain-huggingface`)
- [x] FAISS vector store setup — store vectors + metadata
- [x] Save/load FAISS index to/from disk (`backend/vectorstore/`)
- [x] Semantic search retrieval — top-k with citations (doc name, page)
- [x] Created modular `backend/rag/` package (parser, chunker, embeddings, vectorstore, pipeline)
- [x] Created `backend/ingest.py` — CLI script for ingestion
- [x] Wired RAG into `/chat` endpoint with Gemini 2.5 Flash LLM
- [x] Created `backend/check_env.py` — diagnostic script to test all API keys & connections
- [x] Switched LLM from OpenRouter/GPT-4o-mini → Google Gemini 2.5 Flash (`langchain-google-genai`)

---

## Week 3 — MCP Servers ❌ Not Started

- [ ] **Docs MCP Server** (`mcp-servers/docs/server.py`)
  - [ ] `docs.search(query, filters)` tool
  - [ ] `docs.get_chunk(doc_id, chunk_id)` tool
  - [ ] Resource: list of available docs, metadata, tags
- [ ] **Timetable MCP Server** (`mcp-servers/timetable/server.py`)
  - [ ] `timetable.get(day, student_group)` tool
  - [ ] `deadlines.get(course_id)` tool
  - [ ] Resource: timetable CSV versions, last updated
- [ ] **Backend MCP client** (`backend/mcp_client.py`) — wrapper functions
- [ ] Create `./data/timetable/` directory
- [ ] Test MCP servers locally

---

## Week 4 — LangGraph Multi-Agent Orchestration ❌ Not Started

- [ ] **Supervisor Agent** — routes queries to specialists
- [ ] **Retriever Agent (RAG)** — calls Docs MCP tools, builds citations
- [ ] **Timetable Agent** — calls Timetable MCP tools
- [ ] **Planner Agent** — generates study plans
- [ ] **Response Writer Agent** — produces final cited answers
- [ ] **Safety/Scope Agent** *(optional)* — blocks out-of-scope queries
- [ ] Define `GraphState` (shared state: messages, intent, chunks, tools, answer)
- [ ] Create `backend/graph.py` — LangGraph definition (nodes + edges)
- [ ] Create `backend/agents/` directory with agent files
- [ ] Tool calling flow integrated into the graph
- [ ] **Wire `/chat` endpoint** to run full LangGraph pipeline

---

## Week 5 — Admin Features & Evaluation ❌ Not Started

- [ ] Document tagging (department, year, course)
- [ ] Timetable CSV upload endpoint (`POST /upload-timetable`)
- [ ] Rebuild index button (`POST /rebuild-index`) — re-chunk, re-embed, update FAISS
- [ ] Admin logs view (`GET /admin/logs`) — queries, latency, tool calls, top sources
- [ ] Role-based auth (student vs admin) — currently no roles
- [ ] Create evaluation dataset — 50–80 campus questions with expected answers
- [ ] Evaluation runner script (`eval/runner.py`)
- [ ] Metrics: correctness (1-5), citation accuracy, latency, tool call success rate
- [ ] Runtime logging per query (latency, tokens, MCP calls, docs cited)

---

## Week 6 — Polish & Deliverables ❌ Not Started

- [ ] Streaming responses in Chat UI (SSE or chunked transfer)
- [ ] Notices MCP Server *(optional)*
- [ ] Architecture diagram
- [ ] LangGraph workflow description
- [ ] MCP servers and tools list
- [ ] RAG pipeline with citations logic documentation
- [ ] Evaluation results and logs
- [ ] Project report (final document)
- [ ] Demo video (5–8 minutes)

---

## Summary

| Area | Status |
|---|---|
| Auth (Login/Signup/Logout) | ✅ Complete |
| Chat UI + RAG integration | ✅ Complete (Gemini 2.5 Flash) |
| RAG Pipeline (rag/ package) | ✅ Complete |
| Admin Upload UI | ✅ Basic form done |
| MCP Servers | ❌ Not started |
| LangGraph Agents | ❌ Not started |
| Evaluation & Logging | ❌ Not started |
| Streaming | ❌ Not started |
| Final Report & Demo | ❌ Not started |

### Current Focus: **Week 3 — MCP Servers**

Weeks 1–2 are complete. The RAG pipeline is fully built and the `/chat` endpoint returns AI-powered answers with citations using Google Gemini 2.5 Flash. Next step is building MCP servers for document search and timetable tools.

