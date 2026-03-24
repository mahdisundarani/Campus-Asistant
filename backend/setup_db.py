import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

# The SQL to execute
sql_query = """
-- 1. Create the user_roles table
CREATE TABLE IF NOT EXISTS public.user_roles (
  id uuid REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  role text NOT NULL CHECK (role IN ('student', 'admin'))
);

-- Enable Row Level Security (Secure the table)
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read roles (so our backend can fetch it)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow public read access to user_roles') THEN
        CREATE POLICY "Allow public read access to user_roles" 
        ON public.user_roles FOR SELECT 
        USING (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow service role full access to user_roles') THEN
        CREATE POLICY "Allow service role full access to user_roles" 
        ON public.user_roles 
        USING (true)
        WITH CHECK (true);
    END IF;
END
$$;

-- 2. Create the chat_logs table for telemetry
CREATE TABLE IF NOT EXISTS public.chat_logs (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  query text NOT NULL,
  intent text NOT NULL,
  latency_ms integer NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.chat_logs ENABLE ROW LEVEL SECURITY;

-- Allow public read access to logs (our backend will restrict this to admins later)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow public read access to chat_logs') THEN
        CREATE POLICY "Allow public read access to chat_logs" 
        ON public.chat_logs FOR SELECT 
        USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow public insert access to chat_logs') THEN
        CREATE POLICY "Allow public insert access to chat_logs" 
        ON public.chat_logs FOR INSERT 
        WITH CHECK (true);
    END IF;
END
$$;
"""

print(f"Executing SQL setup on {SUPABASE_URL}...")

# Supabase provides an internal REST endpoint for pg_meta to execute raw SQL, but it's typically heavily restricted.
# Let's try the PostgREST RPC endpoint if one exists, or notify the user.
try:
    # Most Supabase projects don't expose raw SQL execution over the public REST API for security reasons.
    # The standard way to do this via Python is the `postgres` driver (psycopg2) hitting the connection string.
    # We will try to get the DB URL
    db_url = os.getenv("SUPABASE_DB_URL")
    if db_url:
        import psycopg2
        print(f"Connecting directly to database via Supabase DB URL...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql_query)
        cur.close()
        conn.close()
        print("Successfully executed SQL directly against PostgreSQL!")
    else:
        print("\nWARNING: SUPABASE_DB_URL is not set in .env")
        print("To run migrations via Python, we need the direct database connection string.")
        print("Format: postgresql://postgres.[project-ref]:[db-password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        print("\nIf you only have SUPABASE_URL and the ANON/SERVICE keys, you MUST run the SQL in the Supabase Dashboard.")
except Exception as e:
    print(f"\nFailed to execute SQL: {e}")
    if "No module named 'psycopg2'" in str(e):
         print("Missing 'psycopg2' package. You can install it with: pip install psycopg2-binary")
