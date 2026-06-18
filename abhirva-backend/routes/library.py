import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.quiz_service import generate_and_save_book_quiz, get_quiz_from_db, get_book_quiz_from_db
from config.supabase_client import supabase_db

router = APIRouter()

BASE_LIBRARY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "BookLibrary")

@router.get("/books")
async def get_books(grade: str, language: str = "English"):
    """
    Returns list of books for a given grade and language.
    """
    grade_dir = os.path.join(BASE_LIBRARY_DIR, grade, language)
    if not os.path.exists(grade_dir):
        return {"status": "success", "books": []}
        
    books = []
    for filename in os.listdir(grade_dir):
        if filename.endswith(".pdf"):
            books.append(filename)
            
    return {"status": "success", "books": books}

@router.get("/read")
async def read_book(grade: str, book: str, language: str = "English"):
    """
    Streams the PDF book.
    """
    book_path = os.path.join(BASE_LIBRARY_DIR, grade, language, book)
    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail="Book not found")
        
    return FileResponse(book_path, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=" + book})

class GenerateBookQuizRequest(BaseModel):
    grade: str
    language: str = "English"
    book: str
    num_questions: int = 10

@router.post("/quiz/generate")
async def generate_book_quiz(request: GenerateBookQuizRequest):
    book_path = os.path.join(BASE_LIBRARY_DIR, request.grade, request.language, request.book)
    if not os.path.exists(book_path):
        raise HTTPException(status_code=404, detail="Book not found")
        
    try:
        # Check if quiz already exists
        quiz_data = get_book_quiz_from_db(
            grade=request.grade,
            language=request.language,
            book_title=request.book
        )
        
        if quiz_data.get("success") is not False and "error" not in quiz_data:
             return {"status": "success", "message": "Quiz already generated", "data": quiz_data}
             
        # Extract text from first 5 pages to give Gemini context
        context_text = ""
        try:
            import PyPDF2
            with open(book_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = min(5, len(reader.pages))
                for i in range(num_pages):
                    text = reader.pages[i].extract_text()
                    if text:
                        context_text += text + "\n"
        except ImportError:
            print("PyPDF2 not installed, passing only book title to Gemini")
        except Exception as e:
            print("Failed to read PDF:", e)
            
        new_quiz = generate_and_save_book_quiz(
            grade=request.grade,
            book_name=request.book,
            context=context_text,
            language=request.language,
            num_questions=request.num_questions
        )
        if "error" in new_quiz:
             raise Exception(new_quiz["error"])
             
        return {"status": "success", "message": "Quiz generated successfully", "data": new_quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QuizSubmitRequest(BaseModel):
    student_id: str
    quiz_id: str
    score: int
    total_questions: int

@router.post("/quiz/submit")
async def submit_book_quiz(request: QuizSubmitRequest):
    try:
        points_earned = request.score
            
        attempt_data = {
            "profile_id": request.student_id,
            "library_quiz_id": request.quiz_id,
            "score": request.score,
            "total_questions": request.total_questions,
            "points_earned": points_earned
        }
        
        supabase_db.table("library_test_attempts").insert(attempt_data).execute()
        
        profile_resp = supabase_db.table("profiles").select("book_points").eq("id", request.student_id).execute()
        
        if profile_resp.data and len(profile_resp.data) > 0:
            current_points = profile_resp.data[0].get("book_points") or 0
            new_total = current_points + points_earned
            supabase_db.table("profiles").update({"book_points": new_total}).eq("id", request.student_id).execute()
            
        return {
            "status": "success",
            "message": "Quiz submitted successfully!",
            "data": {"score": request.score, "points_earned": points_earned, "new_total": new_total if profile_resp.data else points_earned}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
async def get_book_leaderboard():
    try:
        query = supabase_db.table("profiles").select("id, full_name, book_points").eq("role", "STUDENT").order("book_points", desc=True).limit(10)
        response = query.execute()
        
        return {
            "status": "success",
            "leaderboard": response.data if response.data else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
