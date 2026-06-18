import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client.
    Uses the SERVICE_ROLE_KEY to bypass RLS for secure backend inserts.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not found in environment variables.")
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Global singleton client
supabase_db = get_supabase_client()
