# Campus Assistant — MCP Servers

> **Built with**: [FastMCP](https://gofastmcp.com) | **Transport**: stdio | **Protocol**: [Model Context Protocol](https://modelcontextprotocol.io)

Three local MCP servers expose campus data to the LangGraph agent graph via standardised tool calls.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Directory Structure](#directory-structure)
3. [Docs MCP Server](#1-docs-mcp-server)
4. [Timetable MCP Server](#2-timetable-mcp-server)
5. [Notices MCP Server](#3-notices-mcp-server)
6. [Backend MCP Client](#4-backend-mcp-client)
7. [Data Files](#5-data-files)
8. [Testing](#6-testing)
9. [Troubleshooting](#7-troubleshooting)

---

## Architecture

```
FastAPI Backend (main.py)
        │
        │  spawns via stdio
        │
        ├──► Docs MCP Server (mcp-servers/docs/server.py)
        │        Tools: search_docs, get_chunk
        │        Data:  FAISS vector index
        │
        ├──► Timetable MCP Server (mcp-servers/timetable/server.py)
        │        Tools: get_timetable, get_deadlines
        │        Data:  timetable_*.csv, deadlines.csv (per-group files)
        │
        └──► Notices MCP Server (mcp-servers/notices/server.py)
                 Tools: get_latest_notices
                 Data:  notices.json
```

Each MCP server runs as a **subprocess** started on demand. The backend (`mcp_client.py`) spawns it, performs the MCP handshake, calls a tool, and lets the subprocess exit. Communication is over **stdin/stdout (stdio transport)** using JSON-RPC 2.0.

---

## Directory Structure

```
mcp-servers/
├── README.md
├── docs/
│   ├── __init__.py
│   └── server.py            ← Docs MCP Server
├── timetable/
│   ├── __init__.py
│   └── server.py            ← Timetable MCP Server (per-group support)
└── notices/
    ├── __init__.py
    └── server.py            ← Notices MCP Server

backend/
├── mcp_client.py            ← Async MCP client wrappers
└── main.py                  ← Calls mcp_client from LangGraph agents

data/
├── docs/                    ← Uploaded PDFs and DOCX files
├── timetable/
│   ├── timetable.csv        ← Shared/fallback timetable
│   ├── timetable_CS-A.csv   ← Group-specific timetable
│   ├── timetable_CS-B.csv
│   └── deadlines.csv        ← Assignment/exam deadlines
└── notices/
    └── notices.json
```

---

## 1. Docs MCP Server

**File**: `mcp-servers/docs/server.py`
**Purpose**: Wraps the FAISS vector store and exposes it as MCP tools.

### Tool: `search_docs(query, top_k=5)`

Runs semantic similarity search over the FAISS index. Returns the top-k matching chunks with `source`, `page`, and `content`.

```python
Input:  search_docs("attendance policy", top_k=3)
Output: [
  {"source": "Academic_Policy_Handbook.pdf", "page": 2, "content": "..."},
  {"source": "CS_Department_Handbook.pdf",   "page": 4, "content": "..."}
]
```

Returns `[{"error": "FAISS index not found..."}]` if the index has not been built yet.

### Tool: `get_chunk(doc_name, page)`

Fetches a specific page chunk by doing a broad FAISS search then filtering by filename and page number.

### Resource: `docs://catalog`

Returns a JSON list of all uploaded documents with `filename`, `size_kb`, and `extension`.

---

## 2. Timetable MCP Server

**File**: `mcp-servers/timetable/server.py`
**Purpose**: Reads structured CSV data for class schedules and deadlines. Supports **per-group timetable files**.

### Per-Group File Resolution

When `student_group` is provided, the server first looks for `timetable_{GROUP}.csv` (e.g., `timetable_CS-A.csv`). If found, it reads only that file and filters by `day`. If not found, it falls back to the shared `timetable.csv` and filters by both `day` and `student_group` column.

```
get_timetable(day="Monday", student_group="CS-A")
    1. Check for data/timetable/timetable_CS-A.csv
    2. If found → filter rows by day only (fast path)
    3. If not found → read timetable.csv, filter by day AND student_group column
```

### Tool: `get_timetable(day, student_group=None)`

| Parameter | Type | Example |
|---|---|---|
| `day` | str (required) | `"Monday"` |
| `student_group` | str (optional) | `"CS-A"` |

Returns list of classes with `day`, `time`, `course_id`, `course_name`, `faculty`, `room`, `student_group`.

If group-specific data is not found: `[{"message": "No classes found for Monday in group CS-A"}]`
If CSV is missing entirely: `[{"error": "Timetable data not found. Please ask an admin to upload a timetable."}]`

### Tool: `get_deadlines(course_id=None)`

Reads `deadlines.csv`, optionally filters by `course_id`, sorts by `due_date`, and returns only upcoming deadlines (due_date ≥ today).

```python
Input:  get_deadlines("CS401")
Output: [
  {"course_id": "CS401", "title": "Assignment 1", "type": "Assignment",
   "due_date": "2026-04-05", "description": "Implement linear regression..."}
]
```

### Resource: `timetable://metadata`

Returns JSON summary of all available days, student groups (from both group-specific files and shared file), course IDs, entry counts, and a list of uploaded group files.

---

## 3. Notices MCP Server

**File**: `mcp-servers/notices/server.py`
**Purpose**: Reads `data/notices/notices.json` and exposes latest notices.

### Tool: `get_latest_notices(department=None, limit=5)`

Returns the most recent notices, optionally filtered by department.

```python
Input:  get_latest_notices(department="CS", limit=3)
Output: [
  {"title": "Exam Schedule Updated", "content": "...", "department": "CS"}
]
```

---

## 4. Backend MCP Client

**File**: `backend/mcp_client.py`
**Purpose**: Async wrappers that LangGraph agents call.

### Available Functions

| Function | MCP Server | Tool |
|---|---|---|
| `search_docs(query, top_k)` | Docs | `search_docs` |
| `get_doc_chunk(doc_name, page)` | Docs | `get_chunk` |
| `get_timetable(day, student_group)` | Timetable | `get_timetable` |
| `get_deadlines(course_id)` | Timetable | `get_deadlines` |
| `get_latest_notices(department, limit)` | Notices | `get_latest_notices` |

### How it Works

```python
async with _get_timetable_session() as session:
    result = await session.call_tool("get_timetable", arguments={"day": "Monday", "student_group": "CS-A"})
    return result.content[0].text
```

FastMCP's stdout banner is suppressed by setting `FASTMCP_LOG_LEVEL=CRITICAL` in the subprocess environment.

---

## 5. Data Files

### Timetable CSVs

| Column | Description | Example |
|---|---|---|
| `day` | Day of the week | `Monday` |
| `time` | Time slot (24h) | `08:00-09:00` |
| `course_id` | Course code | `CS401` |
| `course_name` | Full name | `Machine Learning` |
| `faculty` | Instructor | `Dr. Emily Carter` |
| `room` | Room/lab | `Room 301` |
| `student_group` | Section | `CS-A` |

Files: `timetable.csv` (shared), `timetable_CS-A.csv`, `timetable_CS-B.csv`, etc.

### `deadlines.csv`

| Column | Description | Example |
|---|---|---|
| `course_id` | Course code | `CS401` |
| `course_name` | Full course name | `Machine Learning` |
| `title` | Deadline title | `Assignment 1 – Linear Regression` |
| `type` | Category | `Assignment` / `Exam` / `Lab` / `Project` / `Quiz` |
| `due_date` | ISO date | `2026-04-05` |
| `description` | Details | `Implement and compare...` |

### `notices.json`

```json
[
  {"title": "Exam Timetable Released", "content": "...", "department": "CS"},
  {"title": "Library Holiday Notice", "content": "...", "department": "General"}
]
```

---

## 6. Testing

### Standalone self-test (no MCP protocol)
```bash
cd backend && .venv\Scripts\activate
python ..\mcp-servers\timetable\server.py --test
python ..\mcp-servers\docs\server.py --test
```

### MCP client connectivity test
```bash
cd backend && .venv\Scripts\activate
python mcp_client.py
# Expected:
# Testing Docs MCP Server connection...
#   -> Connected! Found tools: ['search_docs', 'get_chunk']
# Testing Timetable MCP Server connection...
#   -> Connected! Found tools: ['get_timetable', 'get_deadlines']
# Testing Notices MCP Server connection...
#   -> Connected! Found tools: ['get_latest_notices']
```

### End-to-end via Chat UI
| Query | Expected Route | Expected Result |
|---|---|---|
| "What classes does CS-A have on Monday?" | Timetable MCP | 4 classes listed |
| "When is the CS401 assignment due?" | Timetable MCP | Deadline list |
| "What is the attendance policy?" | RAG → FAISS | Policy text with citations |
| "Are there any CS notices?" | Notices MCP | Notice cards |

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: fastmcp` | Not installed | `pip install fastmcp` inside activated venv |
| `FAISS index not found` | Index not built | Run `python ingest.py` in `backend/` |
| `Timetable data not found` | Missing CSV | Upload via Admin → Timetable tab |
| Server hangs without `--test` | Normal — waiting for MCP stdin input | Use `--test` or call via `mcp_client.py` |
| `HuggingFace API key missing` | Missing env var | Add `HUGGINGFACE_API_KEY` to `backend/.env` |
