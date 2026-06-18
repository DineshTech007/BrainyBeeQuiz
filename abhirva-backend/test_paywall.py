import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from config.supabase_client import supabase_db

client = TestClient(app)

def run_paywall_test():
    print("[START] Testing Admin Assignment and Paywall Logic...")
    
    # 1. Create a dummy student profile directly in Supabase
    print("\n--- Creating Dummy Student Profile ---")
    profile_resp = supabase_db.table("profiles").insert({
        "full_name": "Test Student",
        "role": "STUDENT"
    }).execute()
    
    if not profile_resp.data:
        print("[FAIL] Could not create test profile.")
        return
        
    student_id = profile_resp.data[0]["id"]
    print(f"Created student with ID: {student_id}")
    
    # Setup request payload
    quiz_request = {
        "student_id": student_id,
        "board": "CBSE",
        "grade": "10",
        "subject": "Mathematics",
        "chapter": "Polynomials" # We already generated this, so it should be a fast cache hit
    }

    # 2. Consume Free Trial #1
    print("\n--- Attempt 1: Consuming Free Trial 1 ---")
    resp1 = client.post("/api/student/quiz/start", json=quiz_request)
    print(f"Status: {resp1.status_code}")
    
    # 3. Consume Free Trial #2
    print("\n--- Attempt 2: Consuming Free Trial 2 ---")
    resp2 = client.post("/api/student/quiz/start", json=quiz_request)
    print(f"Status: {resp2.status_code}")
    
    # 4. Hit Paywall (Attempt 3 should fail)
    print("\n--- Attempt 3: Expecting Paywall Block (403 Forbidden) ---")
    resp3 = client.post("/api/student/quiz/start", json=quiz_request)
    print(f"Status: {resp3.status_code}")
    if resp3.status_code == 403:
        print("[SUCCESS] Paywall successfully blocked the student!")
        print(f"Error Message: {resp3.json().get('detail', {}).get('message')}")
    else:
        print("[FAIL] Paywall did not trigger.")
        
    # 5. Admin Assignment
    print("\n--- Admin Assignment: Granting Package ---")
    # Get the mock package ID
    pkg_resp = supabase_db.table("packages").select("id").ilike("name", "%10th Board Mathematics Booster%").execute()
    if not pkg_resp.data:
        print("[FAIL] Could not find the mock package in DB.")
        return
    package_id = pkg_resp.data[0]["id"]
    
    grant_request = {
        "admin_id": "mock_admin_123",
        "target_profile_id": student_id,
        "package_id": package_id
    }
    grant_resp = client.post("/api/admin/grant", json=grant_request)
    print(f"Status: {grant_resp.status_code} | {grant_resp.json().get('message')}")
    
    # 6. Attempt 4: Success due to active subscription
    print("\n--- Attempt 4: Expecting Success (Subscription Active) ---")
    resp4 = client.post("/api/student/quiz/start", json=quiz_request)
    print(f"Status: {resp4.status_code}")
    if resp4.status_code == 200:
        print("[SUCCESS] Student successfully bypassed paywall using their granted subscription!")
    else:
        print("[FAIL] Subscription bypass failed.")
        
    # Cleanup dummy student
    print("\n--- Cleaning Up Database ---")
    supabase_db.table("profiles").delete().eq("id", student_id).execute()
    print("Test profile deleted.")

if __name__ == "__main__":
    run_paywall_test()
