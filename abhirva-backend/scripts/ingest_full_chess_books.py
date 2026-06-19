"""
Full Chess Book Ingestion Script
=================================
- Clears ALL existing Italian and Alapin variations from the DB first
- Re-ingests both books from scratch with 15-page chunks for better context
- Resumes from last saved progress if interrupted
- Uses flash model for speed + cost efficiency
"""

import os
import sys
import time
import json
import fitz
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chess_parser import process_and_save_chess_book, get_pdf_page_count
from config.supabase_client import supabase_db

import logging
logging.basicConfig(
    filename='ingest.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def log(msg):
    print(msg, flush=True)
    logging.info(msg)

def clear_opening(opening_name: str):
    """Deletes all existing rows for this opening name."""
    log(f"  Clearing existing '{opening_name}' variations from database...")
    try:
        res = supabase_db.table("chess_variations").delete().ilike("opening_name", opening_name).execute()
        deleted = len(res.data) if res.data else 0
        log(f"  Deleted {deleted} existing rows for {opening_name}.")
    except Exception as e:
        log(f"  WARNING: Could not clear {opening_name}: {e}")

def load_progress(progress_file):
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress_file, data):
    with open(progress_file, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    log("=" * 60)
    log("CHESS BOOK FULL INGESTION — START")
    log("=" * 60)

    books = [
        {
            "id": "italian_full",
            "path": r"F:\AbhirvaLearning\chess\opening\white\italian\winning-with-the-slow-but-venomous-italian-9789056916749_compress.pdf",
            "opening_name": "Italian",
            "start_page_offset": 14,   # skip intro/TOC
        },
        {
            "id": "alapin_full",
            "path": r"F:\AbhirvaLearning\chess\opening\white\alapin\vdoc.pub_the-complete-c3-sicilian.pdf",
            "opening_name": "Alapin",
            "start_page_offset": 20,   # skip intro/TOC
        },
    ]

    CHUNK_SIZE = 10  # pages per Gemini call — balanced for token limits
    SLEEP_BETWEEN_CHUNKS = 20  # seconds — respect rate limits

    progress_file = os.path.join(os.path.dirname(__file__), "ingest_progress.json")
    progress = load_progress(progress_file)

    for book in books:
        book_id = book["id"]
        opening_name = book["opening_name"]

        if not os.path.exists(book["path"]):
            log(f"ERROR: Book not found at {book['path']}")
            continue

        total_pages = get_pdf_page_count(book["path"])
        if total_pages == 0:
            log(f"ERROR: Could not open {book['path']}")
            continue

        log(f"\n{'='*50}")
        log(f"BOOK: {opening_name} ({total_pages} pages)")
        log(f"{'='*50}")

        # If this book hasn't been started yet (or we want a fresh start), clear DB first
        if book_id not in progress:
            clear_opening(opening_name)

        current_page = progress.get(book_id, book["start_page_offset"])

        total_saved = 0

        while current_page <= total_pages:
            end_page = min(current_page + CHUNK_SIZE - 1, total_pages)
            log(f"\n>>> {opening_name}: Pages {current_page}–{end_page} of {total_pages} <<<")

            try:
                saved = process_and_save_chess_book(
                    pdf_path=book["path"],
                    opening_name=opening_name,
                    start_page=current_page,
                    end_page=end_page
                )
                total_saved += saved
                log(f"  Saved {saved} new variations this chunk. Total so far: {total_saved}")
            except Exception as e:
                import traceback
                log(f"  ERROR in chunk {current_page}-{end_page}: {e}")
                log(traceback.format_exc())

            current_page += CHUNK_SIZE
            progress[book_id] = current_page
            save_progress(progress_file, progress)

            if current_page <= total_pages:
                log(f"  Sleeping {SLEEP_BETWEEN_CHUNKS}s before next chunk...")
                time.sleep(SLEEP_BETWEEN_CHUNKS)

        log(f"\n[DONE] {opening_name} complete! Total saved: {total_saved} variations")

    log("\n" + "="*60)
    log("FULL INGESTION COMPLETE!")
    log("="*60)

if __name__ == "__main__":
    main()
