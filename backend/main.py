# ==================== LOAD ENV ====================
from dotenv import load_dotenv
load_dotenv()

# ==================== IMPORTS ====================
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import json
import shutil
import requests

from rag import load_index, ingest_documents
import traceback


# ==================== LIFESPAN (STARTUP) ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to Qdrant vector store on server startup."""
    try:
        load_index()
        print("Qdrant index connected successfully!")
    except RuntimeError:
        print("WARNING: Qdrant collection not found. Run 'python ingest.py' first.")
    yield


# ==================== APP ====================
app = FastAPI(title="Campus Assistant API", lifespan=lifespan)

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== SUPABASE CONFIG ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase environment variables not set")

# Note: LLM is now configured inside agents/ (supervisor, timetable_agent, response_writer)

# ==================== AUTH (SUPABASE) ====================
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        response = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
            },
            timeout=10
        )

        if response.status_code != 200:
            print(f"Supabase auth failed with status {response.status_code}: {response.text}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_data = response.json()
        
        # Verify role
        try:
            role_resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/user_roles?id=eq.{user_data['id']}&select=role",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                },
                timeout=5
            )
            is_admin = False
            if role_resp.status_code == 200:
                roles = role_resp.json()
                if roles and len(roles) > 0 and roles[0].get("role") == "admin":
                    is_admin = True
            user_data["is_admin"] = is_admin
        except Exception as e:
            print(f"Error fetching role: {e}")
            user_data["is_admin"] = False

        return user_data
    except requests.exceptions.RequestException as e:
        print(f"Supabase network error: {e}")
        raise HTTPException(status_code=500, detail=f"Auth network error: {str(e)}")
    except Exception as e:
        print(f"Unexpected auth error: {e}")
        raise HTTPException(status_code=500, detail=f"Auth internal error: {str(e)}")

def require_admin(user=Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# ==================== HEALTH ====================
@app.get("/")
def root():
    return {"message": "Campus Assistant API running"}

# ==================== CURRENT USER ====================
@app.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "is_admin": user.get("is_admin", False)
    }

# ==================== ASSIGN ROLE ====================
class RoleAssignRequest(BaseModel):
    user_id: str
    role: str

@app.post("/assign-role")
def assign_role(request: RoleAssignRequest):
    if request.role not in ["student", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/user_roles",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            json={"id": request.user_id, "role": request.role},
            timeout=5
        )
        if response.status_code not in (200, 201, 204):
            raise HTTPException(status_code=response.status_code, detail="Failed to assign role")
        return {"message": "Role assigned successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TAG STORAGE HELPERS ====================
DOC_TAGS_PATH = os.path.join(os.path.dirname(__file__), "doc_tags.json")

def _load_tags() -> dict:
    if not os.path.exists(DOC_TAGS_PATH):
        return {}
    with open(DOC_TAGS_PATH, "r") as f:
        return json.load(f)

def _save_tags(tags: dict) -> None:
    with open(DOC_TAGS_PATH, "w") as f:
        json.dump(tags, f, indent=2)

# ==================== FILE UPLOAD ====================
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    department: str = Form(default=""),
    year: str = Form(default=""),
    course: str = Form(default=""),
    user=Depends(get_current_user),
):
    os.makedirs("data/docs", exist_ok=True)
    path = f"data/docs/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Save tags for this file
    tags = _load_tags()
    tags[file.filename] = {
        "department": department.strip(),
        "year": year.strip(),
        "course": course.strip(),
    }
    _save_tags(tags)

    return {"message": "File uploaded", "path": path}

# ==================== ADMIN ROUTING ====================
@app.get("/admin/docs")
def list_admin_docs(user=Depends(require_admin)):
    docs_dir = "data/docs"
    if not os.path.exists(docs_dir):
        return []
    
    tags = _load_tags()
    files = []
    for filename in os.listdir(docs_dir):
        file_path = os.path.join(docs_dir, filename)
        if os.path.isfile(file_path):
            file_tags = tags.get(filename, {})
            files.append({
                "name": filename,
                "size": os.path.getsize(file_path),
                "department": file_tags.get("department", ""),
                "year": file_tags.get("year", ""),
                "course": file_tags.get("course", ""),
            })
    return files

