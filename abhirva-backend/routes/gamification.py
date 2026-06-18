from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from config.supabase_client import supabase_db

router = APIRouter()

class QuizSubmitRequest(BaseModel):
    student_id: str
    quiz_id: str
    score: int
    total_questions: int

@router.post("/quiz/submit")
async def submit_quiz(request: QuizSubmitRequest):
    """
    Endpoint for submitting a quiz and calculating points.
    """
    try:
        # Calculate points (1 point per correct answer)
        points_earned = request.score
            
        # 1. Insert into test_attempts
        attempt_data = {
            "profile_id": request.student_id,
            "quiz_id": request.quiz_id,
            "score": request.score,
            "points_earned": points_earned,
            "max_score": request.total_questions,
            "topics": "Practice Quiz"
        }
        
        attempt_resp = supabase_db.table("test_attempts").insert(attempt_data).execute()
        
        # 2. Update profiles.total_points
        # We need to fetch the current points first
        profile_resp = supabase_db.table("profiles").select("total_points").eq("id", request.student_id).execute()
        
        if profile_resp.data and len(profile_resp.data) > 0:
            current_points = profile_resp.data[0].get("total_points") or 0
            new_total = current_points + points_earned
            
            supabase_db.table("profiles").update({"total_points": new_total}).eq("id", request.student_id).execute()
            
        return {
            "status": "success",
            "message": "Quiz submitted successfully!",
            "data": {
                "score": request.score,
                "points_earned": points_earned,
                "new_total": new_total if profile_resp.data else points_earned
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
async def get_leaderboard(grade: str = None):
    """
    Fetches the top 10 students by points.
    """
    try:
        query = supabase_db.table("profiles").select("id, full_name, total_points").eq("role", "STUDENT").order("total_points", desc=True).limit(10)
        
        # In a real app we might filter by grade if 'profiles' tracked grade directly, 
        # but for now we just return the global top 10.
        
        response = query.execute()
        
        return {
            "status": "success",
            "leaderboard": response.data if response.data else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
