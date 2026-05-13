from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("WARNING: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing. Storage will not work.")
    supabase = None
else:
    supabase = create_client(url, key)


def upload_file(bucket: str, path: str, file_bytes: bytes):
    if not supabase: return None
    return supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={"upsert": "true"}
    )

def download_file(bucket: str, path: str):
    if not supabase: return None
    return supabase.storage.from_(bucket).download(path)

def list_files(bucket: str):
    if not supabase: return []
    return supabase.storage.from_(bucket).list()

def delete_file(bucket: str, path: str):
    if not supabase: return None
    return supabase.storage.from_(bucket).remove([path])
