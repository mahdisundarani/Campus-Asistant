# Model Context Protocol (MCP) in Campus Assistant

This document explains the **Model Context Protocol (MCP)**, its architecture, and its implementation within the Campus Assistant project.

---

## 1. What is MCP?

The **Model Context Protocol (MCP)** is an open standard developed to allow AI models (LLMs) to seamlessly connect to external data sources and tools. Traditionally, connecting an AI to a database or a file system required writing custom, ad-hoc API integrations. MCP replaces this with a **universal interface**.

Think of MCP as **"USB-C for AI"**. Just as USB-C allows you to connect any peripheral to any computer using a standard plug, MCP allows any AI agent to connect to any data source using a standard protocol.

---

## 2. Why is MCP? (The Motivation)

Before MCP, developers faced several challenges:
- **Integration Fatigue**: Every new tool (Jira, GitHub, Slack, local DB) needed a custom wrapper.
- **Context Management**: Passing too much data (logs, docs) into the model's context window was expensive and messy.
- **Security**: Hard to define clear boundaries for what an AI can and cannot access.

**MCP solves this by:**
- **Standardizing Tool Use**: Servers describe their "tools" (functions) and "resources" (data) in a format any model can understand.
- **On-Demand Context**: The AI pulls only the relevant bits of information (e.g., just the Monday timetable) instead of the entire database.
- **Interoperability**: An MCP server built for this project could, in theory, be plugged into Claude Desktop, VS Code, or any other MCP-compliant client.

---

## 3. Why did we use MCP in this project?

In Campus Assistant, we used MCP for three primary reasons:

1.  **Decoupling Data from Logic**: Our AI agents (LangGraph) don't need to know *how* to read a CSV or query FAISS. They just know they have a "tool" called `get_timetable`. The MCP server handles the file parsing and logic.
2.  **Modularity**: We have three separate servers (`Docs`, `Timetable`, `Notices`). If we want to change the Timetable from a CSV to a SQL database, we only update the MCP server; the AI agent's code remains untouched.
3.  **Local Execution (Security & Speed)**: By using the **stdio transport**, the MCP servers run as local subprocesses. This means campus data never leaves the local environment for processing—it's fast, private, and efficient.

---

## 4. How did we implement MCP?

Our implementation follows a **Client-Server Architecture**:

### The Servers (`mcp-servers/`)
- **FastMCP Framework**: We used the `fastmcp` Python library to quickly define tools.
- **Transport**: We use **stdio**. The backend "speaks" to the server via standard input/output.
- **Servers**:
    - **Docs MCP**: Connects to the FAISS vector store for semantic search.
    - **Timetable MCP**: Parses local CSVs and resolves group-specific schedules.
    - **Notices MCP**: Exposes campus announcements from JSON.

### The Client (`backend/mcp_client.py`)
The FastAPI backend acts as the **MCP Client**. When a user asks a question:
1.  The **LangGraph Agent** decides it needs data.
2.  The **MCP Client** spawns the relevant MCP server (docs, timetable, or notices).
3.  It performs a **Handshake** (JSON-RPC) to discover available tools.
4.  It **Calls the Tool** with the model's parameters.
5.  It receives the data and passes it back to the AI for the final response.

---

## 5. Use Cases of MCP in the Industry

MCP is rapidly becoming a standard in the AI industry:

- **Enterprise Knowledge Search**: Large companies use MCP to connect LLMs to internal wikis (Notion/Confluence) and ticket systems (Jira) WITHOUT giving the LLM full access to the cloud.
- **AI-Powered IDEs**: Tools like **Cursor** and **Windsurf** use MCP to let the AI "see" your terminal, search your codebase through `grep`, and even run your tests.
- **SaaS Connectivity**: Zapier-like automation where an AI can "Check Slack for the meeting time, find the Zoom link in Google Calendar, and join the meeting."
- **Customer Support**: AI agents that can query a live SQL database to check order status or update shipping addresses via standardized MCP tool calls.

---

> [!TIP]
> To see the technical details of our MCP servers, visit the [mcp-servers/README.md](file:///c:/Users/mahdi/OneDrive/Desktop/Campus-Assistant/mcp-servers/README.md).
