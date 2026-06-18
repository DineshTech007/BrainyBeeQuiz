import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("f:/AbhirvaLearning/abhirva-frontend/.env.local")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

# Check all admins
res = supabase.table("profiles").select("*").eq("role", "ADMIN").execute()
print("ADMIN PROFILES:")
for p in res.data:
    print(p)

print("\nALL PROFILES:")
res2 = supabase.table("profiles").select("id, email, full_name, role").execute()
for p in res2.data:
    print(p)
