import json
import re
import fitz  # PyMuPDF
import chess
import os
import sys
import time

# Make sure we can import from config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.supabase_client import supabase_db
from google import genai
from google.genai import types

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"

# Initialise Gemini client once (reads GEMINI_API_KEY from env)
_gemini_client = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

def extract_text_from_pdf(pdf_path: str, start_page: int, end_page: int) -> str:
    """Extract text from a range of pages in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        start = max(0, start_page - 1)
        end = min(len(doc), end_page)
        for i in range(start, end):
            text += doc[i].get_text() + "\n"
        text = text.replace('\x00', ' ')
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def get_pdf_page_count(pdf_path: str) -> int:
    try:
        doc = fitz.open(pdf_path)
        return len(doc)
    except:
        return 0

def generate_2d_board(board: chess.Board):
    """Converts a python-chess board to a 2D array."""
    fen = board.board_fen()
    rows = fen.split('/')
    board_2d = []
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                for _ in range(int(char)):
                    board_row.append("")
            else:
                board_row.append(char)
        board_2d.append(board_row)
    return board_2d

def call_gemini_api(prompt: str, temperature: float = 0.2) -> str:
    """Calls the Gemini API via the official SDK and returns the response text."""
    try:
        client = get_gemini_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8192,
        )
        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=prompt,
            config=config
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            print(f"Gemini quota error: {err_str[:200]}")
        else:
            print(f"Gemini API error: {err_str[:300]}")
        return ""

def batch_translate(texts: list) -> list:
    """
    Translates a list of English texts to Marathi AND Hindi in a single API call.
    Returns a list of dicts: [{"mr": "...", "hi": "..."}, ...]
    """
    if not texts:
        return []

    numbered_texts = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])

    prompt = f"""You are a professional chess translator.
Translate each of the following numbered English chess explanations into Marathi (mr) and Hindi (hi).
Keep all chess piece names, square names (e4, d5, Nf3, etc.), and technical terms in English as they are.
Only translate the explanatory prose.

{numbered_texts}

Return a JSON array where each element corresponds to one numbered item:
[
  {{"mr": "Marathi translation 1", "hi": "Hindi translation 1"}},
  {{"mr": "Marathi translation 2", "hi": "Hindi translation 2"}}
]
Return ONLY the JSON array, no other text."""

    result = call_gemini_api(prompt, temperature=0.1)
    if not result:
        return [{"mr": t, "hi": t} for t in texts]

    try:
        # Strip markdown code fences if present
        cleaned = result.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        parsed = json.loads(cleaned)
        if isinstance(parsed, list) and len(parsed) == len(texts):
            return parsed
        else:
            print(f"Batch translate length mismatch: got {len(parsed) if isinstance(parsed, list) else type(parsed)}, expected {len(texts)}")
            return [{"mr": t, "hi": t} for t in texts]
    except Exception as e:
        print(f"Batch translate parse error: {e}")
        return [{"mr": t, "hi": t} for t in texts]

def parse_chess_variations_from_text(text: str, opening_name: str) -> list:
    """
    Prompts Gemini to extract chess variations from a book chunk.
    Returns a JSON list of variation dicts.
    """
    prompt = f"""You are a grandmaster-level chess annotator and professional book editor.
I am providing raw text extracted from a chess book about the {opening_name}.

Your task is to identify EVERY distinct chess variation or example game discussed in this text and convert it into structured JSON.

RULES:
1. Each variation must have a unique, descriptive name (e.g., "Italian: Slow Main Line 9.a4", "Alapin 2...Nc6: 7.Bc4 Main Line").
2. `description_en` must explain the key strategic ideas, plans, and motives in 2-4 sentences.
3. Moves MUST be in Standard Algebraic Notation (SAN) that python-chess can validate (e.g., "Nf3", "O-O", "exd5", not "N-KB3" or "1.e4").
4. CRITICAL: Every variation's move list MUST start from move 1 (e4 or d4 etc). Do not start from a mid-game position. Fill in the opening moves to reach the position being discussed.
5. `coach_text_en` for each move should be a 1-2 sentence explanation of WHY that move is played.
6. Do NOT include duplicate variations. If the same line appears twice, include it only once with the most complete version.
7. Validate that moves are legal chess moves before including them.

Text from the book:
---
{text[:40000]}
---

Return ONLY a valid JSON array:
[
  {{
    "variation_name_en": "Italian: Slow Main Line with 9.a4",
    "description_en": "White methodically expands on the queenside...",
    "moves": [
      {{"notation": "e4", "coach_text_en": "White seizes central space."}},
      {{"notation": "e5", "coach_text_en": "Black mirrors White's central claim."}},
      {{"notation": "Nf3", "coach_text_en": "White develops and attacks the e5 pawn."}},
      {{"notation": "Nc6", "coach_text_en": "Black defends the e5 pawn with a natural developing move."}}
    ]
  }}
]

