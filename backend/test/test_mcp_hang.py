import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import asyncio
import mcp_client
import sys

async def run():
    print("Testing search_docs...")
    try:
        # Wrap the call in a timeout so we don't wait forever
        results = await asyncio.wait_for(
            mcp_client.search_docs("attendance policy"), 
            timeout=10.0
        )
        print("Results received successfully!")
        print(results)
    except asyncio.TimeoutError:
        print("ERROR: Timeout reached waiting for search_docs!")
        
        # Test a simple fast tool to see if the server itself is hung
        print("Trying get_doc_chunk (fast tool)...")
        try:
            res2 = await asyncio.wait_for(
                mcp_client.get_doc_chunk("Academic_Policy_Handbook.pdf", 2),
                timeout=5.0
            )
            print("get_doc_chunk succeeded! The server is responsive, but search_docs hangs.")
        except asyncio.TimeoutError:
            print("get_doc_chunk also hung! The entire server process is locked up.")

if __name__ == "__main__":
    # Force unbuffered output for debugging
    import os
    os.environ["PYTHONUNBUFFERED"] = "1"
    asyncio.run(run())
