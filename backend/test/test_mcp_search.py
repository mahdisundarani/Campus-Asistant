import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import asyncio
import mcp_client

async def run():
    print("Testing search_docs...")
    results = await mcp_client.search_docs("attendance policy")
    print("Results:")
    print(results)

if __name__ == "__main__":
    asyncio.run(run())
