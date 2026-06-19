from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config.supabase_client import supabase_db
from services.quiz_service import generate_and_save_quiz, generate_and_save_past_paper
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
admin_db_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY else supabase_db

router = APIRouter()

class GrantRequest(BaseModel):
    admin_id: str
    target_profile_id: str
    package_name: str
    package_id: str = ""  # Optional: pass the DB UUID for reliable revoke matching

class GenerateQuizRequest(BaseModel):
    board: str
    grade: str
    subject: str
    chapter: str
    num_questions: int = 10
    quiz_type: str = "Standard"

class GeneratePastPaperRequest(BaseModel):
    board: str
    grade: str
    subject: str
    year: str
    num_questions: int = 10

@router.get("/students")
async def get_all_students(admin_key: str = None):
    """
    Fetches all student profiles from the database.
    """
    try:
        response = supabase_db.table("profiles").select("*").eq("role", "STUDENT").execute()
        return {"status": "success", "students": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics")
async def get_topics(subject: str = None, category: str = "10th Class", sst_sub_subject: str = None):
    """
    Fetches available topics for a given subject and category.
    """
    try:
        if category == "IMO Test" or subject == "IMO Test":
            # Return hardcoded IMO categories
            return {"status": "success", "topics": [
                "Number Sense",
                "Computation Operations",
                "Fractions",
                "Money",
                "Length, Weight, Capacity, Time and Temperature",
                "Geometry",
                "Data Handling",
                "Logical Reasoning"
            ]}
        elif category in ["NSO Test", "SOF Test"] or subject in ["NSO Test", "SOF Test"]:
            return {"status": "success", "topics": [
                "Plants and Animals",
                "Birds",
                "Food",
                "Housing, Clothing and Occupation",
                "Transport, Communication and Safety Rules",
                "Human Body",
                "Earth and Universe",
                "Matter and Materials",
                "Light, Sound and Force",
                "Our Environment",
                "Logical Reasoning"
            ]}
        elif category == "IEO Test" or subject == "IEO Test":
            return {"status": "success", "topics": [
                "Word Power",
                "Synonyms and Antonyms",
                "Gender and Relations",
                "Singular-Plural and One Word Substitution",
                "Idioms and Proverbs",
                "Nouns and Pronouns",
                "Adjectives and Conjunctions",
                "Verbs and Adverbs",
                "Articles and Prepositions",
                "Tenses",
                "Questions and Question Tags",
                "Comprehension",
                "Spoken and Written Expression"
            ]}
        
        if not subject:
            return {"status": "success", "topics": []}
            
        if subject == "Marathi":
            return {"status": "success", "topics": [
                "Chapter 2 (संतवाणी)", 
                "Chapter 3 (शाल)", 
                "Chapter 4 (उपास)", 
                "Chapter 4.1 (मोठे होत असलेल्या मुलांनो)",
                "Grammar: Mix (All Topics)", 
                "Grammar: वाक्प्रचार (Phrases)", 
                "Grammar: समास (Compounds)", 
                "Grammar: शब्दसंपत्ती (Vocabulary)", 
                "Grammar: विरामचिन्हे (Punctuation)", 
                "Grammar: लेखन नियम (Writing Rules)"
            ]}
            
        if subject == "Computers":
            return {"status": "success", "topics": [
                "Unit-1: Digital Documentation (Advanced)",
                "Unit-2: Electronic Spreadsheet (Advanced)",
                "Unit-3: Database Management System",
                "Unit-4: Maintain Healthy, Safe and Secure Working Environment"
            ]}
            
        import json
        
        # Normalize subject names to match JSON filenames
        subject_map = {
            "Mathematics": "maths",
            "Science": "science",
            "English": "english",
            "SST": "sst",
            "Hindi": "hindi",
            "Marathi": "marathi",
            "Computers": "computers"
        }
        normalized_subject = subject_map.get(subject, subject.lower())
        
        json_filename = f"{normalized_subject}_chapters.json"
        chapters_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), json_filename)
        
        if os.path.exists(chapters_path):
            with open(chapters_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            topics = []
            for pdf, chapters in data.items():
                if subject == "SST" and sst_sub_subject and sst_sub_subject.replace(" ", "-") not in pdf:
                    continue
                for chap in chapters:
                    page_info = f" (Page {chap.get('start_page', '')}-{chap.get('end_page', '')})" if 'start_page' in chap else ""
                    if subject == "English":
                        topics.append(f"{chap['title']}{page_info}")
                    else:
                        topics.append(f"{pdf.replace('.pdf', '')} - {chap['title']}{page_info}")
            return {"status": "success", "topics": topics}
            
        # Dynamically read from 10thBooks folder in Supabase Storage
        topics = []
        try:
            res = supabase_db.storage.from_("tenth_books").list(subject)
            for f in res:
                if isinstance(f, dict):
                    filename = f.get("name", "")
                    if filename.endswith(".pdf") or filename.endswith(".docx"):
                        name_without_ext = os.path.splitext(filename)[0]
                        topics.append(name_without_ext)
        except Exception as e:
            print(f"Failed to list topics from storage: {e}")
                    
        # Fallback if no files found
        if not topics:
            if subject == "English":
                topics = [
                    "Chapter 1: A Letter to God / Dust of Snow / Fire and Ice",
                    "Chapter 2: Nelson Mandela: Long Walk to Freedom",
                    "Chapter 3: Two Stories about Flying",
                    "Chapter 4: From the Diary of Anne Frank",
                    "Chapter 5: Glimpses of India",
                    "Chapter 6: Mijbil the Otter",
                    "Chapter 7: Madam Rides the Bus",
                    "Chapter 8: The Sermon at Benares",
                    "Chapter 9: The Proposal",
                    "Supplementary: Footprints Without Feet",
                    "First Flight Poems Supplementary",
                    "Class 10 Literature Reader Guide"
                ]
            elif subject == "Science":
                topics = [
                    "Chapter 1: Chemical Reactions and Equations",
                    "Chapter 2: Acids, Bases and Salts",
                    "Chapter 3: Metals and Non-metals",
                    "Chapter 4: Carbon and its Compounds",
                    "Chapter 5: Life Processes",
                    "Chapter 6: Control and Coordination",
                    "Chapter 7: How do Organisms Reproduce?",
                    "Chapter 8: Heredity and Evolution",
                    "Chapter 9: Light Reflection and Refraction",
                    "Chapter 10: The Human Eye and the Colourful World",
                    "Chapter 11: Electricity",
                    "Chapter 12: Magnetic Effects of Electric Current",
                    "Chapter 13: Our Environment"
                ]
            elif subject == "Maths":
                topics = [
                    "Chapter 1: Real Numbers",
                    "Chapter 2: Polynomials",
                    "Chapter 3: Pair of Linear Equations in Two Variables",
                    "Chapter 4: Quadratic Equations",
                    "Chapter 5: Arithmetic Progressions",
                    "Chapter 6: Triangles",
                    "Chapter 7: Coordinate Geometry",
                    "Chapter 8: Introduction to Trigonometry",
                    "Chapter 9: Some Applications of Trigonometry",
                    "Chapter 10: Circles",
                    "Chapter 11: Areas Related to Circles",
                    "Chapter 12: Surface Areas and Volumes",
                    "Chapter 13: Statistics",
                    "Chapter 14: Probability"
                ]
            else:
                topics = [f"Default Topic 1 for {subject}", f"Default Topic 2 for {subject}"]
                
        return {"status": "success", "topics": topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{profile_id}/access")
async def get_student_access(profile_id: str, admin_key: str = None):
    """
    Fetches the active subscriptions for a specific student.
    """
    try:
        sub_resp = supabase_db.table("subscriptions").select("package_id, status").eq("profile_id", profile_id).eq("status", "ACTIVE").execute()
        
        if not sub_resp.data:
            return {"status": "success", "subscriptions": []}
            
        package_ids = [sub["package_id"] for sub in sub_resp.data]
        
        pkg_resp = supabase_db.table("packages").select("id, name").in_("id", package_ids).execute()
        
        return {"status": "success", "subscriptions": pkg_resp.data if pkg_resp.data else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/grant")
async def grant_package(request: GrantRequest):
    """
    Manually injects a subscription row into Supabase to gift a package.
    """
    try:
        # Look up the package UUID by name
        pkg_resp = supabase_db.table("packages").select("id").ilike("name", request.package_name).execute()
        
        if pkg_resp.data and len(pkg_resp.data) > 0:
            actual_package_id = pkg_resp.data[0]["id"]
        else:
            # Auto-create the package if it doesn't exist
            new_pkg_resp = supabase_db.table("packages").insert({
                "name": request.package_name,
                "price": 499.0, # default price
                "is_active": True
            }).execute()
            if not new_pkg_resp.data:
                raise Exception(f"Failed to auto-create package {request.package_name}")
            actual_package_id = new_pkg_resp.data[0]["id"]

        # Check if subscription already exists
        existing = supabase_db.table("subscriptions").select("id, status").eq("profile_id", request.target_profile_id).eq("package_id", actual_package_id).execute()
        
        if existing.data and len(existing.data) > 0:
            if existing.data[0].get("status") != "ACTIVE":
                supabase_db.table("subscriptions").update({"status": "ACTIVE"}).eq("id", existing.data[0]["id"]).execute()
                return {"status": "success", "message": f"Successfully re-activated package {request.package_name}."}
            return {"status": "success", "message": "Student already has an active subscription for this package."}
        
        # Insert new subscription
        subscription_data = {
            "profile_id": request.target_profile_id,
            "package_id": actual_package_id,
            "status": "ACTIVE"
        }
        
        response = supabase_db.table("subscriptions").insert(subscription_data).execute()
        
        if not response.data:
            raise Exception("Failed to insert subscription.")
            
        print(f"Admin {request.admin_id} granted {request.package_name} (ID: {actual_package_id}) to {request.target_profile_id}")
        return {
            "status": "success",
            "message": f"Successfully granted package {request.package_name} to student."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/revoke")
async def revoke_package(request: GrantRequest):
    """
    Revokes a granted package from a student.
    
    Fix: Accepts package_id (UUID) directly for reliable matching.
    Falls back to ilike name search if package_id is not provided.
    Dual-action: tries DELETE first, then UPDATE to REVOKED as safety net.
    """
    try:
        actual_package_id = None

        # --- Step 1: Resolve package ID ---
        if request.package_id:
            # Reliable path: direct UUID lookup
            pkg_check = supabase_db.table("packages").select("id, name").eq("id", request.package_id).execute()
            if pkg_check.data:
                actual_package_id = pkg_check.data[0]["id"]
        
        if not actual_package_id:
            # Fallback: search by exact name first, then ilike
            pkg_resp = supabase_db.table("packages").select("id, name").eq("name", request.package_name).execute()
            if not pkg_resp.data:
                # Try case-insensitive partial match
                pkg_resp = supabase_db.table("packages").select("id, name").ilike("name", f"%{request.package_name}%").execute()
            
            if not pkg_resp.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Package '{request.package_name}' not found in database."
                )
            actual_package_id = pkg_resp.data[0]["id"]
            resolved_name = pkg_resp.data[0]["name"]
        else:
            resolved_name = request.package_name

        # --- Step 2: Check subscription exists ---
        existing = supabase_db.table("subscriptions").select("id, status").eq(
            "profile_id", request.target_profile_id
        ).eq("package_id", actual_package_id).execute()

        if not existing.data:
            return {
                "status": "error",
                "message": f"Student does not have an active subscription for '{resolved_name}'."
            }

        subscription_id = existing.data[0]["id"]

        # --- Step 3: Try DELETE first ---
        try:
            admin_db_client.table("subscriptions").delete().eq("id", subscription_id).execute()
            print(f"Admin {request.admin_id} deleted subscription {subscription_id}")
        except Exception as e:
            print("Delete failed, trying update to REVOKED:", e)
            # Safety net: UPDATE status to REVOKED instead
            update_response = admin_db_client.table("subscriptions").update(
                {"status": "REVOKED"}
            ).eq("id", subscription_id).execute()

            if not update_response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to revoke subscription — both DELETE and UPDATE failed."
                )

        print(f"Admin {request.admin_id} revoked '{resolved_name}' (pkg: {actual_package_id}) from profile {request.target_profile_id}")
        return {
            "status": "success",
            "message": f"Successfully revoked '{resolved_name}' from student."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revoke failed: {str(e)}")


@router.post("/generate_quiz")
async def generate_quiz(request: GenerateQuizRequest):
    """
    Generates a quiz using Gemini and saves it to the database.
    """
    try:
        grade = request.grade
        if grade == "10th Class":
            grade = "10"
            
        quiz_data = generate_and_save_quiz(
            board=request.board,
            grade=grade,
            subject=request.subject,
            chapter=request.chapter,
            num_questions=request.num_questions,
            quiz_type=request.quiz_type
        )
        if "error" in quiz_data:
            raise Exception(quiz_data["error"])
            
        return {
            "status": "success",
            "message": "Quiz generated and saved successfully",
            "data": quiz_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_past_paper")
async def admin_generate_past_paper(request: GeneratePastPaperRequest):
    """
    Admin endpoint to generate a full Past Paper.
    """
    try:
        paper_data = generate_and_save_past_paper(
            board=request.board,
            grade=request.grade,
            subject=request.subject,
            year=request.year,
            num_questions=request.num_questions
        )
        if "error" in paper_data:
            raise Exception(paper_data["error"])
            
        return {"status": "success", "message": "Past Paper generated and saved successfully", "data": paper_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import json

CONNECTIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "parent_connections.json")

def load_connections():
    if os.path.exists(CONNECTIONS_FILE):
        with open(CONNECTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_connections(data):
    with open(CONNECTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@router.delete("/student/{profile_id}")
async def delete_student(profile_id: str):
    try:
        from supabase import create_client
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. Clean up referencing tables to prevent foreign key errors
        try:
            res = admin_db_client.table("subscriptions").delete().eq("profile_id", profile_id).execute()
            if not res.data:
                print("No subscriptions found to delete, or RLS blocked it.")
        except Exception as e:
            print("Error deleting subscriptions:", e)

        try:
            admin_db_client.table("test_attempts").delete().eq("profile_id", profile_id).execute()
        except Exception as e:
            print("Error deleting test_attempts:", e)

        try:
            admin_db_client.table("library_test_attempts").delete().eq("profile_id", profile_id).execute()
        except Exception as e:
            print("Error deleting library_test_attempts:", e)

        # 2. Delete Auth user
        try:
            auth_client.auth.admin.delete_user(profile_id)
        except Exception as e:
            print("Auth delete error:", e)
            
        # 3. Delete Profile
        try:
            res = admin_db_client.table("profiles").delete().eq("id", profile_id).execute()
            if not res.data:
                print("Profile delete returned empty data (may not exist or RLS blocked it)")
        except Exception as e:
            print("Profile delete error (may be handled by cascade):", e)
        
        conns = load_connections()
        changed = False
        for pid, students in conns.items():
            if profile_id in students:
                students.remove(profile_id)
                changed = True
        if changed:
            save_connections(conns)
            
        return {"status": "success", "message": "Student deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parents")
async def get_all_parents():
    try:
        response = supabase_db.table("profiles").select("*").eq("role", "PARENT").execute()
        return {"status": "success", "parents": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parent-connections")
async def get_parent_connections():
    return {"status": "success", "connections": load_connections()}

class ConnectionRequest(BaseModel):
    parent_id: str
    student_id: str

@router.post("/parent-connection")
async def add_parent_connection(request: ConnectionRequest):
    conns = load_connections()
    if request.parent_id not in conns:
        conns[request.parent_id] = []
    if request.student_id not in conns[request.parent_id]:
        conns[request.parent_id].append(request.student_id)
        save_connections(conns)
    return {"status": "success", "message": "Connection added"}

@router.delete("/parent-connection")
async def remove_parent_connection(parent_id: str, student_id: str):
    conns = load_connections()
    if parent_id in conns and student_id in conns[parent_id]:
        conns[parent_id].remove(student_id)
        save_connections(conns)
    return {"status": "success", "message": "Connection removed"}
