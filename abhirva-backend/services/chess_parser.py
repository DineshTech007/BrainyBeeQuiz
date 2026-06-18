import json
import re
import fitz  # PyMuPDF
import chess
import os
import sys

# Make sure we can import from config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.supabase_client import supabase_db

DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"

def extract_text_from_pdf(pdf_path: str, start_page: int, end_page: int) -> str:
    """Extract text from a range of pages in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        # fitz uses 0-indexed pages
        start = max(0, start_page - 1)
        end = min(len(doc), end_page)
        for i in range(start, end):
            text += doc[i].get_text() + "\n"
        # Sanitize text to prevent silent crashes in C extensions/networking libraries
        text = text.replace('\x00', ' ')
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def generate_2d_board(board: chess.Board):
    """Converts a python-chess board to a 2D array suitable for react-chessboard."""
    # python-chess fen: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    fen = board.board_fen()
    rows = fen.split('/')
    board_2d = []
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                # Empty squares
                for _ in range(int(char)):
                    board_row.append("")
            else:
                # Piece (e.g., 'r', 'N', 'p')
                # Wait, react-chessboard expects 'wP', 'bN', etc. or standard FEN.
                # Actually, our ChessTutor.jsx expects `wP`, `bP`, etc.
                # Let's check ChessTutor.jsx: it builds FEN from this array:
                # "if (piece === "") empty++ else fen += piece"
                # So if it's 'p', it adds 'p' (which is black pawn in standard FEN).
                # So we can just use standard FEN characters!
                board_row.append(char)
        board_2d.append(board_row)
    return board_2d

def translate_to_marathi_and_hindi(text: str) -> dict:
    """Translates the text to Marathi and Hindi using Gemini."""
    if not text or text.strip() == "":
        return {"mr": "", "hi": ""}
        
    prompt = f"""
    Translate the following chess explanation into Marathi and Hindi. 
    Maintain the context of chess (e.g., pieces, squares, tactics).
    
    Text to translate:
    {text}
    
    Return ONLY a valid JSON object:
    {{
        "mr": "marathi translation here",
        "hi": "hindi translation here"
    }}
    """
    
    try:
        import os
        import json
        import subprocess
        import tempfile
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"mr": "Error: No API Key", "hi": "Error: No API Key"}
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_GEMINI_MODEL}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.json') as tmp_in:
            json.dump(payload, tmp_in)
            tmp_in_name = tmp_in.name
            
        tmp_out_name = tmp_in_name + ".out"
        
        curl_cmd = [
            "curl.exe", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", f"@{tmp_in_name}",
            "-o", tmp_out_name,
            url
        ]
        
        subprocess.run(curl_cmd, check=False)
        
        if not os.path.exists(tmp_out_name):
            return {"mr": "Translation failed", "hi": "Translation failed"}
            
        with open(tmp_out_name, "r", encoding="utf-8") as f:
            res_body = f.read()
            
        try:
            os.remove(tmp_in_name)
            os.remove(tmp_out_name)
        except:
            pass
            
        response_json = json.loads(res_body)
        if "error" in response_json:
            return {"mr": "Translation failed", "hi": "Translation failed"}
            
        content_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(content_text.strip())
    except Exception as e:
        print(f"Translation error: {e}")
        return {"mr": "Translation failed", "hi": "Translation failed"}

def parse_chess_variations_from_text(text: str, opening_name: str):
    """
    Prompts Gemini to extract chess variations from the raw text.
    It returns a JSON list of variations.
    """

    prompt = f"""
    You are an expert chess annotator and grandmaster.
    I am providing you a chunk of text from a chess book about the {opening_name}.
    
    Your task:
    1. Identify EVERY distinct chess variation discussed in this text. Do not miss any.
    2. For each variation, provide a clear, descriptive title in English (e.g., "Alapin: Main Line with 2...Nf6").
    3. CRITICAL: For each variation, provide a detailed `description_en` that explains the overarching motive, strategy, and narrative behind this variation.
    4. CRITICAL: For each variation, you MUST provide the FULL sequence of moves starting from the very beginning of the chess game (Move 1). If the text is discussing a sub-variation at move 10, you must fill in the first 9 moves of the {opening_name} to reach that position so that a chess engine can validate it from the standard starting board.
    5. For each move, provide the standard algebraic notation (SAN) and a brief, highly educational coaching explanation in English.

    Text:
    {text[:100000]}

    Return ONLY a valid JSON array of variations. Each variation must follow this structure exactly:
    [
        {{
            "variation_name_en": "Alapin: Main Line with 2...Nf6",
            "description_en": "This variation focuses on rapid development and challenging the center immediately, sacrificing pawn structure for dynamic piece play.",
            "moves": [
                {{
                    "notation": "e4",
                    "coach_text_en": "White plays the King's Pawn to control the center."
                }},
                {{
                    "notation": "c5",
                    "coach_text_en": "Black responds with the Sicilian Defense."
                }},
                {{
                    "notation": "c3",
                    "coach_text_en": "White plays the Alapin variation."
                }}
            ]
        }}
    ]
    Make sure the sequence of moves is perfectly valid from the initial starting board. If a move is invalid, my parser will crash.
    """
    
    try:
        import os
        import json
        import subprocess
        import tempfile
        
        with open("debug_parser.txt", "a") as f:
            f.write("DEBUG: Calling generate_content via curl subprocess...\n")
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_GEMINI_MODEL}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        
        # Write payload to a temp file to avoid command line length limits and encoding issues
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.json') as tmp_in:
            json.dump(payload, tmp_in)
            tmp_in_name = tmp_in.name
            
        tmp_out_name = tmp_in_name + ".out"
        
        # Run curl
        curl_cmd = [
            "curl.exe", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", f"@{tmp_in_name}",
            "-o", tmp_out_name,
            url
        ]
        
        subprocess.run(curl_cmd, check=False)
        
        # Read the result
        if not os.path.exists(tmp_out_name):
            with open("debug_parser.txt", "a") as f:
                f.write("DEBUG: curl did not produce output file.\n")
            return []
            
        with open(tmp_out_name, "r", encoding="utf-8") as f:
            res_body = f.read()
            
        # Clean up temp files
        try:
            os.remove(tmp_in_name)
            os.remove(tmp_out_name)
        except:
            pass
            
        try:
            response_json = json.loads(res_body)
        except Exception as e:
            with open("debug_parser.txt", "a") as f:
                f.write(f"DEBUG: curl returned invalid JSON: {res_body[:200]}\n")
            return []
            
        if "error" in response_json:
            with open("debug_parser.txt", "a") as f:
                f.write(f"DEBUG: API Error: {response_json['error']}\n")
            return []
            
        with open("debug_parser.txt", "a") as f:
            f.write("DEBUG: curl REST API returned successfully.\n")
            
        content_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(content_text.strip())
            
    except BaseException as e:
        import traceback
        with open("parser_error.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"Extraction error: {e}")
        return []

def process_and_save_chess_book(pdf_path: str, opening_name: str, start_page: int, end_page: int):
    """Orchestrates the entire extraction, translation, fen generation, and db insertion."""
    print(f"Reading {pdf_path} from page {start_page} to {end_page}...")
    raw_text = extract_text_from_pdf(pdf_path, start_page, end_page)
    if not raw_text:
        print("No text extracted.")
        return False
        
    print("Extracting variations with Gemini...")
    variations = parse_chess_variations_from_text(raw_text, opening_name)
    
    if not variations:
        print("No variations found.")
        return False
        
    print(f"Found {len(variations)} variations. Processing moves...")
    
    for var in variations:
        var_name_en = var.get("variation_name_en", "Unknown Variation")
        desc_en = var.get("description_en", "")
        print(f"Processing variation: {var_name_en}")
        
        # Translate variation name
        var_name_trans = translate_to_marathi_and_hindi(var_name_en)
        var_name_mr = var_name_trans.get("mr", var_name_en)
        var_name_hi = var_name_trans.get("hi", var_name_en)
        
        # Translate description
        desc_trans = translate_to_marathi_and_hindi(desc_en)
        desc_mr = desc_trans.get("mr", desc_en)
        desc_hi = desc_trans.get("hi", desc_en)
        
        board = chess.Board()
        processed_moves = []
        
        # Always insert the start position first
        processed_moves.append({
            "step": 0,
            "notation": "start",
            "board": generate_2d_board(board),
            "fen": board.fen(),
            "highlight_squares": [],
            "coach_text_en": "Initial position for this variation.",
            "coach_text_mr": "या व्हेरियेशनची सुरुवातीची पोझिशन.",
            "coach_text_hi": "इस वेरियेशन की प्रारंभिक स्थिति।"
        })
        
        for step, move_data in enumerate(var.get("moves", []), start=1):
            notation = move_data.get("notation")
            coach_en = move_data.get("coach_text_en", "")
            
            # Play move on board to get state
            try:
                move = board.push_san(notation)
                highlight = [chess.square_name(move.from_square), chess.square_name(move.to_square)]
            except ValueError as e:
                print(f"Invalid move {notation} in variation {var_name_en}: {e}")
                # We stop processing this variation if a move is invalid
                break
                
            # Translate coach text
            coach_trans = translate_to_marathi_and_hindi(coach_en)
            
            processed_moves.append({
                "step": step,
                "notation": notation,
                "board": generate_2d_board(board),
                "fen": board.fen(),
                "highlight_squares": highlight,
                "coach_text_en": coach_en,
                "coach_text_mr": coach_trans.get("mr", ""),
                "coach_text_hi": coach_trans.get("hi", "")
            })
            
        if len(processed_moves) <= 1:
            continue
            
        # Save to Supabase
        db_record = {
            "opening_name": opening_name,
            "variation_name_en": var_name_en,
            "variation_name_mr": var_name_mr,
            "variation_name_hi": var_name_hi,
            "description_en": desc_en,
            "description_mr": desc_mr,
            "description_hi": desc_hi,
            "moves": processed_moves
        }
        
        try:
            supabase_db.table("chess_variations").insert(db_record).execute()
            print(f"Saved {var_name_en} to database!")
        except Exception as e:
            print(f"Error saving to database: {e}")
            
    print("Done processing book chunk.")
    return True
