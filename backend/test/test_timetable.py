import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import asyncio
from graph import campus_graph

async def test():
    result = await campus_graph.ainvoke({
        'query': 'what lectures do i have on monday?',
        'history': [],
        'intent': '',
        'context': [],
        'sources': [],
        'response': ''
    })
    print(result['response'])

if __name__ == '__main__':
    asyncio.run(test())
