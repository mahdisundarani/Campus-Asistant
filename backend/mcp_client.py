"""
mcp_client.py — Backend wrapper for communicating with local FastMCP servers.

Uses FastMCP's Client to spawn the servers as subprocesses and call their tools.
"""

import os
from fastmcp import Client

# Define paths to the server scripts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_SERVER_SCRIPT = os.path.join(BASE_DIR, "..", "mcp-servers", "docs", "server.py")
TIMETABLE_SERVER_SCRIPT = os.path.join(BASE_DIR, "..", "mcp-servers", "timetable", "server.py")

# Ensure we use the exact same Python executable as the backend
# This ensures it runs inside the .venv with the fastmcp dependency
PYTHON_EXEC = sys.executable if 'sys' in globals() else os.environ.get("VIRTUAL_ENV", "") + "/Scripts/python"
if not os.path.exists(PYTHON_EXEC):
    import sys
    PYTHON_EXEC = sys.executable

import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Define paths to the server scripts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_SERVER_SCRIPT = os.path.join(BASE_DIR, "..", "mcp-servers", "docs", "server.py")
TIMETABLE_SERVER_SCRIPT = os.path.join(BASE_DIR, "..", "mcp-servers", "timetable", "server.py")

PYTHON_EXEC = sys.executable

# ==================== CONNECTION MANAGERS ====================

@asynccontextmanager
async def _get_docs_session() -> AsyncGenerator[ClientSession, None]:
    """Provide a session connected to the Docs MCP Server."""
    server_params = StdioServerParameters(command=PYTHON_EXEC, args=[DOCS_SERVER_SCRIPT])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

@asynccontextmanager
async def _get_timetable_session() -> AsyncGenerator[ClientSession, None]:
    """Provide a session connected to the Timetable MCP Server."""
    server_params = StdioServerParameters(command=PYTHON_EXEC, args=[TIMETABLE_SERVER_SCRIPT])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

# ==================== DOCS TOOLS ====================

async def search_docs(query: str, top_k: int = 5) -> list[dict]:
    """Call the Docs MCP server to search FAISS."""
    async with _get_docs_session() as session:
        result = await session.call_tool("search_docs", arguments={"query": query, "top_k": top_k})
        return result.content[0].text if result.content else "[]"

async def get_doc_chunk(doc_name: str, page: int) -> dict:
    """Call the Docs MCP server to fetch a specific chunk."""
    async with _get_docs_session() as session:
        result = await session.call_tool("get_chunk", arguments={"doc_name": doc_name, "page": page})
        return result.content[0].text if result.content else "{}"

# ==================== TIMETABLE TOOLS ====================

async def get_timetable(day: str, student_group: str = None) -> list[dict]:
    """Call the Timetable MCP server to get a day's schedule."""
    args = {"day": day}
    if student_group:
        args["student_group"] = student_group
        
    async with _get_timetable_session() as session:
        result = await session.call_tool("get_timetable", arguments=args)
        return result.content[0].text if result.content else "[]"

async def get_deadlines(course_id: str = None) -> list[dict]:
    """Call the Timetable MCP server to get upcoming deadlines."""
    args = {}
    if course_id:
        args["course_id"] = course_id
        
    async with _get_timetable_session() as session:
        result = await session.call_tool("get_deadlines", arguments=args)
        return result.content[0].text if result.content else "[]"

# ==================== TEST/VERIFY ====================

async def _test_connections():
    """Verify that both clients can connect and list tools."""
    print("Testing Docs MCP Server connection...")
    async with _get_docs_session() as session:
        tools = await session.list_tools()
        print(f"  -> Connected! Found tools: {[t.name for t in tools.tools]}")
        
    print("\nTesting Timetable MCP Server connection...")
    async with _get_timetable_session() as session:
        tools = await session.list_tools()
        print(f"  -> Connected! Found tools: {[t.name for t in tools.tools]}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(_test_connections())