@app.delete("/admin/docs/{filename}")
def delete_admin_doc(filename: str, user=Depends(require_admin)):
    docs_dir = "data/docs"
    file_path = os.path.join(docs_dir, filename)
    
    if not os.path.abspath(file_path).startswith(os.path.abspath(docs_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        os.remove(file_path)
        # Also clean up tags entry
        tags = _load_tags()
        tags.pop(filename, None)
        _save_tags(tags)
        return {"message": f"Deleted {filename} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/docs/{filename}/view")
def view_admin_doc(filename: str, user=Depends(require_admin)):
    docs_dir = "data/docs"
    file_path = os.path.join(docs_dir, filename)
    
    # Simple path traversal protection
    if not os.path.abspath(file_path).startswith(os.path.abspath(docs_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path)

@app.get("/admin/logs")
def get_admin_logs(user=Depends(require_admin)):
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/chat_logs?select=*&order=created_at.desc&limit=100",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=500, detail="Failed to fetch logs")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-timetable")
async def upload_timetable(
    file: UploadFile = File(...),
    group: str = Form(default=""),
    user=Depends(require_admin)
):
    os.makedirs("data/timetable", exist_ok=True)
    if group.strip():
        # Save group-specific file: timetable_CS-A.csv, timetable_CS-B.csv etc.
        safe_group = group.strip().upper().replace(" ", "-")
        path = f"data/timetable/timetable_{safe_group}.csv"
    else:
        # Falling back to shared / global timetable
        path = "data/timetable/timetable.csv"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"Timetable uploaded successfully", "path": path}

@app.post("/upload-deadlines")
async def upload_deadlines(file: UploadFile = File(...), user=Depends(require_admin)):
    os.makedirs("data/timetable", exist_ok=True)
    path = f"data/timetable/deadlines.csv"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": "Deadlines uploaded successfully"}

@app.get("/admin/deadlines")
def get_admin_deadlines(user=Depends(require_admin)):
    """Read deadlines.csv and return rows as a list of dicts."""
    path = "data/timetable/deadlines.csv"
    if not os.path.exists(path):
        return {"exists": False, "rows": [], "headers": []}
    try:
        import csv as _csv
        with open(path, "r", encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
        headers = list(rows[0].keys()) if rows else []
        return {
            "exists": True,
            "rows": rows,
            "headers": headers,
            "size": os.path.getsize(path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/deadlines")
def delete_admin_deadlines(user=Depends(require_admin)):
    """Delete the uploaded deadlines.csv file."""
    path = "data/timetable/deadlines.csv"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No deadlines file found")
    try:
        os.remove(path)
        return {"message": "Deadlines deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/notices")
def get_admin_notices(user=Depends(require_admin)):
    path = "data/notices/notices.json"
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

@app.get("/admin/timetable")
def get_admin_timetable(user=Depends(require_admin)):
    """List all uploaded timetable files with their row counts."""
    timetable_dir = "data/timetable"
    if not os.path.exists(timetable_dir):
        return []
    import csv as _csv
    results = []
    for fname in sorted(os.listdir(timetable_dir)):
        if not fname.endswith(".csv") or fname == "deadlines.csv":
            continue
        fpath = os.path.join(timetable_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                rows = list(_csv.DictReader(f))
            # Derive the group label from the filename
            if fname == "timetable.csv":
                group_label = "Shared / Global"
            else:
                group_label = fname.replace("timetable_", "").replace(".csv", "")
            # Read column headers for the first file to show in preview
            headers = list(rows[0].keys()) if rows else []
            results.append({
                "filename": fname,
                "group": group_label,
                "rows": rows,
                "headers": headers,
                "row_count": len(rows),
                "size": os.path.getsize(fpath),
            })
        except Exception as e:
            results.append({"filename": fname, "group": fname, "error": str(e), "rows": [], "headers": [], "row_count": 0, "size": 0})
    return results

@app.delete("/admin/timetable/{filename}")
def delete_admin_timetable(filename: str, user=Depends(require_admin)):
    """Delete a specific timetable file by filename (e.g. timetable_CS-A.csv)."""
    timetable_dir = os.path.abspath("data/timetable")
    file_path = os.path.join(timetable_dir, filename)
    if not file_path.startswith(timetable_dir):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.endswith(".csv") or filename == "deadlines.csv":
        raise HTTPException(status_code=400, detail="Invalid file")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        os.remove(file_path)
        return {"message": f"Deleted {filename} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/notices/{notice_index}")
def delete_admin_notice(notice_index: int, user=Depends(require_admin)):
    """Delete a single notice by its index in the notices.json array."""
    path = "data/notices/notices.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="notices.json not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if notice_index < 0 or notice_index >= len(data):
            raise HTTPException(status_code=404, detail="Notice index out of range")
        data.pop(notice_index)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"message": "Notice deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-notices")
async def upload_notices(file: UploadFile = File(...), user=Depends(require_admin)):
    os.makedirs("data/notices", exist_ok=True)
    path = "data/notices/notices.json"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": "Notices updated successfully"}

@app.post("/rebuild-index")
def rebuild_index(user=Depends(require_admin)):
    try:
        # Read saved tags and pass to ingestion
        tags_map = _load_tags()
        ingest_documents("data/docs", tags_map=tags_map)
        # Reload the index into memory
        load_index()
        return {"message": "Search index rebuilt successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from graph import campus_graph

# ==================== CHAT SESSIONS ====================
@app.get("/chat/sessions")
def get_chat_sessions(user=Depends(get_current_user)):
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/chat_sessions?user_id=eq.{user['id']}&select=id,title,updated_at&order=updated_at.desc",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch sessions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/sessions/{session_id}")
def get_chat_session(session_id: str, user=Depends(get_current_user)):
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{session_id}&user_id=eq.{user['id']}&select=messages",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if not data:
                raise HTTPException(status_code=404, detail="Session not found")
            return data[0]["messages"]
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch session")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SessionRenameRequest(BaseModel):
    title: str

@app.put("/chat/sessions/{session_id}")
def rename_chat_session(session_id: str, request: SessionRenameRequest, user=Depends(get_current_user)):
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{session_id}&user_id=eq.{user['id']}",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/json",
            },
            json={"title": request.title},
            timeout=5
        )
        if response.status_code in (200, 204):
            return {"message": "Session renamed successfully"}
        raise HTTPException(status_code=response.status_code, detail="Failed to rename session")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/sessions/{session_id}")
def delete_chat_session(session_id: str, user=Depends(get_current_user)):
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{session_id}&user_id=eq.{user['id']}",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
            },
            timeout=5
        )
        if response.status_code in (200, 204):
            return {"message": "Session deleted successfully"}
        raise HTTPException(status_code=response.status_code, detail="Failed to delete session")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CHAT ====================
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    session_id: str | None = None

