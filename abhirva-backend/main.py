from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import Routers
from routes import student, parent, admin, gamification, library, auth

app = FastAPI(
    title="Abhirva Learning Solutions API",
    description="Backend API for Parent, Student, and Admin Portals",
    version="1.0.0"
)

# Configure CORS (Allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to specific domains in production (e.g. localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(student.router, prefix="/api/student", tags=["Student Portal"])
app.include_router(parent.router, prefix="/api/parent", tags=["Parent Portal"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Portal"])
app.include_router(gamification.router, prefix="/api/student/gamification", tags=["Gamification"])
app.include_router(library.router, prefix="/api/library", tags=["Library"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Import and include Chess Router
from routes import chess
app.include_router(chess.router, prefix="/api/chess", tags=["Chess Tutor"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Abhirva Learning API", "status": "Online"}

if __name__ == "__main__":
    print("[START] Starting FastAPI Server on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
