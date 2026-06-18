import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from config.supabase_client import supabase_db

try:
    resp = supabase_db.table("test_attempts").select("*").limit(1).execute()
    print("Success test_attempts:", resp.data)
except Exception as e:
    print("Error test_attempts:", e)
