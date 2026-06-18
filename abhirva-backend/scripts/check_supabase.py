import os
import sys
from dotenv import load_dotenv

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.supabase_client import supabase_db

def main():
    load_dotenv(override=True)
    
    try:
        response = supabase_db.table("chess_variations").select("variation_name_en, variation_name_mr, variation_name_hi").execute()
        data = response.data
        with open("db_content.txt", "w", encoding="utf-8") as f:
            f.write(f"Total variations in DB: {len(data)}\n")
            for i, row in enumerate(data[:15]):
                f.write(f"[{i+1}] EN: {row.get('variation_name_en')} | MR: {row.get('variation_name_mr')} | HI: {row.get('variation_name_hi')}\n")
    except Exception as e:
        print(f"Error reading from DB: {e}")

if __name__ == "__main__":
    main()
