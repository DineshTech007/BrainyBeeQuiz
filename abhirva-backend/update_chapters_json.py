import PyPDF2
import json
import re
import os
import sys

def process_subject(subject_dir, subject_name):
    print(f"Processing subject: {subject_name} in {subject_dir}")
    if not os.path.exists(subject_dir):
        print(f"Directory {subject_dir} does not exist.")
        return

    pdfs = [f for f in os.listdir(subject_dir) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"No PDFs found in {subject_name}. Skipping to preserve existing JSON.")
        return
        
    book_chapters = {}
    
    for pdf in pdfs:
        path = os.path.join(subject_dir, pdf)
        print(f"  Reading {pdf}...")
        try:
            reader = PyPDF2.PdfReader(path)
            total_pages = len(reader.pages)
        except Exception as e:
            print(f"  Error reading {pdf}: {e}")
            continue
            
        chapters = []
        
        # Scan pages for "Chapter", "CHAPTER", "Unit", etc.
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if not text: continue
                text = text[:800] # look at first 800 chars
                
                # Look for "Chapter 1", "CHAPTER I", "Unit 1"
                match = re.search(r'(?i)(?:Chapter|CHAPTER|Unit)\s*([IVX\d]+)', text)
                if match:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    title = "Chapter " + match.group(1)
                    
                    for j, line in enumerate(lines):
                        if match.group(1) in line or "Chapter" in line or "CHAPTER" in line or "Unit" in line:
                            if j + 1 < len(lines):
                                title += ": " + lines[j+1][:60]
                            break
                    
                    # Avoid duplicates within 3 pages
                    if not chapters or (i + 1 - chapters[-1]['start_page'] > 3):
                        chapters.append({
                            "title": title,
                            "start_page": i + 1
                        })
            except Exception as e:
                pass
                
        # Now set end pages
        for i in range(len(chapters)):
            if i < len(chapters) - 1:
                chapters[i]['end_page'] = chapters[i+1]['start_page'] - 1
            else:
                chapters[i]['end_page'] = total_pages
                
        if not chapters:
            chapters = [{"title": "Entire Book", "start_page": 1, "end_page": min(total_pages, 20)}]
            
        book_chapters[pdf] = chapters

    # Map the subject name to normalized JSON filename
    subject_map = {
        "Mathematics": "maths",
        "Science": "science",
        "English": "english",
        "SST": "sst",
        "Hindi": "hindi",
        "Marathi": "marathi",
        "Computers": "computers"
    }
    normalized_subject = subject_map.get(subject_name, subject_name.lower())
    
    out_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"{normalized_subject}_chapters.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(book_chapters, f, indent=4)
        
    print(f"Generated {out_file} with {len(book_chapters)} books.")

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "10thBooks")
    if not os.path.exists(base_dir):
        print(f"Books directory not found at {base_dir}")
        return
        
    for item in os.listdir(base_dir):
        subject_dir = os.path.join(base_dir, item)
        if os.path.isdir(subject_dir):
            process_subject(subject_dir, item)

if __name__ == "__main__":
    main()
