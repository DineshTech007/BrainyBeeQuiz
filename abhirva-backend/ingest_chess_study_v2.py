import os
import json
import time
from dotenv import load_dotenv

load_dotenv(r'f:\AbhirvaLearning\abhirva-backend\.env')

from google import genai
from google.genai import types
from config.supabase_client import supabase_db
from config.gemini_config import gemini_client

def ingest_chess_study_v2():
    chess_dir = r'f:\AbhirvaLearning\chess'
    
    print("Starting Deep V2 Trilingual Chess Study Ingestion...")
    
    files = [f for f in os.listdir(chess_dir) if f.lower().endswith('.pdf')]
    # Sort files by size so smaller books process first and UI populates faster!
    files.sort(key=lambda f: os.path.getsize(os.path.join(chess_dir, f)))
    
    for file in files:
        pdf_path = os.path.join(chess_dir, file)
        print(f"\nProcessing Book: {file} ({os.path.getsize(pdf_path) // 1024 // 1024} MB)")
        
        uploaded_file = None
        try:
            print(f"  Uploading to Gemini...")
            uploaded_file = gemini_client.files.upload(file=pdf_path)
            
            print(f"  Waiting for Gemini to process the document...")
            while True:
                file_info = gemini_client.files.get(name=uploaded_file.name)
                if file_info.state == "ACTIVE":
                    break
                elif file_info.state == "FAILED":
                    raise Exception("Document processing failed on Google servers.")
                time.sleep(5)
            
            prompt = """
            You are a Grandmaster Chess Tutor. I have attached a comprehensive chess PDF book.
            Extract exactly 15 key foundational chess concepts or tactical motifs from this book.
            
            For each concept, provide:
            1. The name of the concept in English, Hindi, and Marathi.
            2. An array of EXACTLY 4 steps demonstrating a sequence of moves that illustrate this concept.
            
            For each step in the sequence, provide:
            - fen: A valid standard FEN string showing the exact board position after the move.
            - notation: The algebraic notation of the move played (e.g., "e4", "Nf3").
            - explanation_en: A brief English explanation of what this move accomplishes for the concept.
            - explanation_hi: The Hindi translation of the explanation.
            - explanation_mr: The Marathi translation of the explanation.
            """
            
            response_schema = {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "concept_name_en": {"type": "STRING"},
                        "concept_name_hi": {"type": "STRING"},
                        "concept_name_mr": {"type": "STRING"},
                        "steps": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "fen": {"type": "STRING"},
                                    "notation": {"type": "STRING"},
                                    "explanation_en": {"type": "STRING"},
                                    "explanation_hi": {"type": "STRING"},
                                    "explanation_mr": {"type": "STRING"}
                                },
                                "required": ["fen", "notation", "explanation_en", "explanation_hi", "explanation_mr"]
                            }
                        }
                    },
                    "required": ["concept_name_en", "concept_name_hi", "concept_name_mr", "steps"]
                }
            }

            generation_config = types.GenerateContentConfig(
                system_instruction="You are a Grandmaster Chess Tutor. Return ONLY valid JSON.",
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=response_schema
            )
            
            print(f"  Extracting 15 concepts with 4-step interactive move sequences...")
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
                    "steps": c["steps"]
                })
                
            if payloads:
                supabase_db.table("chess_study_concepts_v2").insert(payloads).execute()
                print(f"  [SUCCESS] Saved {len(payloads)} deep step-by-step concepts to DB!")
                
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
    ingest_chess_study_v2()
