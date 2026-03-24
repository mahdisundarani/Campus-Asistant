import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from agents.supervisor import supervisor_node

async def main():
    query = "mention the dates mentioned in academic calendar"
    print(f"Querying Supervisor for: {query}")
    state = {"query": query, "history": []}
    result = await supervisor_node(state)
    print(f"Resulting state updates: {result}")

if __name__ == "__main__":
    asyncio.run(main())
