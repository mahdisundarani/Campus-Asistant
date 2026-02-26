# ==================== LOAD ENV ====================
from dotenv import load_dotenv
load_dotenv()

# ==================== IMPORTS ====================
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import shutil
import requests

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from rag import load_index, search_documents


# ==================== LIFESPAN (STARTUP) ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the FAISS index into memory on server startup."""
    try:
        load_index()
        print("FAISS index loaded successfully!")
    except FileNotFoundError:
        print("WARNING: No FAISS index found. Run 'python ingest.py' first.")
    yield


# ==================== APP ====================
app = FastAPI(title="Campus Assistant API", lifespan=lifespan)

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== SUPABASE CONFIG ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase environment variables not set")

# ==================== LLM CONFIG ====================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.3,
)

# ==================== AUTH (SUPABASE) ====================
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    response = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
        },
    )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()

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
    }

# ==================== FILE UPLOAD ====================
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    os.makedirs("../data/docs", exist_ok=True)
    path = f"../data/docs/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"message": "File uploaded", "path": path}

from mcp_client import get_timetable, get_deadlines
from rag import load_index, search_documents

# ==================== CHAT ====================
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

SYSTEM_PROMPT = """You are a helpful campus assistant for Greenfield University. 
Answer student questions based ONLY on the context provided below.

**Formatting Rules:**
- Use **Markdown** for all answers.
- Use `## Headers` for sections.
- Use `* bullet points` for lists.
- Use `**bold**` for key terms.
- For document answers, always include citations with the document name and page number.
- For schedule/deadline answers, format the data clearly into tables or lists.

If the context does not contain the answer, say: "I don't have this information in the uploaded documents."

Context:
{context}
"""

@app.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    try:
        query_lower = request.message.lower()
        context_parts = []
        sources = []
        
        # Step 1: Detect Intent (Simple heuristic for Week 3 before LangGraph)
        is_timetable_query = any(kw in query_lower for kw in ["timetable", "schedule", "class", "monday", "tuesday", "wednesday", "thursday", "friday"])
        is_deadline_query = any(kw in query_lower for kw in ["deadline", "due", "assignment", "exam", "project"])

        if is_timetable_query or is_deadline_query:
            # === MCP TOOL PATH ===
            if is_deadline_query:
                # Extract simple course_id if present (e.g. CS401)
                course_id = None
                for word in query_lower.split():
                    if word.startswith("cs") and len(word) == 5 and word[2:].isdigit():
                        course_id = word.upper()
                        break
                
                result_str = await get_deadlines(course_id)
                context_parts.append(f"[MCP Tool: get_deadlines]:\n{result_str}")
                sources.append({"doc": "Timetable API (Deadlines)", "page": "Live Data"})
                
            if is_timetable_query:
                # Extract day if present
                days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                day = "Monday" # default
                for d in days:
                    if d in query_lower:
                        day = d.capitalize()
                        break
                
                # Extract group if present (e.g. CS-A)
                group = None
                if "cs-a" in query_lower: group = "CS-A"
                elif "cs-b" in query_lower: group = "CS-B"
                
                result_str = await get_timetable(day, group)
                context_parts.append(f"[MCP Tool: get_timetable({day})]:\n{result_str}")
                sources.append({"doc": f"Timetable API ({day})", "page": "Live Data"})

        else:
            # === RAG DOCUMENT PATH (Existing) ===
            try:
                # In Week 3, we still use the direct rag package for this endpoint 
                # (Week 4 LangGraph will use MCP Docs Server tools instead)
                results = search_documents(request.message, top_k=5)
                for doc in results:
                    source = doc.metadata.get("source", "Unknown")
                    page = doc.metadata.get("page", "?")
                    context_parts.append(f"[{source}, Page {page}]:\n{doc.page_content}")
                    sources.append({"doc": source, "page": page})
            except RuntimeError:
                 return {
                    "response": "The knowledge base has not been set up yet. Please ask an admin to run the ingestion pipeline.",
                    "sources": [],
                 }

        # Step 2: Build context
        context = "\n\n---\n\n".join(context_parts)

        # Step 3: Call LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
            HumanMessage(content=request.message),
        ]

        response = await llm.ainvoke(messages)

        return {
            "response": response.content,
            "sources": sources,
        }
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
