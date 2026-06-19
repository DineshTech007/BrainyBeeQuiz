import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.quiz_service import generate_and_save_book_quiz, get_quiz_from_db, get_book_quiz_from_db
from config.supabase_client import supabase_db
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()

BASE_LIBRARY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "BookLibrary")

@router.get("/books")
async def get_books(grade: str, language: str = "English"):
    """
    Returns list of books for a given grade and language from Supabase Storage,
    along with indicators for which books already have quizzes generated.
    """
    try:
        folder_path = f"{grade}/{language}"
        res = supabase_db.storage.from_("library_books").list(folder_path)
        books = [f["name"] for f in res if isinstance(f, dict) and f.get("name", "").endswith(".pdf")]
        
        # Fetch existing quizzes from DB to see which books have questions
        existing_quizzes_resp = supabase_db.table("library_quizzes").select("book_title").eq("grade", grade).eq("language", language).execute()
        books_with_quizzes = [q["book_title"] for q in existing_quizzes_resp.data] if existing_quizzes_resp.data else []
        
        return {"status": "success", "books": books, "books_with_quizzes": books_with_quizzes}
    except Exception as e:
        print(f"Error fetching books from storage: {e}")
        return {"status": "success", "books": []}

@router.get("/read")
async def read_book(grade: str, book: str, language: str = "English"):
    """
    Streams the PDF book from Supabase Storage.
    """
    try:
        bucket_path = f"{grade}/{language}/{book}"
        public_url = supabase_db.storage.from_("library_books").get_public_url(bucket_path)
        
        async def generate():
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", public_url) as r:
                    if r.status_code != 200:
                        raise Exception("Book not found in storage")
                    async for chunk in r.aiter_bytes():
                        yield chunk
                        
        return StreamingResponse(
            generate(), 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"inline; filename={book}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

class GenerateBookQuizRequest(BaseModel):
    grade: str
    language: str = "English"
    book: str
    num_questions: int = 10

@router.post("/quiz/generate")
async def generate_book_quiz(request: GenerateBookQuizRequest):
    bucket_path = f"{request.grade}/{request.language}/{request.book}"
    public_url = supabase_db.storage.from_("library_books").get_public_url(bucket_path)
        
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
            import io
            
            # Fetch PDF into memory
            async with httpx.AsyncClient() as client:
                response = await client.get(public_url)
                if response.status_code == 200:
                    reader = PyPDF2.PdfReader(io.BytesIO(response.content))
                    num_pages = len(reader.pages)
                    for i in range(num_pages):
                        text = reader.pages[i].extract_text()
                        if text:
                            context_text += text + "\n"
        except ImportError:
            print("PyPDF2 not installed, passing only book title to Gemini")
        except Exception as e:
            print("Failed to read PDF from storage:", e)
            
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
