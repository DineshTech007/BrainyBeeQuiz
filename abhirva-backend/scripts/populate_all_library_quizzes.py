import os
import sys
import argparse
import time
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Ensure backend root is in python path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_ROOT)

load_dotenv(os.path.join(BACKEND_ROOT, ".env"), override=True)

from config.supabase_client import supabase_db
from services.quiz_service import get_book_quiz_from_db, generate_and_save_book_quiz

def main():
    parser = argparse.ArgumentParser(description="Populate all grade books and generate 10-question quizzes covering complete story.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of books processed for quiz generation.")
    parser.add_argument("--skip-upload", action="store_true", help="Skip uploading books to Supabase storage.")
    parser.add_argument("--force", action="store_true", default=True, help="Force regeneration of quizzes even if they already exist.")
    parser.add_argument("--no-force", action="store_false", dest="force", help="Do not force regeneration of quizzes.")
    parser.add_argument("--sleep-seconds", type=int, default=12, help="Seconds to sleep between Gemini requests to avoid rate limits.")
    args = parser.parse_args()

    print("==================================================")
    print("All Grades Book Library Quiz Population Script")
    print(f"Configuration: Limit={args.limit}, SkipUpload={args.skip_upload}, Force={args.force}, Sleep={args.sleep_seconds}s")
    print("==================================================")

    # 1. Locate local BookLibrary books
    library_base_dir = os.path.normpath(os.path.join(BACKEND_ROOT, "..", "BookLibrary"))
    if not os.path.exists(library_base_dir):
        print(f"Error: BookLibrary directory not found at: {library_base_dir}")
        sys.exit(1)

    grades = ["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
    languages = ["English", "Marathi", "Hindi"]
    
    books_to_process = []  # List of tuples: (local_filepath, rel_path, grade, language, book_filename)

    for grade in grades:
        grade_dir = os.path.join(library_base_dir, grade)
        if not os.path.exists(grade_dir):
            continue
            
        # Check if there are pdf files directly in this directory (e.g. Kindergarten)
        direct_pdfs = [f for f in os.listdir(grade_dir) if f.endswith(".pdf")]
        if direct_pdfs:
            for file in direct_pdfs:
                filepath = os.path.join(grade_dir, file)
                rel_path = f"{grade}/English/{file}"
                books_to_process.append((filepath, rel_path, grade, "English", file))
                
        # Also check subdirectories for languages
        for lang in languages:
            lang_dir = os.path.join(grade_dir, lang)
            if not os.path.exists(lang_dir):
                continue
            for file in os.listdir(lang_dir):
                if file.endswith(".pdf"):
                    filepath = os.path.join(lang_dir, file)
                    rel_path = f"{grade}/{lang}/{file}"
                    books_to_process.append((filepath, rel_path, grade, lang, file))

    print(f"Found {len(books_to_process)} local PDF books in total.")

    
    # Print breakdown
    breakdown = {}
    for filepath, rel_path, grade, lang, file in books_to_process:
        breakdown[grade] = breakdown.get(grade, 0) + 1
    print("Breakdown by grade:")
    for g, count in breakdown.items():
        print(f"  {g}: {count} books")

    # 2. Upload books to Supabase Storage if not skip_upload
    if not args.skip_upload:
        print("\n--- Phase 1: Uploading books to Supabase Storage ---")
        # Group books by cloud folder to fetch bucket listings efficiently
        by_folder = {}
        for filepath, rel_path, grade, lang, file in books_to_process:
            folder = f"{grade}/{lang}"
            by_folder.setdefault(folder, []).append((filepath, rel_path, file))
            
        for folder, files in by_folder.items():
            try:
                res = supabase_db.storage.from_("library_books").list(folder)
                existing_names = {f["name"] for f in res if isinstance(f, dict) and "name" in f}
            except Exception as e:
                print(f"  Warning: Could not list folder {folder}: {e}")
                existing_names = set()
                
            for filepath, rel_path, file in files:
                if file in existing_names:
                    continue
                    
                print(f"  Uploading {rel_path}...")
                try:
                    with open(filepath, 'rb') as f:
                        supabase_db.storage.from_("library_books").upload(
                            path=rel_path,
                            file=f,
                            file_options={"content-type": "application/pdf"}
                        )
                    print("    Success.")
                except Exception as e:
                    print(f"    Failed to upload {rel_path}: {e}")

    # 3. Generate Quizzes using Gemini
    print("\n--- Phase 2: Generating and Populating Quizzes ---")
    quiz_count = 0
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, (filepath, rel_path, grade, lang, file) in enumerate(books_to_process):
        if args.limit is not None and quiz_count >= args.limit:
            print(f"\nLimit of {args.limit} books reached. Stopping quiz generation.")
            break

        print(f"\n[{idx+1}/{len(books_to_process)}] Processing quiz for: {grade} | {lang} | {file}")

        # Check if quiz already exists and has questions
        if not args.force:
            try:
                existing_quiz = get_book_quiz_from_db(grade, lang, file)
                if existing_quiz and existing_quiz.get("success") is not False and "error" not in existing_quiz:
                    print(f"  Quiz already exists in DB. Skipping.")
                    skipped_count += 1
                    continue
            except Exception as e:
                print(f"  Error checking database for existing quiz: {e}")

        # Extract text from ALL pages using fitz
        context = ""
        try:
            doc = fitz.open(filepath)
            num_pages = len(doc)
            for p in range(num_pages):
                context += doc[p].get_text() + "\n"
            doc.close()
        except Exception as e:
            print(f"  Error reading local PDF file {filepath}: {e}")
            failed_count += 1
            continue

        print(f"  Extracted {len(context)} chars of context (from all {num_pages} pages). Requesting quiz generation...")
        
        # Increment processed count as we are making a Gemini call
        quiz_count += 1

        # Retry logic
        max_retries = 3
        attempt = 0
        success = False
        
        while attempt < max_retries and not success:
            attempt += 1
            if attempt > 1:
                print(f"  Retrying generation (Attempt {attempt}/{max_retries})...")
                time.sleep(args.sleep_seconds * 2) # Sleep longer on retry
                
            try:
                result = generate_and_save_book_quiz(
                    grade=grade,
                    book_name=file,
                    context=context,
                    language=lang,
                    num_questions=10
                )

                if result and result.get("success") is not False and "error" not in result:
                    print(f"  [SUCCESS] Quiz created/updated. ID: {result.get('quiz_id') or result.get('id')}")
                    success_count += 1
                    success = True
                else:
                    error_msg = result.get("error") if result else "Unknown error"
                    print(f"  [FAILED] Attempt {attempt} failed: {error_msg}")
                    if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                        print("    Rate limit/quota issue detected. Sleeping for 45 seconds...")
                        time.sleep(45)
            except Exception as e:
                print(f"  [ERROR] Attempt {attempt} crashed: {e}")
                
        if not success:
            failed_count += 1

        # Sleep to respect Gemini API rate limits
        if idx < len(books_to_process) - 1 and (args.limit is None or quiz_count < args.limit):
            print(f"  Sleeping for {args.sleep_seconds} seconds...")
            time.sleep(args.sleep_seconds)

    print("\n==================================================")
    print("All Grades Population Summary")
    print(f"Total Books Checked: {len(books_to_process)}")
    print(f"Quizzes skipped (already existed): {skipped_count}")
    print(f"Quizzes generated successfully: {success_count}")
    print(f"Quizzes failed: {failed_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
