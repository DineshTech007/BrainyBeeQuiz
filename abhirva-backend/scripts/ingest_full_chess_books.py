import os
import sys
import time
import json
import fitz
from dotenv import load_dotenv

load_dotenv(override=True)

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chess_parser import process_and_save_chess_book

import logging

logging.basicConfig(
    filename='ingest.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_log(msg):
    print(msg, flush=True)
    logging.info(msg)

def get_total_pages(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return len(doc)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return 0

def load_progress(progress_file):
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_progress(progress_file, data):
    with open(progress_file, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    try:
        print_log("=== Chess Book FULL Ingestion ===")
        
        books = [
            {
                "id": "alapin_full",
                "path": r"F:\AbhirvaLearning\chess\opening\white\alapin\vdoc.pub_the-complete-c3-sicilian.pdf",
                "opening_name": "Alapin",
                "start_page_offset": 15, # skip intro/TOC
            },
            {
                "id": "italian_full",
                "path": r"F:\AbhirvaLearning\chess\opening\white\italian\winning-with-the-slow-but-venomous-italian-9789056916749_compress.pdf",
                "opening_name": "Italian",
                "start_page_offset": 15,
            }
        ]
        
        progress_file = os.path.join(os.path.dirname(__file__), "ingest_progress.json")
        progress = load_progress(progress_file)
        
        CHUNK_SIZE = 6 # process 6 pages at a time to stay within token limits and maintain context
        
        for book in books:
            book_id = book["id"]
            if not os.path.exists(book["path"]):
                print_log(f"Error: Could not find book at {book['path']}")
                continue
                
            total_pages = get_total_pages(book["path"])
            if total_pages == 0:
                continue
                
            print_log(f"\n--- Processing {book['opening_name']} ({total_pages} total pages) ---")
            
            current_page = progress.get(book_id, book["start_page_offset"])
            
            while current_page <= total_pages:
                end_page = min(current_page + CHUNK_SIZE - 1, total_pages)
                print_log(f"\n>>> Processing {book['opening_name']}: Pages {current_page} to {end_page} ...")
                
                success = process_and_save_chess_book(
                    pdf_path=book["path"],
                    opening_name=book["opening_name"],
                    start_page=current_page,
                    end_page=end_page
                )
                
                if not success:
                    print_log(f"Skipped or no variations found in pages {current_page}-{end_page}.")
                else:
                    print_log(f"Successfully processed pages {current_page}-{end_page}.")
                
                # Save progress so we can resume
                current_page += CHUNK_SIZE
                progress[book_id] = current_page
                save_progress(progress_file, progress)
                
                # Rate limiting pause
                print_log("Sleeping for 15 seconds to respect rate limits...")
                time.sleep(15)
                
        print_log("\n✅ Full Ingestion Complete!")

    except Exception as e:
        import traceback
        with open("global_crash.txt", "w") as f:
            f.write(f"CRASH: {e}\n{traceback.format_exc()}")
        print_log(f"CRASH: {e}")

if __name__ == "__main__":
    main()
