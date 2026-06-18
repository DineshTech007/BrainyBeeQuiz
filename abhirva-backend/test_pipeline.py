import sys
import os

# Add the backend directory to Python path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.quiz_service import get_or_create_quiz

def run_test():
    print("[START] Starting Pipeline Test...")
    print("Testing connection to Supabase and Gemini...")
    
    try:
        # Request a test quiz
        # If this is the first time running, it should hit Gemini, save to DB, and return.
        # If run again, it should instantly pull from the Supabase Cache.
        quiz_data = get_or_create_quiz(
            board="CBSE",
            grade="10",
            subject="Mathematics",
            chapter="Polynomials"
        )
        
        if "error" in quiz_data:
            print(f"\n[FAIL] Pipeline failed: {quiz_data['error']}")
        else:
            print("\n[SUCCESS] Pipeline Succeeded!")
            print(f"Quiz ID: {quiz_data.get('id')}")
            print(f"Number of Questions: {len(quiz_data.get('questions', []))}")
            if len(quiz_data.get('questions', [])) > 0:
                print(f"Sample Question: {quiz_data['questions'][0]['question_text']}")
                print(f"Sample Explanation: {quiz_data['questions'][0]['explanation_description']}")
            
    except Exception as e:
        print(f"\n❌ Pipeline crashed: {e}")

if __name__ == "__main__":
    run_test()
