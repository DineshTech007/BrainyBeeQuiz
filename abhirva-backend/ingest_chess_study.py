import os
import json
import time
from dotenv import load_dotenv

load_dotenv(r'f:\AbhirvaLearning\abhirva-backend\.env')

from google import genai
from google.genai import types
from config.supabase_client import supabase_db
from config.gemini_config import gemini_client

def ingest_chess_study():
    chess_dir = r'f:\AbhirvaLearning\chess'
    
    print("Starting Trilingual Chess Study Ingestion with genai SDK...")
    
    for file in os.listdir(chess_dir):
        if not file.lower().endswith('.pdf'):
            continue
            
        pdf_path = os.path.join(chess_dir, file)
        print(f"\nProcessing Book: {file}")
        
        uploaded_file = None
        try:
            print(f"  Uploading to Gemini...")
            uploaded_file = gemini_client.files.upload(file=pdf_path)
            
            prompt = """
            You are a Grandmaster Chess Tutor. I have attached a chess PDF book.
            Extract exactly 5 key chess concepts from this book. For each concept, provide:
            1. The name of the concept in English, Hindi, and Marathi.
            2. A clear, beginner-friendly explanation of the concept in English, Hindi, and Marathi.
            3. A standard FEN string representing a board position that perfectly illustrates this concept.
            """
            
            response_schema = {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "concept_name_en": {"type": "STRING"},
                        "concept_name_hi": {"type": "STRING"},
                        "concept_name_mr": {"type": "STRING"},
                        "explanation_en": {"type": "STRING"},
                        "explanation_hi": {"type": "STRING"},
                        "explanation_mr": {"type": "STRING"},
                        "fen": {"type": "STRING"}
                    },
                    "required": ["concept_name_en", "concept_name_hi", "concept_name_mr", "explanation_en", "explanation_hi", "explanation_mr", "fen"]
                }
            }

            generation_config = types.GenerateContentConfig(
                system_instruction="You are a Grandmaster Chess Tutor. Return ONLY valid JSON.",
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=response_schema
            )
            
            print(f"  Extracting 5 concepts in 3 languages...")
            ai_response = gemini_client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[uploaded_file, prompt],
                config=generation_config
            )
            
            concepts = json.loads(ai_response.text)
            
            payloads = []
            for c in concepts:
                payloads.append({
                    "book_source": file,
                    "concept_name_en": c["concept_name_en"],
                    "concept_name_hi": c["concept_name_hi"],
                    "concept_name_mr": c["concept_name_mr"],
                    "explanation_en": c["explanation_en"],
                    "explanation_hi": c["explanation_hi"],
                    "explanation_mr": c["explanation_mr"],
                    "fen": c["fen"]
                })
                
            if payloads:
                supabase_db.table("chess_study_concepts").insert(payloads).execute()
                print(f"  [SUCCESS] Saved {len(payloads)} trilingual concepts to DB!")
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            
        finally:
            if uploaded_file:
                try:
                    gemini_client.files.delete(name=uploaded_file.name)
                except:
                    pass
                    
        print("  Sleeping for 15 seconds to respect rate limits...")
        time.sleep(15)

if __name__ == "__main__":
    ingest_chess_study()
