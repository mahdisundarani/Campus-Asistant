import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import asyncio
from graph import campus_graph

async def test():
    print("Sending 'hi' to pipeline...")
    result = await campus_graph.ainvoke({
        'query': 'hi',
        'history': [],
        'intent': '',
        'context': [],
        'sources': [],
        'response': ''
    })
    print("\nFINAL RESPONSE:")
    print(result['response'])

if __name__ == '__main__':
    asyncio.run(test())
