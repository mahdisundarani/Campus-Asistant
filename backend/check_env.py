"""
check_env.py — Verify all environment variables and API connections.

Run:  python check_env.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def check_env_var(name):
    val = os.getenv(name)
    if val:
        masked = val[:8] + "..." + val[-4:] if len(val) > 16 else val
        print(f"  {PASS} {name} = {masked}")
        return val
    else:
        print(f"  {FAIL} {name} — NOT SET")
        return None


def check_supabase(url, key):
    print(f"\n{'='*50}")
    print("2. Supabase Connection")
    print(f"{'='*50}")
    if not url or not key:
        print(f"  {FAIL} Skipped — missing credentials")
        return

    try:
        resp = requests.get(
            f"{url}/auth/v1/settings",
            headers={"apikey": key},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"  {PASS} Supabase auth endpoint reachable (HTTP {resp.status_code})")
        else:
            print(f"  {FAIL} Supabase returned HTTP {resp.status_code}")
            print(f"       Response: {resp.text[:200]}")
    except requests.ConnectionError:
        print(f"  {FAIL} Cannot connect to Supabase at {url}")
    except Exception as e:
        print(f"  {FAIL} Error: {e}")


def check_openrouter(api_key, api_base):
    print(f"\n{'='*50}")
    print("3. LLM / OpenRouter Connection")
    print(f"{'='*50}")
    if not api_key or not api_base:
        print(f"  {FAIL} Skipped — missing credentials")
        return

    # Check key validity by listing models
    try:
        resp = requests.get(
            f"{api_base}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            model_count = len(data.get("data", []))
            print(f"  {PASS} API key is valid — {model_count} models available")
        elif resp.status_code == 401:
            print(f"  {FAIL} API key is INVALID or EXPIRED (HTTP 401)")
            print(f"       Response: {resp.text[:200]}")
            return
        else:
            print(f"  {WARN} Unexpected response (HTTP {resp.status_code})")
            print(f"       Response: {resp.text[:200]}")
    except requests.ConnectionError:
        print(f"  {FAIL} Cannot connect to {api_base}")
        return
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
        return

    # Check credits / auth with a minimal chat completion
    model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    print(f"\n  Testing chat completion with model: {model}")
    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say hi"}],
                "max_tokens": 5,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            print(f"  {PASS} Chat completion works! Reply: \"{reply}\"")
        elif resp.status_code == 401:
            error = resp.json().get("error", {})
            print(f"  {FAIL} Authentication failed (HTTP 401)")
            print(f"       Message: {error.get('message', resp.text[:200])}")
        elif resp.status_code == 402:
            print(f"  {FAIL} No credits remaining (HTTP 402)")
            print(f"       Add credits at: https://openrouter.ai/credits")
        elif resp.status_code == 429:
            print(f"  {WARN} Rate limited (HTTP 429) — key works but slow down")
        else:
            print(f"  {FAIL} Unexpected response (HTTP {resp.status_code})")
            print(f"       Response: {resp.text[:300]}")
    except Exception as e:
        print(f"  {FAIL} Error: {e}")


def check_huggingface(api_key):
    print(f"\n{'='*50}")
    print("4. HuggingFace API")
    print(f"{'='*50}")
    if not api_key:
        print(f"  {FAIL} Skipped — missing credentials")
        return

    try:
        resp = requests.get(
            "https://huggingface.co/api/whoami-v2",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            user = resp.json().get("name", "unknown")
            print(f"  {PASS} HuggingFace API key valid — user: {user}")
        elif resp.status_code == 401:
            print(f"  {FAIL} HuggingFace API key is INVALID (HTTP 401)")
        else:
            print(f"  {WARN} Unexpected response (HTTP {resp.status_code})")
    except Exception as e:
        print(f"  {FAIL} Error: {e}")


def check_qdrant_collection():
    print(f"\n{'='*50}")
    print("5. Qdrant Vector Store")
    print(f"{'='*50}")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "campus_assistant")
    chunks_path = os.path.join(os.path.dirname(__file__), "vectorstore", "chunks.pkl")

    if qdrant_url:
        print(f"  {PASS} QDRANT_URL = {qdrant_url[:40]}...")
    else:
        print(f"  {FAIL} QDRANT_URL — NOT SET")

    if qdrant_key:
        print(f"  {PASS} QDRANT_API_KEY is set")
    else:
        print(f"  {WARN} QDRANT_API_KEY not set (ok for local Qdrant)")

    print(f"  Collection name: '{collection}'")

    if os.path.exists(chunks_path):
        size_mb = os.path.getsize(chunks_path) / (1024 * 1024)
        print(f"  {PASS} chunks.pkl (BM25) exists ({size_mb:.2f} MB)")
    else:
        print(f"  {FAIL} chunks.pkl NOT FOUND — run 'python ingest.py'")


if __name__ == "__main__":
    print(f"{'='*50}")
    print("1. Environment Variables")
    print(f"{'='*50}")

    supabase_url = check_env_var("SUPABASE_URL")
    supabase_key = check_env_var("SUPABASE_SERVICE_ROLE_KEY")
    openai_key = check_env_var("OPENAI_API_KEY")
    openai_base = check_env_var("OPENAI_API_BASE")
    hf_key = check_env_var("HUGGINGFACE_API_KEY")
    llm_model = check_env_var("LLM_MODEL")
    if not llm_model:
        print(f"  {WARN} LLM_MODEL not set — will default to 'openai/gpt-4o-mini'")

    check_supabase(supabase_url, supabase_key)
    check_openrouter(openai_key, openai_base)
    check_huggingface(hf_key)
    check_qdrant_collection()

    print(f"\n{'='*50}")
    print("Done!")
    print(f"{'='*50}")
