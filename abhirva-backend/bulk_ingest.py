import os
import re
import time
from services.quiz_service import generate_and_save_past_paper

def bulk_ingest_pdfs():
    base_dir = r'f:\AbhirvaLearning\10thBooks'
    count = 0
    success = 0
    errors = 0
    
    print("Starting Bulk Ingestion of Past Papers...")
    
    print("Starting Bulk Ingestion of Past Papers...")
    
    # Better to use os.walk to find files but explicitly ignore backups
    for root, dirs, files in os.walk(base_dir):
        # Ignore backup directories
        if 'backup' in [d.lower() for d in root.split(os.sep)]:
            continue
            
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue
                
            # Extract subject from the parent directory
            rel_path = os.path.relpath(root, base_dir)
            if rel_path == '.':
                continue
            subject = rel_path.split(os.sep)[0]
            
            # Extract year from filename
            match = re.search(r'(20\d{2})', file)
            if not match:
                print(f"Skipping {file} - No year found in filename.")
                continue
                
            year = match.group(1)
            pdf_path = os.path.join(root, file)
            count += 1
            
            print(f"[{count}] Processing {subject} | {year} | {file}")
            
            try:
                # Call the modified quiz_service logic directly
                # We request 5 questions per PDF to speed it up and save some tokens, adjust as needed.
                # Actually, standard is 10. Let's stick to 5 for bulk ingest to ensure we don't hit max tokens too easily per minute.
                result = generate_and_save_past_paper(
                    board="CBSE",
                    grade="10th Class",
                    subject=subject,
                    year=year,
                    num_questions=5, 
                    exact_pdf_path=pdf_path
                )
                
                if result.get("success") is False:
                    print(f"  [ERROR] {result.get('error')}")
                    errors += 1
                else:
                    print(f"  [SUCCESS] Saved to Database!")
                    success += 1
            except Exception as e:
                print(f"  [CRITICAL ERROR] {e}")
                errors += 1
                
            print("  Sleeping for 10 seconds to respect rate limits...\n")
            time.sleep(10)
            
    print(f"\n======================================")
    print(f"Bulk Ingestion Complete!")
    print(f"Total PDFs Found: {count}")
    print(f"Successful Ingests: {success}")
    print(f"Failed Ingests: {errors}")
    print(f"======================================")

if __name__ == "__main__":
    bulk_ingest_pdfs()
