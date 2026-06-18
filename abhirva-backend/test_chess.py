import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from config.supabase_client import supabase_db

try:
    resp = supabase_db.table("chess_variations").select("*").ilike("opening_name", "Alapin").execute()
    print("Success:", json.dumps(resp.data, indent=2))
except Exception as e:
    print("Error:", e)
