# Campus Assistant — Progress Tracker

> Last updated: 2026-03-03

> **Core Philosophy**: Redesign and/or refine my product UI UX to feel like a top tier $100M ARR enterprise software product, with a premium, trustworthy, fast, and consistent experience across the entire app.

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
- [x] Switched LLM provider from `langchain-google-genai` → `langchain-openai` via **OpenRouter** (to avoid Gemini API rate limits)

---

## Week 3 — MCP Servers ✅

- [x] **Docs MCP Server** (`mcp-servers/docs/server.py`)
  - [x] `search_docs(query, top_k)` tool — semantic search over FAISS index
  - [x] `get_chunk(doc_name, page)` tool — fetch specific chunk by doc + page
  - [x] Resource: `docs://catalog` — list of all indexed documents with metadata
- [x] **Timetable MCP Server** (`mcp-servers/timetable/server.py`)
  - [x] `get_timetable(day, student_group)` tool — class schedule lookup
  - [x] `get_deadlines(course_id)` tool — upcoming deadlines
  - [x] Resource: `timetable://metadata` — available days, groups, courses, timestamps
- [x] **Backend MCP client** (`backend/mcp_client.py`) — async wrapper functions
- [x] Created `./data/timetable/` directory with `timetable.csv` and `deadlines.csv`
- [x] Self-test scripts built into each server (`--test` flag)
- [x] Connection test function in `mcp_client.py`
- [x] **Known Issue**: Docs MCP Server hangs when called via `stdio_client` due to FAISS/HuggingFace blocking the AnyIO event loop. RAG Agent now bypasses MCP and queries FAISS directly (see Week 4 notes).

---

### 📖 MCP Code Explanation

**What is MCP?**
MCP (Model Context Protocol) is a standardized protocol that lets an LLM (or agent) communicate with external data sources via **tools** (callable functions) and **resources** (read-only data). Instead of the backend hardcoding how to search docs or read timetables, MCP servers expose those capabilities as discoverable tools that any MCP-compatible client can call.

**Architecture Overview:**
```
User → Frontend → /chat endpoint → MCP Client → [Docs MCP Server | Timetable MCP Server]
                                        ↕                  ↕                    ↕
                                   (stdio IPC)         FAISS Index         CSV files
```

#### 1. Docs MCP Server (`mcp-servers/docs/server.py`)

- Built with **FastMCP** framework — registers tools and resources via decorators.
- **`@mcp.tool search_docs(query, top_k=5)`**: Loads the FAISS vector index (cached after first call via `_get_index()`), runs semantic search, and returns the top-k matching chunks with `source`, `page`, and `content`.
- **`@mcp.tool get_chunk(doc_name, page)`**: Searches across a broad set of results (top-50) and filters by document name (partial, case-insensitive match) and page number to return one specific chunk.
- **`@mcp.resource("docs://catalog")`**: Scans the `data/docs/` directory and returns a JSON catalog of all uploaded documents with filename, size, and extension.
- Internally reuses the same `rag.embeddings` and `rag.vectorstore` modules from Week 2 — so the FAISS index built by `ingest.py` is shared.

#### 2. Timetable MCP Server (`mcp-servers/timetable/server.py`)

- Also built with **FastMCP**.
- **`@mcp.tool get_timetable(day, student_group=None)`**: Reads `timetable.csv`, filters by day (case-insensitive), optionally filters by student group (e.g., `CS-A`), returns matching rows.
- **`@mcp.tool get_deadlines(course_id=None)`**: Reads `deadlines.csv`, optionally filters by course, sorts by due date, and returns only upcoming deadlines (date ≥ today).
- **`@mcp.resource("timetable://metadata")`**: Returns a JSON summary of all available days, student groups, courses, entry counts, and CSV last-modified timestamps.

#### 3. Backend MCP Client (`backend/mcp_client.py`)

- Acts as the **bridge** between the backend (FastAPI) and the MCP servers.
- Uses the official `mcp` Python SDK's `stdio_client` + `ClientSession` to spawn each server as a **subprocess** and communicate over **stdin/stdout** (stdio transport).
- Each call opens a session → initializes the MCP handshake → calls the tool → returns the result → closes the session.
- Exposes simple async functions: `search_docs()`, `get_doc_chunk()`, `get_timetable()`, `get_deadlines()`.
- Includes a `_test_connections()` function that verifies connectivity and lists available tools from both servers.

---

### 🧪 How to Test MCP Servers

**Prerequisites:** Activate the virtual environment and ensure dependencies are installed.

