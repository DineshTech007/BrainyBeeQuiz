from fastapi import APIRouter, HTTPException
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.supabase_client import supabase_db
from pydantic import BaseModel
from services.chess_parser import call_gemini_api, batch_translate

router = APIRouter()

class DynamicCoachRequest(BaseModel):
    fen: str
    bookMove: str
    userMove: str
    evaluation: float
    openingName: str

@router.get("/study/concepts")
async def get_study_concepts():
    """Returns a list of all chess study concepts in 3 languages."""
    try:
        response = supabase_db.table("chess_study_concepts_v2").select("*").execute()
        return {"status": "success", "concepts": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/openings")
async def get_all_openings():
    """Returns a list of all available chess openings in the database."""
    try:
        response = supabase_db.table("chess_variations").select("opening_name").execute()
        
        # Get unique opening names
        openings = set()
        if response.data:
            for item in response.data:
                openings.add(item["opening_name"])
                
        return {"status": "success", "openings": list(openings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/openings/{opening_name}")
async def get_opening_variations(opening_name: str):
    """
    Returns all variations for a specific opening to feed into the Chess Tutor.
    """
    try:
        # We query case-insensitively
        response = supabase_db.table("chess_variations").select("*").ilike("opening_name", opening_name).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No variations found for opening: {opening_name}")
            
        # Format for ChessTutor.jsx
        # ChessTutor expects `syllabusData = { variations: [...] }`
        variations = []
        for item in response.data:
            variations.append({
                "id": item["id"],
                "name_en": item["variation_name_en"],
                "name_mr": item["variation_name_mr"],
                "name_hi": item["variation_name_hi"],
                "description_en": item.get("description_en", ""),
                "description_mr": item.get("description_mr", ""),
                "description_hi": item.get("description_hi", ""),
                "moves": item["moves"]
            })
        # Sort variations by the number of moves (descending)
        variations.sort(key=lambda x: len(x.get("moves", [])), reverse=True)
            
        return {"status": "success", "syllabusData": {"variations": variations}}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dynamic-coach")
async def get_dynamic_coach_explanation(req: DynamicCoachRequest):
    """
    Takes an off-book user move and engine evaluation, and prompts Gemini to explain the mistake.
    """
    try:
        # Generate prompt for Gemini
        prompt = f"""You are a professional chess coach. 
The user is studying the {req.openingName} opening.
Current position FEN: {req.fen}
The correct book move was: {req.bookMove}
The user played a mistake/deviation: {req.userMove}
Stockfish evaluates the new position at: {req.evaluation} pawns.

Explain to the user in 1-3 simple sentences why {req.userMove} is a mistake or sub-optimal compared to {req.bookMove}, and briefly how the opponent might punish it. Keep it very encouraging but instructive."""

        explanation_en = call_gemini_api(prompt, temperature=0.3).strip()
        
        # Translate to Marathi and Hindi
        translations = batch_translate([explanation_en])
        explanation_mr = translations[0].get("mr", explanation_en) if translations else explanation_en
        explanation_hi = translations[0].get("hi", explanation_en) if translations else explanation_en

        return {
            "status": "success",
            "coach_en": explanation_en,
            "coach_mr": explanation_mr,
            "coach_hi": explanation_hi
        }
    except Exception as e:
        print(f"Dynamic coach error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dynamic coaching explanation.")
