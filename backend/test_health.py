import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    try:
        print(f"Testing {BASE_URL}/...")
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("[OK] Health check passed:", response.json())
        else:
            print(f"[FAIL] Health check failed with status {response.status_code}: {response.text}")
            sys.exit(1)
            
        print(f"\nTesting {BASE_URL}/chat (without auth)...")
        
        chat_payload = {"message": "Hello"}
        response = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        if response.status_code == 401 or response.status_code == 403:
            print(f"[OK] Auth check passed (got expected {response.status_code})")
        else:
            print(f"[WARN] Unexpected status check for /chat: {response.status_code}")
            if response.status_code == 200:
                print("Response:", response.json())
            
            if response.status_code == 500:
                 print(f"[FAIL] Backend crashed: {response.text}")
                 sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("[FAIL] Could not connect to backend. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_health()