```bash
cd backend
.venv\Scripts\activate       # Windows
pip install fastmcp mcp
```

#### Test 1 — Self-test each server standalone

```bash
# Test Docs MCP Server (requires FAISS index to exist)
python ../mcp-servers/docs/server.py --test

# Test Timetable MCP Server
python ../mcp-servers/timetable/server.py --test
```

**Expected output for Docs:**
```
Docs MCP Server -- Self-Test
[1] Testing docs_catalog():  -> N documents found
[2] Testing search_docs('attendance policy'):  -> 5 results
[3] Testing search_docs('hostel rules'):  -> 5 results
All self-tests passed!
```

**Expected output for Timetable:**
```
Timetable MCP Server -- Self-Test
[1] Testing get_timetable('Monday'):  -> 8 results
[2] Testing get_timetable('Monday', 'CS-A'):  -> 4 results
[3] Testing get_deadlines('CS401'):  -> N results
[4] Testing get_deadlines() (all):  -> N results
[5] Testing timetable_metadata():  -> {"available_days": [...], ...}
All self-tests passed!
```

#### Test 2 — Test MCP client connectivity (full stdio round-trip)

```bash
cd backend
python mcp_client.py 
```

**Expected output:**
```
Testing Docs MCP Server connection...
  -> Connected! Found tools: ['search_docs', 'get_chunk']

Testing Timetable MCP Server connection...
  -> Connected! Found tools: ['get_timetable', 'get_deadlines']
```

This test spawns each server as a subprocess, does the MCP handshake, lists available tools, and verifies communication works end-to-end.

#### Test 3 — Run via batch scripts

```bash
# From project root
mcp-servers\timetable\run_timetable.bat
mcp-servers\docs\run_docs.bat
```

#### Troubleshooting

| Symptom | Likely Cause |
|---|---|
| `ModuleNotFoundError: fastmcp` | `fastmcp` not installed in the active venv |
| `FAISS index not found` | Run `python ingest.py` first to build the FAISS index |
| `Timetable data not found` | Missing `data/timetable/timetable.csv` |
| Connection hangs | Wrong Python path or server script path mismatch |

---

### 🔄 What Would Be Different Without MCP?

| Aspect | **With MCP** | **Without MCP** |
|---|---|---|
| **Architecture** | Modular — each data source runs as an independent server with a standard protocol | Monolithic — all document search and timetable logic lives directly inside `main.py` or the `rag/` package |
| **Tool Discovery** | LLM agents can dynamically discover available tools via `session.list_tools()` — no hardcoded function lists | Every tool must be manually imported and wired; the agent has no way to discover what's available at runtime |
| **Adding New Data Sources** | Add a new MCP server (e.g., Notices server) → the client auto-discovers it. **Zero changes** to existing code | Must modify the backend code, add new imports, update route handlers, and redeploy |
| **Isolation** | Each server runs in its own process — a crash in the Timetable server doesn't affect document search | A bug in timetable parsing could crash the entire backend |
| **LangGraph Integration (Week 4)** | Agents call MCP tools via the standard protocol — the Supervisor can route to any MCP tool dynamically | Each agent must have hardcoded function calls; routing logic becomes tightly coupled |
| **Testing** | Each server can be tested in complete isolation (`--test` flag) | Must spin up the entire backend to test any single feature |
| **Scalability** | Servers can be moved to separate machines or containers independently | Everything scales as one monolith |
| **Protocol Standard** | Follows the open MCP standard — compatible with any MCP client (Claude Desktop, other agents, etc.) | Custom API only — nothing external can use your tools without custom integration |

**In short:** Without MCP, the project would still work — the `/chat` endpoint currently calls RAG directly. But MCP is the foundation that enables **Week 4's LangGraph multi-agent orchestration**, where a Supervisor Agent can dynamically route queries to specialized agents that each call MCP tools. Without MCP, the agent system would be tightly coupled and much harder to extend.

---

## Week 4 — LangGraph Multi-Agent Orchestration ✅ Complete

