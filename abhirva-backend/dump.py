import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from config.supabase_client import supabase_db

resp = supabase_db.table("chess_variations").select("*").ilike("opening_name", "Alapin").execute()
with open("test_output.json", "w") as f:
    json.dump(resp.data, f)
