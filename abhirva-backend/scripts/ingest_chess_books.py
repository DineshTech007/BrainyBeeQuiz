import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chess_parser import process_and_save_chess_book
from config.supabase_client import supabase_db

def init_db():
    print("Ensuring the chess_variations table exists is something that needs to be done manually in Supabase SQL editor.")
    print("If you haven't run the `chess_schema.sql` file yet, please do so.")

def main():
    print("=== Chess Book Ingestion POC ===")
    
    books = [
        {
            "path": r"F:\AbhirvaLearning\chess\opening\white\alapin\vdoc.pub_the-complete-c3-sicilian.pdf",
            "opening_name": "Alapin",
            "start_page": 20, # Skip title/index pages, go to first main line chapter
            "end_page": 22
        },
        {
            "path": r"F:\AbhirvaLearning\chess\opening\white\italian\winning-with-the-slow-but-venomous-italian-9789056916749_compress.pdf",
            "opening_name": "Italian",
            "start_page": 20, # Skip title/index pages
            "end_page": 22
        }
    ]
    
    for book in books:
        if not os.path.exists(book["path"]):
            print(f"Error: Could not find book at {book['path']}")
            continue
            
        print(f"\n--- Processing {book['opening_name']} ---")
        process_and_save_chess_book(
            pdf_path=book["path"],
            opening_name=book["opening_name"],
            start_page=book["start_page"],
            end_page=book["end_page"]
        )

if __name__ == "__main__":
    init_db()
    main()
