import json
import time
import os
import sys

# Add parent dir to path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import campus_graph

import asyncio

# Maximum time (seconds) allowed per query before skipping
QUERY_TIMEOUT = 60

async def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    results_path = os.path.join(os.path.dirname(__file__), "results.json")
    
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    print(f"Starting Evaluation on {len(dataset)} queries...")
    print(f"Per-query timeout: {QUERY_TIMEOUT}s\n")
    
    results = []
    correct_intents = 0
    total_latency = 0
    succeeded = 0
    timed_out = 0
    errored = 0
    
    for item in dataset:
        qid = item["id"]
        query = item["query"]
        expected_intent = item["expected_intent"]
        keywords = item["expected_keywords"]
        
        print(f"[{qid}] Testing: '{query}'")
        
        start_time = time.time()
        
        # Invoke the graph asynchronously
        state = {
            "query": query,
            "history": [],
            "intent": "",
            "context": [],
            "sources": [],
            "response": ""
        }
        
        try:
            final_state = await asyncio.wait_for(
                campus_graph.ainvoke(state),
                timeout=QUERY_TIMEOUT
            )
            
            actual_intent = final_state.get("intent", "unknown")
            response_text = final_state.get("response", "").lower()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Checks
            intent_match = actual_intent == expected_intent
            if intent_match:
                correct_intents += 1
                
            keyword_matches = sum(1 for kw in keywords if kw.lower() in response_text)
            match_rate = keyword_matches / len(keywords) if len(keywords) > 0 else 1.0
            
            total_latency += latency_ms
            succeeded += 1
            
            print(f"  -> Intent: {actual_intent} (Expected: {expected_intent}) {'✅' if intent_match else '❌'}")
            print(f"  -> Latency: {latency_ms}ms | Keywords Found: {keyword_matches}/{len(keywords)}\n")
            
            results.append({
                "id": qid,
                "query": query,
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "intent_correct": intent_match,
                "latency_ms": latency_ms,
                "keyword_match_rate": round(match_rate, 2),
                "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
            })

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            timed_out += 1
            print(f"  -> TIMEOUT after {latency_ms}ms (limit: {QUERY_TIMEOUT}s) ⏰\n")
            results.append({
                "id": qid,
                "query": query,
                "expected_intent": expected_intent,
                "actual_intent": "TIMEOUT",
                "intent_correct": False,
                "latency_ms": latency_ms,
                "keyword_match_rate": 0,
                "response_preview": "TIMED OUT"
            })
            
        except Exception as e:
            errored += 1
            print(f"  -> ERROR: {str(e)}\n")
            results.append({
                "id": qid,
                "query": query,
                "expected_intent": expected_intent,
                "error": str(e)
            })
            
    # Summary
    completed = succeeded + timed_out + errored
    metrics = {
        "total_queries": len(dataset),
        "succeeded": succeeded,
        "timed_out": timed_out,
        "errored": errored,
        "intent_accuracy": round((correct_intents / max(succeeded, 1)) * 100, 2),
        "mean_latency_ms": round(total_latency / max(succeeded, 1), 2)
    }
    
    print("="*50)
    print("           EVALUATION SUMMARY")
    print("="*50)
    print(f"  Total Queries       : {metrics['total_queries']}")
    print(f"  Succeeded           : {metrics['succeeded']}")
    print(f"  Timed Out           : {metrics['timed_out']}")
    print(f"  Errored             : {metrics['errored']}")
    print(f"  Intent Accuracy     : {metrics['intent_accuracy']}%")
    print(f"  Avg Latency (ok)    : {metrics['mean_latency_ms']} ms")
    print("="*50)
    
    with open(results_path, "w") as f:
        json.dump({"metrics": metrics, "detailed_results": results}, f, indent=2)
        
    print(f"\nDetailed results written to {results_path}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
