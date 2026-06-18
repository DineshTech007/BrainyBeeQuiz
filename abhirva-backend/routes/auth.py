from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config.supabase_client import supabase_db
from supabase import create_client
import os

router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "STUDENT"  # STUDENT, PARENT, ADMIN


@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticates a user via Supabase Auth (email + password).
    Returns the Supabase access_token, refresh_token, and the user's profile row.
    """
    try:
        # Use a Supabase client with the SERVICE_ROLE key to call auth admin
        # We call signInWithPassword using the project anon-level auth endpoint
        # The Supabase Python client supports auth.sign_in_with_password
        auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)

        auth_response = auth_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        auth_user = auth_response.user
        session = auth_response.session

        # Fetch the profile row linked to this auth UID
        profile_resp = supabase_db.table("profiles").select("*").eq("id", auth_user.id).execute()

        if not profile_resp.data or len(profile_resp.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Profile not found for this account. Please contact support."
            )

        profile = profile_resp.data[0]

        return {
            "status": "success",
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "profile": {
                "id": profile["id"],
                "full_name": profile.get("full_name") or profile.get("name") or auth_user.email,
                "email": auth_user.email,
                "role": profile.get("role", "STUDENT"),
                "total_points": profile.get("total_points", 0),
                "book_points": profile.get("book_points", 0),
                "free_tests_taken": profile.get("free_tests_taken", 0),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg or "invalid_credentials" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        raise HTTPException(status_code=500, detail=f"Authentication error: {error_msg}")


@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Creates a new Supabase Auth user AND a linked profile row.
    The profile.id is set to the Auth user's UUID to link them.
    """
    try:
        auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 1. Create Supabase Auth user
        auth_response = auth_client.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,  # Auto-confirm so user can login immediately
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Failed to create auth user.")

        auth_user = auth_response.user

        # 2. Create profile row with the Auth UID as primary key
        role = request.role.upper()
        if role not in ["STUDENT", "PARENT", "ADMIN"]:
            role = "STUDENT"

        profile_data = {
            "id": auth_user.id,         # Link profile to Auth user via same UUID
            "full_name": request.full_name,
            "role": role,
            "free_tests_taken": 0,
            "total_points": 0,
            "book_points": 0,
        }

        profile_resp = supabase_db.table("profiles").insert(profile_data).execute()

        if not profile_resp.data:
            # Cleanup: delete the auth user if profile creation failed
            try:
                auth_client.auth.admin.delete_user(auth_user.id)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail="Failed to create user profile.")

        return {
            "status": "success",
            "message": "Account created successfully. You can now log in.",
            "profile_id": auth_user.id,
            "full_name": request.full_name,
            "email": request.email,
            "role": role,
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg or "already been registered" in error_msg:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        raise HTTPException(status_code=500, detail=f"Signup error: {error_msg}")


@router.post("/logout")
async def logout():
    """
    Server-side logout acknowledgement.
    The actual session invalidation happens via Supabase's built-in token expiry.
    """
    return {"status": "success", "message": "Logged out successfully."}
