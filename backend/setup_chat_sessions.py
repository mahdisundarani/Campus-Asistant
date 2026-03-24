import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DB_URL = os.getenv("SUPABASE_DB_URL")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

# The SQL to execute
sql_query = """
-- Create the chat_sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  messages jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Enable Row Level Security (Secure the table)
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- Allow users to manage their own sessions securely
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow users to select their own sessions') THEN
        CREATE POLICY "Allow users to select their own sessions" 
        ON public.chat_sessions FOR SELECT 
        USING (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow users to insert their own sessions') THEN
        CREATE POLICY "Allow users to insert their own sessions" 
        ON public.chat_sessions FOR INSERT 
        WITH CHECK (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow users to update their own sessions') THEN
        CREATE POLICY "Allow users to update their own sessions" 
        ON public.chat_sessions FOR UPDATE 
        USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow users to delete their own sessions') THEN
        CREATE POLICY "Allow users to delete their own sessions" 
        ON public.chat_sessions FOR DELETE 
        USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow public service access to chat_sessions') THEN
        CREATE POLICY "Allow public service access to chat_sessions" 
        ON public.chat_sessions 
        USING (true)
        WITH CHECK (true);
    END IF;
END
$$;
"""

print(f"Executing SQL setup for chat_sessions on {SUPABASE_URL}...")

try:
    if DB_URL:
        import psycopg2
        print(f"Connecting directly to database via Supabase DB URL...")
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql_query)
        cur.close()
        conn.close()
        print("Successfully executed SQL directly against PostgreSQL!")
    else:
        print("\nWARNING: SUPABASE_DB_URL is not set in .env")
        print("To run migrations via Python, we need the direct database connection string.")
        exit(1)
except Exception as e:
    print(f"\nFailed to execute SQL: {e}")
    if "No module named 'psycopg2'" in str(e):
         print("Missing 'psycopg2' package. You can install it with: pip install psycopg2-binary")