Include ALL variations you find in the text. Quality and completeness are critical."""

    result = call_gemini_api(prompt, temperature=0.15)
    if not result:
        return []

    try:
        # Strip markdown code fences if present
        cleaned = result.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        # Try direct parse first
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        # JSON was truncated — try to salvage complete variation objects
        # Find all complete {...} objects inside the array
        salvaged = []
        depth = 0
        obj_start = None
        for i, ch in enumerate(cleaned):
            if ch == '{':
                if depth == 0:
                    obj_start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and obj_start is not None:
                    obj_str = cleaned[obj_start:i+1]
                    try:
                        obj = json.loads(obj_str)
                        if isinstance(obj, dict) and 'variation_name_en' in obj:
                            salvaged.append(obj)
                    except:
                        pass
                    obj_start = None

        if salvaged:
            print(f"  Salvaged {len(salvaged)} complete variations from truncated JSON.")
            return salvaged

        print(f"Variation parse error: could not parse JSON | Preview: {result[:300]}")
        return []
    except Exception as e:
        print(f"Variation parse error: {e} | Preview: {result[:300]}")
        return []

def get_existing_variation_names(opening_name: str) -> set:
    """Fetch all existing variation names for this opening to avoid duplicates."""
    try:
        res = supabase_db.table("chess_variations").select("variation_name_en").ilike("opening_name", opening_name).execute()
        return {r["variation_name_en"] for r in (res.data or [])}
    except:
        return set()

def process_and_save_chess_book(pdf_path: str, opening_name: str, start_page: int, end_page: int) -> int:
    """
    Orchestrates extraction, translation, FEN generation, and DB insertion.
    Returns the number of variations successfully saved.
    """
    print(f"Reading {pdf_path} pages {start_page}-{end_page}...")
    raw_text = extract_text_from_pdf(pdf_path, start_page, end_page)
    if not raw_text.strip():
        print("No text extracted from this page range.")
        return 0

    print(f"Extracted {len(raw_text)} chars. Calling Gemini to extract variations...")
    variations = parse_chess_variations_from_text(raw_text, opening_name)

    if not variations:
        print("No variations found in this chunk.")
        return 0

    print(f"Found {len(variations)} variations. Checking for duplicates...")
    existing_names = get_existing_variation_names(opening_name)

    # Filter out duplicates
    new_variations = []
    for var in variations:
        name = var.get("variation_name_en", "")
        if name and name not in existing_names:
            new_variations.append(var)
            existing_names.add(name)  # prevent duplicates within this batch too
        else:
            print(f"  Skipping duplicate: {name}")

    if not new_variations:
        print("All variations already exist in DB. Skipping.")
        return 0

    print(f"Processing {len(new_variations)} new variations...")

    # --- BATCH TRANSLATE variation names and descriptions ---
    var_names_en = [v.get("variation_name_en", "") for v in new_variations]
    desc_texts_en = [v.get("description_en", "") for v in new_variations]

    print(f"  Batch translating {len(var_names_en)} variation names...")
    name_translations = batch_translate(var_names_en)
    time.sleep(2)

    print(f"  Batch translating {len(desc_texts_en)} descriptions...")
    desc_translations = batch_translate(desc_texts_en)
    time.sleep(2)

    saved_count = 0

    for i, var in enumerate(new_variations):
        var_name_en = var.get("variation_name_en", f"Variation {i+1}")
        desc_en = var.get("description_en", "")
        raw_moves = var.get("moves", [])

        var_name_mr = name_translations[i].get("mr", var_name_en) if i < len(name_translations) else var_name_en
        var_name_hi = name_translations[i].get("hi", var_name_en) if i < len(name_translations) else var_name_en
        desc_mr = desc_translations[i].get("mr", desc_en) if i < len(desc_translations) else desc_en
        desc_hi = desc_translations[i].get("hi", desc_en) if i < len(desc_translations) else desc_en

        print(f"  Processing moves for: {var_name_en}")

        # --- BATCH TRANSLATE move coach texts ---
        coach_texts_en = [m.get("coach_text_en", "") for m in raw_moves if m.get("coach_text_en")]
        all_coach_en_full = [m.get("coach_text_en", "") for m in raw_moves]

        print(f"    Batch translating {len(coach_texts_en)} coach texts...")
        coach_translations = batch_translate(all_coach_en_full)
        time.sleep(2)

        # --- PLAY MOVES ON BOARD ---
        board = chess.Board()
        processed_moves = []

        # Always insert the start position first
        processed_moves.append({
            "step": 0,
            "notation": "start",
            "board": generate_2d_board(board),
            "fen": board.fen(),
            "highlight_squares": [],
            "coach_text_en": f"Starting position for {var_name_en}.",
            "coach_text_mr": coach_translations[0].get("mr", "") if coach_translations else "",
            "coach_text_hi": coach_translations[0].get("hi", "") if coach_translations else "",
            "tips_en": "",
            "tips_mr": "",
            "tips_hi": "",
        })

        valid_moves = True
        for step, move_data in enumerate(raw_moves, start=1):
            notation = move_data.get("notation", "").strip()
            if not notation:
                continue

            # Clean up notation artifacts
            notation = re.sub(r'^\d+\.+\s*', '', notation).strip()
            notation = notation.split()[0]  # take only first token if AI added extras

            coach_en = all_coach_en_full[step-1] if step-1 < len(all_coach_en_full) else ""
            trans = coach_translations[step-1] if step-1 < len(coach_translations) else {"mr": "", "hi": ""}

            try:
                move = board.push_san(notation)
                highlight = [chess.square_name(move.from_square), chess.square_name(move.to_square)]
            except ValueError as e:
                print(f"    Invalid move '{notation}' at step {step} in '{var_name_en}': {e}. Stopping this variation here.")
                valid_moves = False
                break

            processed_moves.append({
                "step": step,
                "notation": notation,
                "board": generate_2d_board(board),
                "fen": board.fen(),
                "highlight_squares": highlight,
                "coach_text_en": coach_en,
                "coach_text_mr": trans.get("mr", ""),
                "coach_text_hi": trans.get("hi", ""),
                "tips_en": "",
                "tips_mr": "",
                "tips_hi": "",
            })

        # Only save if we have at least the starting position + a few moves
        if len(processed_moves) < 3:
            print(f"    Skipping '{var_name_en}' — too few valid moves ({len(processed_moves)-1} moves).")
            continue

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
            print(f"    [OK] Saved '{var_name_en}' ({len(processed_moves)-1} moves)")
            saved_count += 1
        except Exception as e:
            print(f"    [ERROR] DB error saving '{var_name_en}': {e}")

    return saved_count
