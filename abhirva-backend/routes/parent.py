from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config.supabase_client import supabase_db

router = APIRouter()

class PurchaseRequest(BaseModel):
    parent_id: str
    package_id: str
    child_profile_id: str

@router.get("/students")
async def get_students(parent_id: str = None):
    """
    Returns a list of all registered students so the parent can select which child to track.
    If parent_id is provided, filters by parent_connections.json.
    """
    try:
        query = supabase_db.table("profiles").select("id, full_name").eq("role", "STUDENT")
        response = query.execute()
        students = response.data or []
        
        if parent_id:
            import json
            import os
            CONNECTIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "parent_connections.json")
            if os.path.exists(CONNECTIONS_FILE):
                with open(CONNECTIONS_FILE, 'r') as f:
                    conns = json.load(f)
                
                # Only filter if the parent is actually defined in the connections file
                # Otherwise, let them see all students as a fallback for testing
                if parent_id in conns:
                    allowed_student_ids = conns.get(parent_id, [])
                    students = [s for s in students if s["id"] in allowed_student_ids]
                
        return {"status": "success", "students": students}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student_progress/{profile_id}")
async def get_student_progress(profile_id: str):
    """
    Fetches the student's total_points, book_points, and their recent quiz attempts.
    """
    try:
        # Fetch profile info for points
        profile_resp = supabase_db.table("profiles").select("total_points, book_points").eq("id", profile_id).execute()
        if not profile_resp.data:
            raise HTTPException(status_code=404, detail="Student not found")
            
        profile_data = profile_resp.data[0]
        
        # Fetch recent test attempts
        attempts_resp = supabase_db.table("test_attempts").select("id, created_at, score, max_score, topics").eq("profile_id", profile_id).order("created_at", desc=True).limit(5).execute()
        
        return {
            "status": "success",
            "progress": {
                "total_points": profile_data.get("total_points", 0),
                "book_points": profile_data.get("book_points", 0),
                "recent_attempts": attempts_resp.data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/packages")
async def get_packages():
    """
    Returns the available subscription packages from Supabase.
    """
    # ---------------------------------------------------------
    # TODO: Fetch from Supabase PACKAGES table
    # ---------------------------------------------------------
    mock_packages = [
        {"id": "pkg_1", "name": "10th Board Math Booster", "price": 499},
        {"id": "pkg_2", "name": "IMO Gold Package", "price": 999}
    ]
    return {"status": "success", "packages": mock_packages}

@router.post("/purchase")
async def purchase_package(request: PurchaseRequest):
    """
    Placeholder for Razorpay checkout flow.
    """
    return {
        "status": "pending",
        "message": "Razorpay Order ID generated.",
        "order_id": "order_mock_12345"
    }
