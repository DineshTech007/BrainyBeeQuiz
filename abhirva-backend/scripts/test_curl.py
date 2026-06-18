import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.chess_parser import extract_text_from_pdf

def main():
    path = r"F:\AbhirvaLearning\chess\opening\white\alapin\vdoc.pub_the-complete-c3-sicilian.pdf"
    text = extract_text_from_pdf(path, 15, 20)
    
    prompt = f"""
    You are an expert chess annotator and grandmaster.
    I am providing you a chunk of text from a chess book about the Alapin.
    
    Your task:
    1. Identify EVERY distinct chess variation discussed in this text. Do not miss any.
    2. For each variation, provide a clear, descriptive title in English (e.g., "Alapin: Main Line with 2...Nf6").
    3. CRITICAL: For each variation, you MUST provide the FULL sequence of moves starting from the very beginning of the chess game (Move 1). If the text is discussing a sub-variation at move 10, you must fill in the first 9 moves of the Alapin to reach that position so that a chess engine can validate it from the standard starting board.
    4. For each move, provide the standard algebraic notation (SAN) and a brief, highly educational coaching explanation in English.

    Text:
    {text[:100000]}

    Return ONLY a valid JSON array of variations. Each variation must follow this structure exactly:
    [
        {{
            "variation_name_en": "Alapin: Main Line with 2...Nf6",
            "moves": [
                {{
                    "notation": "e4",
                    "coach_text_en": "White plays the King's Pawn to control the center."
                }}
            ]
        }}
    ]
    Make sure the sequence of moves is perfectly valid from the initial starting board. If a move is invalid, my parser will crash.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }
    
    with open("payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print("Payload written to payload.json")

if __name__ == "__main__":
    main()
