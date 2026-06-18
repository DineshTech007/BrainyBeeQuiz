import os
import re
import time
from services.quiz_service import generate_and_save_past_paper

def ingest_marathi():
    subject_dir = r'f:\AbhirvaLearning\10thBooks\Marathi'
    count = 0
    
    print("Ingesting specifically Marathi PDFs...")
    
    for file in os.listdir(subject_dir):
        if not file.lower().endswith('.pdf'):
            continue
            
        # Extract year from filename
        match = re.search(r'(20\d{2})', file)
        if not match:
            continue
            
        year = match.group(1)
        pdf_path = os.path.join(subject_dir, file)
        count += 1
        
        print(f"[{count}] Processing Marathi | {year} | {file}")
        
        try:
            result = generate_and_save_past_paper(
                board="CBSE",
                grade="10th Class",
                subject="Marathi",
                year=year,
                num_questions=5, 
                exact_pdf_path=pdf_path
            )
            if result.get("success") is False:
                print(f"  [ERROR] {result.get('error')}")
            else:
                print(f"  [SUCCESS] Saved to Database!")
        except Exception as e:
            print(f"  [CRITICAL ERROR] {e}")
            
        time.sleep(10)
        
    print(f"Completed Marathi Specific Ingestion! Processed {count} files.")

if __name__ == "__main__":
    ingest_marathi()
