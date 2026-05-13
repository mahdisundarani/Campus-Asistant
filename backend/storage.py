from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def upload_file(bucket: str, path: str, file_bytes: bytes):
    return supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={"upsert": "true"}
    )

def download_file(bucket: str, path: str):
    return supabase.storage.from_(bucket).download(path)

def list_files(bucket: str):
    return supabase.storage.from_(bucket).list()

def delete_file(bucket: str, path: str):
    return supabase.storage.from_(bucket).remove([path])