- [x] **Supervisor Agent** (`agents/supervisor.py`) — classifies intent into `rag`, `timetable`, `deadline`, `planner`, `general`
- [x] **RAG Agent** (`agents/rag_agent.py`) — queries FAISS index directly (bypasses MCP due to stdio hanging issue)
- [x] **Timetable Agent** (`agents/timetable_agent.py`) — calls Timetable MCP tools for schedules and deadlines
- [x] **Planner Agent** (`agents/planner_agent.py`) — generates study plans
- [x] **Response Writer Agent** (`agents/response_writer.py`) — produces final cited markdown answers
- [x] Define `GraphState` (`agents/state.py`) — shared state: query, history, intent, context, sources, response
- [x] Create `backend/graph.py` — LangGraph definition (nodes + conditional edges)
- [x] Create `backend/agents/` directory with agent files
- [x] **Wire `/chat` endpoint** to run full LangGraph pipeline
- [x] **Chat context memory** — frontend sends conversation history, all agents use it for follow-up questions
- [x] **LLM Provider**: Switched to OpenRouter (`google/gemini-2.5-flash`) using `langchain-openai` to avoid Gemini API rate limits
- [x] **Supervisor prompt tuning** — academic calendar/holidays now correctly routed to RAG instead of deadline
- [x] **Response writer prompt tuning** — LLM now synthesizes answers from partially relevant context instead of requiring exact matches
- [x] **Timetable param extraction** — improved JSON parsing (finds `{}` in LLM output) and context-aware follow-ups (e.g., "What about Tuesday?" remembers CS-A)

---

## Week 5 — Admin Features & Evaluation ✅ Complete

- [x] Document tagging (department, year, course)
- [x] Timetable CSV upload endpoint (`POST /upload-timetable`)
- [x] Rebuild index button (`POST /rebuild-index`) — re-chunk, re-embed, update FAISS
- [x] Admin logs view (`GET /admin/logs`) — queries, latency, tool calls, top sources
- [x] Role-based auth (student vs admin) — Supabase user_roles integration
- [x] **Role selection toggle** on Login and Signup pages (Student / Administrator)
- [x] **`POST /assign-role`** backend endpoint — assigns role to Supabase `user_roles` table on signup
- [x] **Login role verification** — admin login checks `/me` for `is_admin`, rejects non-admins
- [x] Create evaluation dataset — 50 campus questions with expected intents and keywords (`eval/dataset.json`)
- [x] Evaluation runner script (`eval/runner.py`) — async with 60s per-query timeout
- [x] **Evaluation Results:**
  - Intent Routing Accuracy: **97.5%** (39/40 succeeded queries correctly routed)
  - Mean Latency: **5,378 ms** (for succeeded queries)
  - 40/50 queries succeeded, 10 timed out (all planner-intent — MCP subprocess bottleneck on Windows)
  - Only 1 misclassification: "club meetings" (expected: timetable, got: general)
- [x] Runtime logging per query (latency, tokens, MCP calls, docs cited)

---

## Week 6 — Polish & Deliverables ❌ Not Started

- [x] Streaming responses in Chat UI (SSE or chunked transfer)
- [x] Notices MCP Server *(optional)*
- [x] Architecture diagram
- [x] LangGraph workflow description
- [x] MCP servers and tools list
- [x] RAG pipeline with citations logic documentation
- [x] Evaluation results and logs
- [x] Project report (final document)
- [x] Demo video (5–8 minutes)

---

## Summary

| Area | Status |
|---|---|
| Auth (Login/Signup/Logout) | ✅ Complete (with Admin/Student role toggle) |
| Chat UI + RAG integration | ✅ Complete (Gemini 2.5 Flash via OpenRouter) |
| RAG Pipeline (rag/ package) | ✅ Complete |
| Admin Upload UI | ✅ Multi-tab layout complete (Docs, Timetables, Logs, Index) |
| MCP Servers | ✅ Complete (Docs + Timetable + Client) |
| LangGraph Agents | ✅ Complete (Supervisor, RAG, Timetable, Planner, Response Writer) |
| Chat Context Memory | ✅ Complete (frontend sends history, agents use it) |
| Logging & Auth | ✅ Complete (Supabase role-checking and telemetry logging) |
| Evaluation Data | ✅ Complete (50-query dataset, 97.5% intent accuracy) |
| Streaming | ✅ Complete (NDJSON trace streaming implemented) |
| Final Report & Demo | ✅ Complete- [x] **Hybrid RAG Implementation** — BM25 + FAISS ensemble search
- [x] **FlashRank Re-ranking** — local cross-encoder for precision
- [x] **UX Loading States** — centered spinners, skeletons, and transition feedback
- [x] **Admin Document Viewer** — secure PDF previewing from dashboard
| Document Tagging & Filtering | ✅ Complete (Advanced metadata filtering integrated) |

### Current Focus: **Week 6 — Polish & Deliverables**

All core features, evaluation, and advanced **Document Tagging/Filtering** are complete. Implementation includes a high-performance Hybrid RAG pipeline and a premium, responsive UX.

**Next Up**: Notices MCP Server (optional), and final technical documentation (architecture/workflow).
