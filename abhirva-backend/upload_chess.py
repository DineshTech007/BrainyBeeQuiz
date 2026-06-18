import json
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.supabase_client import supabase_db

def main():
    json_path = r"F:\AbhirvaLearning\abhirva-frontend\chess\opening\white\italian\italian_syllabus.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    opening_name = "italian"  # The frontend uses lowercase usually or the URL parameter
    
    # First, let's delete existing italian variations so we don't duplicate
    try:
        supabase_db.table("chess_variations").delete().eq("opening_name", opening_name).execute()
        print("Deleted existing Italian variations.")
    except Exception as e:
        print(f"Error deleting existing variations (maybe none exist): {e}")

    variations = data.get("variations", [])
    
    for var in variations:
        record = {
            "opening_name": opening_name,
            "variation_name_en": var["name_en"],
            "variation_name_mr": var["name_mr"],
            "variation_name_hi": var["name_hi"],
            "moves": var["moves"]
        }
        
        try:
            supabase_db.table("chess_variations").insert(record).execute()
            print(f"Successfully inserted {var['name_en']}")
        except Exception as e:
            print(f"Error inserting {var['name_en']}: {e}")

if __name__ == '__main__':
    main()
