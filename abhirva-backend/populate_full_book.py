import os
import sys
import time
import json
import argparse
import fitz  # PyMuPDF
from dotenv import load_dotenv

load_dotenv(override=True)

# Add backend directory to path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chess_parser import process_and_save_chess_book

PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "populate_progress.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "populate_book.log")

def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def load_progress() -> int:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_processed_page", 14) # Start page default is 15 (last processed 14)
        except Exception as e:
            log(f"Warning: Could not parse progress file, starting fresh: {e}")
    return 14

def save_progress(last_page: int):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_processed_page": last_page, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=4)
    except Exception as e:
        log(f"Error saving progress: {e}")

def main():
    parser = argparse.ArgumentParser(description="Orchestrator to populate complete chess book variations into Supabase")
    parser.add_argument("--start", type=int, default=None, help="Start page of the PDF (1-based)")
    parser.add_argument("--end", type=int, default=None, help="End page of the PDF (1-based)")
    parser.add_argument("--chunk-size", type=int, default=10, help="Number of pages to process at once")
    parser.add_argument("--sleep", type=int, default=20, help="Seconds to sleep between requests to avoid rate limits")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from last processed page")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Do not resume, start from the specified start page")
    
    args = parser.parse_args()

    log("=== Starting Chess Book Population Orchestration ===")
    
    # Resolve PDF path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(backend_dir, "..", "chess", "opening", "white", "italian", "winning-with-the-slow-but-venomous-italian-9789056916749_compress.pdf"))
    
    if not os.path.exists(pdf_path):
        log(f"CRITICAL ERROR: PDF not found at path: {pdf_path}")
        sys.exit(1)
        
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        log(f"Successfully opened PDF. Total pages: {total_pages}")
    except Exception as e:
        log(f"CRITICAL ERROR: Failed to open PDF: {e}")
        sys.exit(1)
        
    # Determine page bounds
    start_page = args.start
    if start_page is None:
        if args.resume:
            last_processed = load_progress()
            start_page = last_processed + 1
            log(f"Resuming progress from page {start_page}...")
        else:
            start_page = 15  # Default start page skipping intro/TOC
            log(f"Starting fresh from page {start_page}...")
            
    end_page = args.end if args.end is not None else total_pages
    chunk_size = args.chunk_size
    sleep_duration = args.sleep
    
    log(f"Configuration: Range={start_page}-{end_page}, ChunkSize={chunk_size}, Sleep={sleep_duration}s")
    
    current_page = start_page
    while current_page <= end_page:
        chunk_end = min(current_page + chunk_size - 1, end_page)
        log(f"\n--- Processing Chunk: Pages {current_page} to {chunk_end} ---")
        
        success = False
        retry_count = 0
        max_retries = 2
        
        while not success and retry_count <= max_retries:
            try:
                success = process_and_save_chess_book(
                    pdf_path=pdf_path,
                    opening_name="italian",
                    start_page=current_page,
                    end_page=chunk_end
                )
                if success:
                    log(f"Success: Pages {current_page}-{chunk_end} processed.")
                else:
                    log(f"Warning: No variations extracted/saved for pages {current_page}-{chunk_end}.")
                    # We count no variations as a success to move forward, as some page ranges are purely text/diagrams
                    success = True 
            except Exception as e:
                retry_count += 1
                log(f"Error processing pages {current_page}-{chunk_end} (Attempt {retry_count}/{max_retries + 1}): {e}")
                if retry_count <= max_retries:
                    log(f"Sleeping for {sleep_duration * 2} seconds before retrying...")
                    time.sleep(sleep_duration * 2)
                else:
                    log(f"ERROR: Max retries exceeded. Skipping page range {current_page}-{chunk_end} to continue.")
                    
        # Update progress and save state
        save_progress(chunk_end)
        current_page = chunk_end + 1
        
        if current_page <= end_page:
            log(f"Respecting rate limit: Sleeping for {sleep_duration} seconds...")
            time.sleep(sleep_duration)

    log("\n=== Orchestration Job Finished ===")
    log("All pages have been processed or skipped.")

if __name__ == "__main__":
    main()
