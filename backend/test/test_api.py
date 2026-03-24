import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from main import app, get_current_user

# Mock the Supabase authentication so we don't need a real JWT
def mock_get_current_user():
    return {"id": "test-user-123", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

print("Sending request to /chat...")
response = client.post("/chat", json={
    "message": "hi",
    "history": [{"role": "user", "content": "hi"}]
})

print(f"STATUS: {response.status_code}")
try:
    print(f"JSON: {response.json()}")
except Exception as e:
    print(f"TEXT: {response.text}")
