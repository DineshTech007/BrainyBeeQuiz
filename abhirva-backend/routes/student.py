from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from services.quiz_service import get_quiz_from_db, get_book_quiz_from_db, get_all_past_papers, get_past_paper_from_db
from config.supabase_client import supabase_db

router = APIRouter()

class SignupRequest(BaseModel):
    full_name: str
    email: Optional[str] = None
    role: Optional[str] = "STUDENT"

@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Creates a new student or parent profile.
    """
    try:
        response = supabase_db.table("profiles").insert({
            "full_name": request.full_name,
            "role": request.role.upper(),
            "free_tests_taken": 0,
            "total_points": 0
        }).execute()
        
        if not response.data:
            raise Exception("Failed to create profile")
            
        student_id = response.data[0]["id"]
        return {"status": "success", "student_id": student_id, "full_name": request.full_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/past_papers")
async def fetch_past_papers():
    """
    Fetches all available past papers.
    """
    try:
        data = get_all_past_papers()
        if "error" in data:
            raise Exception(data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/past_papers/start")
async def start_past_paper(request: PastPaperRequest):
    """
    Starts a past paper exam.
    """
    try:
        # Check student access (simplified for now, assume access)
        data = get_past_paper_from_db(request.past_paper_id)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QuizRequest(BaseModel):
    student_id: str
    board: str
    grade: str
    subject: str
    chapter: str
    language: Optional[str] = "English"

class PastPaperRequest(BaseModel):
    student_id: str
    past_paper_id: str

@router.post("/quiz/start")
async def start_quiz(request: QuizRequest):
    """
    Endpoint for a student to request a quiz.
    It will first check if the student has access, 
    then fetch the quiz from Supabase.
    """
    try:
        # Determine the required package name based on request parameters
        if request.board == "Library":
            package_name = "Book Library"
        elif request.subject == "IMO Test" or request.board == "IMO":
            package_name = f"IMO {request.grade}"
        else:
            # Map sub-subjects back to their master package
            sst_subs = ["History", "Geography", "Political Science", "Economics"]
            package_subject = "SST" if request.subject in sst_subs else request.subject
            package_name = f"{request.grade}th Board {package_subject} Booster"
            
        # First find the package ID by name
        pkg_resp = supabase_db.table("packages").select("id").ilike("name", f"%{package_name}%").execute()
        has_subscription = False
        
        if pkg_resp.data and len(pkg_resp.data) > 0:
            package_id = pkg_resp.data[0]["id"]
            # Check subscriptions
            sub_resp = supabase_db.table("subscriptions").select("id").eq("profile_id", request.student_id).eq("package_id", package_id).eq("status", "ACTIVE").execute()
            if sub_resp.data and len(sub_resp.data) > 0:
                has_subscription = True

        # If no subscription, check free_tests_taken
        if not has_subscription:
            profile_resp = supabase_db.table("profiles").select("free_tests_taken").eq("id", request.student_id).execute()
            
            if not profile_resp.data:
                raise HTTPException(status_code=404, detail="Student profile not found.")
                
            free_tests = profile_resp.data[0].get("free_tests_taken", 0)
            
            if free_tests >= 2:
                # Paywall hit
                raise HTTPException(
                    status_code=403, 
                    detail={"error": "TRIAL_EXHAUSTED", "message": f"You need the '{package_name}' package or your 2 free tests are exhausted. Please ask your parent to purchase this package."}
                )
            
            # Increment free_tests_taken
            new_count = free_tests + 1
            supabase_db.table("profiles").update({"free_tests_taken": new_count}).eq("id", request.student_id).execute()
            print(f"Student {request.student_id} consumed free test #{new_count} for {package_name}")
        else:
            print(f"Student {request.student_id} accessed quiz via active subscription to {package_name}.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Access verification failed: {str(e)}")
    
    # Fetch quiz from DB
    if request.board == "Library":
        quiz_data = get_book_quiz_from_db(
            grade=request.grade,
            language=request.language,
            book_title=request.chapter
        )
    else:
        quiz_data = get_quiz_from_db(
            board=request.board,
            grade=request.grade,
            subject=request.subject,
            chapter=request.chapter
        )
    
    if quiz_data.get("success") is False or "error" in quiz_data:
        # Return 404 if not generated yet
        raise HTTPException(status_code=404, detail="This quiz hasn't been published yet. Please ask your administrator.")
        
    return {
        "status": "success",
        "message": "Quiz loaded successfully",
        "data": quiz_data
    }