import json
import uuid

@app.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    # Generate new session ID if one doesn't exist
    session_id = request.session_id if request.session_id else str(uuid.uuid4())
    is_new_session = not bool(request.session_id)

    # Calculate title from first message
    title = request.message[:50] + "..." if len(request.message) > 50 else request.message

    if is_new_session:
        try:
            requests.post(
                f"{SUPABASE_URL}/rest/v1/chat_sessions",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Content-Type": "application/json",
                    "Prefer": "resolution=ignore-duplicates"
                },
                json={
                    "id": session_id,
                    "user_id": user["id"],
                    "title": title,
                    "messages": request.history + [{"role": "user", "content": request.message}],
                    "updated_at": "now()"
                },
                timeout=5
            )
        except Exception as e:
            print(f"Error pre-saving chat session: {e}")

    async def event_generator():
        import time
        start_time = time.time()
        final_intent = "unknown"
        
        # We need to accumulate the full trace array and final response to sync to the database
        assistant_traces = []
        assistant_response = ""
        
        try:
            # Yield the session_id first so the frontend can lock it in natively
            yield json.dumps({"type": "session_id", "session_id": session_id}) + "\n"
            
            # First trace
            trace_msg = "> [Supervisor Agent] Analyzing query intent..."
            assistant_traces.append(trace_msg)
            yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"

            # Run the LangGraph multi-agent pipeline
            async for event in campus_graph.astream({
                "query": request.message,
                "history": request.history,
                "intent": "",
                "context": [],
                "sources": [],
                "response": "",
            }, stream_mode="updates"):
                
                for node_name, state_update in event.items():
                    if node_name == "supervisor":
                        final_intent = state_update.get("intent", "unknown")
                        trace_msg = f"> [Supervisor Agent] Intent classified as: {final_intent.upper()}"
                        assistant_traces.append(trace_msg)
                        yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                    
                    elif node_name == "rag_agent":
                        trace_msg = "> [RAG Agent] Searching vector database for relevant university documents..."
                        assistant_traces.append(trace_msg)
                        yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                        
                    elif node_name == "timetable_agent":
                        trace_msg = "> [Timetable Agent] Querying Timetable MCP Server for live schedules and deadlines..."
                        assistant_traces.append(trace_msg)
                        yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                        
                    elif node_name == "planner_agent":
                        trace_msg = "> [Planner Agent] Generating personalized study schedule..."
                        assistant_traces.append(trace_msg)
                        yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                        
                    elif node_name == "response_writer":
                        trace_msg = "> [Response Writer] Synthesizing final response based on retrieved context..."
                        assistant_traces.append(trace_msg)
                        yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                        
                        assistant_response = state_update.get("response", "")
                        yield json.dumps({
                            "type": "result",
                            "response": assistant_response,
                            "sources": state_update.get("sources", [])
                        }) + "\n"
            
            # Save the full chat state to Supabase
            # Note: We must construct the final messages array reflecting the user msg and new AI response
            updated_messages = request.history + [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": assistant_response, "traces": assistant_traces}
            ]

            payload = {
                "id": session_id,
                "user_id": user["id"],
                "title": title if is_new_session else None, # Only set title if new session, though we use upsert
                "messages": updated_messages,
                "updated_at": "now()"
            }
            if is_new_session:
                payload["title"] = title
            else:
                # If it's an existing session, we omit title to avoid overwriting it
                payload.pop("title", None)

            try:
                requests.post(
                    f"{SUPABASE_URL}/rest/v1/chat_sessions",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                        "apikey": SUPABASE_SERVICE_ROLE_KEY,
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates"
                    },
                    json=payload,
                    timeout=5
                )
            except Exception as db_err:
                print(f"Error saving chat session: {db_err}")

            # Log telemetry (existing)
            latency_ms = int((time.time() - start_time) * 1000)
            try:
                requests.post(
                    f"{SUPABASE_URL}/rest/v1/chat_logs",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                        "apikey": SUPABASE_SERVICE_ROLE_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "user_id": user["id"],
                        "query": request.message,
                        "intent": final_intent,
                        "latency_ms": latency_ms
                    },
                    timeout=5
                )
            except Exception as e:
                print(f"Error saving chat log to Supabase: {e}")

        except Exception as e:
            print(f"Error in chat stream generator: {e}")
            traceback.print_exc()
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

