import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import subprocess
import json
import sys

# Start the Docs Server
print("Starting Docs Server...")
process = subprocess.Popen(
    [sys.executable, "mcp-servers/docs/server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send Initialize Request
init_req = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
}
print(f"Sending: {json.dumps(init_req)}")
process.stdin.write(json.dumps(init_req) + "\n")
process.stdin.flush()

# Read Initialize Response
init_res = process.stdout.readline()
print(f"Received: {init_res}")

# Send initialized Notification
initialized_notif = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
}
print(f"Sending: {json.dumps(initialized_notif)}")
process.stdin.write(json.dumps(initialized_notif) + "\n")
process.stdin.flush()

# Send Ping Request
ping_req = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "ping",
        "arguments": {}
    }
}
print(f"Sending: {json.dumps(ping_req)}")
process.stdin.write(json.dumps(ping_req) + "\n")
process.stdin.flush()

# Read Ping Response
ping_res = process.stdout.readline()
print(f"Received Ping: {ping_res}")

# Send Search Request
search_req = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "search_docs",
        "arguments": {
            "query": "attendance policy"
        }
    }
}
print(f"Sending: {json.dumps(search_req)}")
process.stdin.write(json.dumps(search_req) + "\n")
process.stdin.flush()

# Read Search Response
print("Waiting for Search Response...")
search_res = process.stdout.readline()
print(f"Received Search: {search_res}")

process.terminate()
