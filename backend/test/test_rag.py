import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import asyncio
from agents.state import GraphState
from agents.rag_agent import rag_node

async def main():
    state: GraphState = {
        'query': 'what are hostel rules', 
        'history': [], 
        'intent': 'rag', 
        'context': [], 
        'sources': [], 
        'response': ''
    }
    result = await rag_node(state)
    print("\nCONTEXT CHUNKS:")
    for c in result.get("context", []):
        print(f"- [{c.get('source')} p.{c.get('page')}] {c.get('content')[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
