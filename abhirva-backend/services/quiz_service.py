import json
from google import genai
from google.genai import types
from config.supabase_client import supabase_db
from config.gemini_config import gemini_client

def get_quiz_from_db(board: str, grade: str, subject: str, chapter: str) -> dict:
    """
    Fetches a quiz from Supabase. Returns a dict with "error" if not found.
    """
    try:
        print(f"Fetching quiz from DB for: {board} | {grade} | {subject} | {chapter}".encode('ascii', 'replace').decode('ascii'))
        
        response = (
            supabase_db.table("quizzes")
            .select("id, board, grade, subject, chapter_or_topic, passage, questions(question_text, question_type, difficulty_level, options, correct_option, solution_steps, explanation_description)")
            .eq("board", board)
            .eq("grade", grade)
            .eq("subject", subject)
            .eq("chapter_or_topic", chapter)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            existing_quiz = response.data[0]
            if existing_quiz.get("questions") and len(existing_quiz["questions"]) > 0:
                print("[SUCCESS] Quiz found in database.")
                return existing_quiz
                
        print("[WARN] Quiz not found in database.")
        return {"error": "Quiz not found", "success": False}
        
    except Exception as e:
        print(f"[FAIL] get_quiz_from_db Error: {str(e)}".encode('ascii', 'replace').decode('ascii'))
        return {"error": str(e), "success": False}

def get_book_quiz_from_db(grade: str, language: str, book_title: str) -> dict:
    """
    Fetches a book quiz from the dedicated library_quizzes table in Supabase.
    """
    try:
        print(f"Fetching book quiz from DB for: {grade} | {language} | {book_title}".encode('ascii', 'replace').decode('ascii'))
        
        response = (
            supabase_db.table("library_quizzes")
            .select("id, grade, language, book_title, library_questions(question_text, options, correct_option, explanation_description, marks)")
            .eq("grade", grade)
            .eq("language", language)
            .eq("book_title", book_title)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            existing_quiz = response.data[0]
            # Map the inner join to "questions" to match frontend expectations
            if existing_quiz.get("library_questions") and len(existing_quiz["library_questions"]) > 0:
                existing_quiz["questions"] = existing_quiz["library_questions"]
                del existing_quiz["library_questions"]
                # Also map id to quiz_id to match frontend expectations
                existing_quiz["quiz_id"] = existing_quiz["id"]
                print("[SUCCESS] Book Quiz found in database.")
                return existing_quiz
                
        print("[WARN] Book Quiz not found in database.")
        return {"error": "Quiz not found", "success": False}
        
    except Exception as e:
        print(f"[FAIL] get_book_quiz_from_db Error: {str(e)}".encode('ascii', 'replace').decode('ascii'))
        return {"error": str(e), "success": False}


def generate_and_save_quiz(board: str, grade: str, subject: str, chapter: str, num_questions: int = 10, quiz_type: str = "Standard") -> dict:
    """
    Forces generation of a new quiz via Gemini API and saves it to Supabase.
    """
    try:
        print(f"[INFO] Generating new quiz via Gemini API for {board} | {grade} | {subject} | {chapter}...".encode('ascii', 'replace').decode('ascii'))
        
        prompt = f"""
        Create a high-quality, academic quiz for the following curriculum:
        - Board: {board}
        - Grade: {grade}
        - Subject: {subject}
        - Topic/Chapter: {chapter}
        - Quiz Type: {quiz_type}

        Generate exactly {num_questions} questions.
        For each question, assign a `difficulty_level` ('Easy', 'Medium', or 'Hard') that strictly matches the pattern and rigor of standard CBSE 10th-grade past board exams.
        """

        if subject == "English" and quiz_type == "Comprehension":
            prompt += """
            IMPORTANT: Write an original reading comprehension passage appropriate for a 10th-grade student.
            Return this passage in the root JSON field `passage`. 
            All generated questions MUST be based exclusively on this passage.
            """
        elif subject == "Maths":
            prompt += """
            IMPORTANT: Since this is Maths, generate a mix of MCQ and INTEGER-based questions.
            For INTEGER questions, the `question_type` MUST be "INTEGER", the `options` array MUST be completely empty, and the `correct_option` MUST be a pure number string (e.g., "5", "-2").
            For MCQ questions, `question_type` MUST be "MCQ" and `options` MUST contain exactly 4 strings.
            """
        else:
            prompt += """
            Generate multiple-choice questions. 
            `question_type` MUST be "MCQ", `options` MUST contain exactly 4 strings, and `correct_option` must exactly match one of the options.
            """

        prompt += """
        Provide step-by-step solutions and a detailed explanation for why the answer is correct in `solution_steps` and `explanation_description`.
        """

        system_instruction = f"You are an expert {board} educational content creator. Return ONLY valid JSON in the requested format."

        # Define strict JSON Schema for the output
        response_schema = {
            "type": "object",
            "properties": {
                "passage": {"type": "string"},
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_text": {"type": "string"},
                            "question_type": {"type": "string"},
                            "difficulty_level": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "correct_option": {"type": "string"},
                            "solution_steps": {"type": "string"},
                            "explanation_description": {"type": "string"}
                        },
                        "required": ["question_text", "question_type", "difficulty_level", "options", "correct_option", "solution_steps", "explanation_description"]
                    }
                }
            },
            "required": ["questions"]
        }

        # Call Gemini API
        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=response_schema
        )
        
        ai_response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=generation_config
        )

        generated_text = ai_response.text
        if not generated_text:
            raise Exception("Gemini returned an empty response.")

        parsed_data = json.loads(generated_text)
        generated_questions = parsed_data.get("questions", [])

        print("[INFO] Saving newly generated quiz to Supabase...")
        
        # Check and Delete Existing
        existing_meta = supabase_db.table("quizzes").select("id").eq("board", board).eq("grade", grade).eq("subject", subject).eq("chapter_or_topic", chapter).execute()
        if existing_meta.data and len(existing_meta.data) > 0:
            existing_id = existing_meta.data[0]["id"]
            supabase_db.table("questions").delete().eq("quiz_id", existing_id).execute()
            supabase_db.table("quizzes").delete().eq("id", existing_id).execute()
            
        # Insert Quiz Metadata
        quiz_metadata = {
            "board": board,
            "grade": grade,
            "subject": subject,
            "chapter_or_topic": chapter,
            "passage": parsed_data.get("passage") if parsed_data.get("passage") else None
        }
        
        quiz_insert_response = supabase_db.table("quizzes").insert(quiz_metadata).execute()
        
        if not quiz_insert_response.data:
            raise Exception("Failed to save quiz metadata to Supabase.")
            
        new_quiz = quiz_insert_response.data[0]
        new_quiz_id = new_quiz["id"]

        # Prepare Questions payload
        questions_payload = []
        for q in generated_questions:
            questions_payload.append({
                "quiz_id": new_quiz_id,
                "question_text": q.get("question_text"),
                "question_type": q.get("question_type", "MCQ"),
                "difficulty_level": q.get("difficulty_level", "Medium"),
                "options": q.get("options", []),
                "correct_option": q.get("correct_option"),
                "solution_steps": q.get("solution_steps"),
                "explanation_description": q.get("explanation_description")
            })

        # Bulk Insert Questions
        questions_insert_response = supabase_db.table("questions").insert(questions_payload).execute()
        
        if not questions_insert_response.data:
            print("Error: Questions failed to insert. (Consider rollback logic here)")
            raise Exception("Failed to save questions to Supabase.")

        print("[SUCCESS] Successfully saved and returning new quiz!")
        
        new_quiz["questions"] = questions_payload
        return new_quiz

    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] generate_and_save_quiz Error: {error_msg}".encode('ascii', 'replace').decode('ascii'))
        
        # Fallback if API key is exhausted
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("[INFO] API quota exceeded. Returning mock quiz.")
            return {
                "board": board,
                "grade": grade,
                "subject": subject,
                "chapter_or_topic": chapter,
                "quiz_id": "mock-fallback-id",
                "success": True,
                "questions": [
                    {
                        "question_text": "[API Exhausted Fallback] What happens when your Gemini API key runs out of credits?",
                        "options": ["App crashes", "Returns mock data", "Nothing", "I need to add a new key"],
                        "correct_option": "I need to add a new key",
                        "solution_steps": "Go to AI Studio to manage billing.",
                        "explanation_description": "Your API key prepayment credits are depleted."
                    }
                ]
            }
            
        return {"error": error_msg, "success": False}

def generate_and_save_book_quiz(grade: str, book_name: str, context: str, language: str = "English", num_questions: int = 10) -> dict:
    """
    Forces generation of a new quiz for a library book via Gemini API and saves it to Supabase.
    """
    try:
        board = "Library"
        subject = "Library Book"
        chapter = book_name
        
        print(f"[INFO] Generating new book quiz via Gemini API for {grade} | {book_name}...".encode('ascii', 'replace').decode('ascii'))
        
        prompt = f"""
        Create a reading comprehension multiple-choice quiz in {language} for the following book:
        - Grade Level: {grade}
        - Book Name: {book_name}
        - Language: {language}

        Here is a sample of the book text for context:
        \"\"\"{context}\"\"\"

        Generate exactly {num_questions} questions. They should assess understanding of the text, characters, or general knowledge if the context is insufficient.
        Ensure the correct_option string is an exact match to one of the strings in the options array.
        Provide step-by-step solutions and a detailed explanation for why the answer is correct. All questions, options, and explanations must be written in {language}.
        """

        system_instruction = f"You are an expert educational reading comprehension content creator. Return ONLY valid JSON in the requested format."

        # Define strict JSON Schema for the output
        response_schema = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_text": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "correct_option": {"type": "string"},
                            "solution_steps": {"type": "string"},
                            "explanation_description": {"type": "string"}
                        },
                        "required": ["question_text", "options", "correct_option", "solution_steps", "explanation_description"]
                    }
                }
            },
            "required": ["questions"]
        }

        # Call Gemini API
        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=response_schema
        )
        
        ai_response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=generation_config
        )

        generated_text = ai_response.text
        if not generated_text:
            raise Exception("Gemini returned an empty response.")

        parsed_data = json.loads(generated_text)
        generated_questions = parsed_data.get("questions", [])

        print("[INFO] Saving newly generated book quiz to Supabase...")
        
        # Check and Delete Existing
        existing_meta = supabase_db.table("library_quizzes").select("id").eq("grade", grade).eq("language", language).eq("book_title", book_name).execute()
        if existing_meta.data and len(existing_meta.data) > 0:
            existing_id = existing_meta.data[0]["id"]
            supabase_db.table("library_questions").delete().eq("library_quiz_id", existing_id).execute()
            supabase_db.table("library_quizzes").delete().eq("id", existing_id).execute()
            
        # Insert Quiz Metadata
        quiz_metadata = {
            "grade": grade,
            "language": language,
            "book_title": book_name
        }
        
        quiz_insert_response = supabase_db.table("library_quizzes").insert(quiz_metadata).execute()
        
        if not quiz_insert_response.data:
            raise Exception("Failed to save quiz metadata to Supabase.")
            
        new_quiz = quiz_insert_response.data[0]
        new_quiz_id = new_quiz["id"]

        # Prepare Questions payload
        questions_payload = []
        for q in generated_questions:
            questions_payload.append({
                "library_quiz_id": new_quiz_id,
                "question_text": q.get("question_text"),
                "options": q.get("options"),
                "correct_option": q.get("correct_option"),
                "explanation_description": q.get("explanation_description"),
                "marks": 1
            })

        # Bulk Insert Questions
        questions_insert_response = supabase_db.table("library_questions").insert(questions_payload).execute()
        
        if not questions_insert_response.data:
            raise Exception("Failed to save questions to Supabase.")

        new_quiz["questions"] = questions_payload
        new_quiz["quiz_id"] = new_quiz_id
        return new_quiz

    except Exception as e:
        error_msg = str(e)
        if "23505" in error_msg or "duplicate key" in error_msg.lower():
            print(f"[INFO] Concurrent insert detected for {book_name}. Fetching existing quiz.")
            existing_quiz = get_book_quiz_from_db(grade, language, book_name)
            if existing_quiz.get("success") is not False and "error" not in existing_quiz:
                return existing_quiz
                
        print(f"[FAIL] generate_and_save_book_quiz Error: {error_msg}".encode('ascii', 'replace').decode('ascii'))
        
        # Fallback if API key is exhausted
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("[INFO] API quota exceeded. Returning mock quiz.")
            return {
                "board": "Library",
                "grade": grade,
                "subject": "Library Book",
                "chapter_or_topic": book_name,
                "quiz_id": "mock-fallback-id",
                "success": True,
                "questions": [
                    {
                        "question_text": f"[API Exhausted Fallback] What happens when your Gemini API key runs out of credits while reading {book_name}?",
                        "options": ["App crashes", "Returns mock data", "Nothing", "I need to add a new key"],
                        "correct_option": "I need to add a new key",
                        "solution_steps": "Go to AI Studio to manage billing.",
                        "explanation_description": "Your API key prepayment credits are depleted.",
                        "marks": 1
                    }
                ]
            }
            
        return {"error": error_msg, "success": False}



def get_all_past_papers() -> dict:
    """
    Fetches all available past papers from Supabase.
    """
    try:
        response = supabase_db.table("past_papers").select("*").execute()
        return {"status": "success", "past_papers": response.data}
    except Exception as e:
        return {"error": str(e), "status": "error"}

def get_past_paper_from_db(past_paper_id: str) -> dict:
    """
    Fetches a specific past paper and its questions.
    """
    try:
        response = (
            supabase_db.table("past_papers")
            .select("id, board, grade, subject, year, past_paper_questions(question_text, question_type, difficulty_level, options, correct_option, solution_steps, explanation_description)")
            .eq("id", past_paper_id)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            existing_paper = response.data[0]
            if existing_paper.get("past_paper_questions") and len(existing_paper["past_paper_questions"]) > 0:
                existing_paper["questions"] = existing_paper["past_paper_questions"]
                del existing_paper["past_paper_questions"]
                existing_paper["quiz_id"] = existing_paper["id"]
                return existing_paper

                
        return {"error": "Past Paper not found", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

import os
def find_past_paper_pdf(subject: str, year: str) -> str:
    """
    Scans the 10thBooks/{subject} folder for a PDF filename containing the year.
    Returns the absolute path if found, otherwise None.
    """
    base_dir = r"f:\AbhirvaLearning\10thBooks"
    subject_dir = os.path.join(base_dir, subject)
    if not os.path.exists(subject_dir):
        return None
        
    for file in os.listdir(subject_dir):
        if file.lower().endswith('.pdf') and year in file:
            return os.path.join(subject_dir, file)
            
    return None

def generate_and_save_past_paper(board: str, grade: str, subject: str, year: str, num_questions: int = 10, exact_pdf_path: str = None) -> dict:
    """
    Forces generation of a new Past Paper via Gemini API and saves it to Supabase.
    """
    try:
        print(f"[INFO] Generating Past Paper via Gemini API for {board} | {grade} | {subject} | {year}...")
        
        pdf_path = exact_pdf_path if exact_pdf_path else find_past_paper_pdf(subject, year)
        contents = []
        uploaded_file = None
        
        if pdf_path:
            print(f"[INFO] Found local PDF for {year} {subject}. Using it for authentic extraction: {pdf_path}")
            uploaded_file = gemini_client.files.upload(file=pdf_path)
            contents.append(uploaded_file)
            
            prompt = f"""
            I have attached the exact {board} {grade}th Grade {subject} Board Exam paper from {year} as a PDF.
            Extract exactly {num_questions} real questions from this document.
            
            For each extracted question, assign a `difficulty_level` ('Easy', 'Medium', or 'Hard') that matches the rigor of the exam.
            
            If a question is an INTEGER-based question, the `question_type` MUST be "INTEGER", the `options` array MUST be empty, and the `correct_option` MUST be a pure number string.
            If a question is an MCQ, `question_type` MUST be "MCQ" and `options` MUST contain exactly 4 strings.
            
            Provide step-by-step solutions and a detailed explanation for why the answer is correct.
            """
        else:
            prompt = f"""
            Act as a strict, authentic CBSE Board Examiner.
            Simulate the exact {board} {grade}th Grade {subject} Board Exam paper from the year {year}.
            Generate exactly {num_questions} questions that perfectly mimic the style, verbiage, and difficulty of that specific historical past paper.
            
            For each question, assign a `difficulty_level` ('Easy', 'Medium', or 'Hard') that strictly matches the rigor of the {year} board exam.
            
            Since this is a simulated board exam, generate a mix of MCQ and INTEGER-based questions where appropriate for the subject.
            For INTEGER questions, the `question_type` MUST be "INTEGER", the `options` array MUST be empty, and the `correct_option` MUST be a pure number string.
            For MCQ questions, `question_type` MUST be "MCQ" and `options` MUST contain exactly 4 strings.
            
            Provide step-by-step solutions and a detailed explanation for why the answer is correct.
            """
            
        contents.append(prompt)

        system_instruction = f"You are an expert {board} educational content creator. Return ONLY valid JSON in the requested format."

        response_schema = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_text": {"type": "string"},
                            "question_type": {"type": "string"},
                            "difficulty_level": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "correct_option": {"type": "string"},
                            "solution_steps": {"type": "string"},
                            "explanation_description": {"type": "string"}
                        },
                        "required": ["question_text", "question_type", "difficulty_level", "options", "correct_option", "solution_steps", "explanation_description"]
                    }
                }
            },
            "required": ["questions"]
        }

        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=response_schema
        )
        
        ai_response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=generation_config
        )
        
        if uploaded_file:
            try:
                gemini_client.files.delete(name=uploaded_file.name)
            except Exception as e:
                print(f"[WARN] Failed to delete temporary file {uploaded_file.name}: {e}")

        generated_text = ai_response.text
        if not generated_text:
            raise Exception("Gemini returned an empty response.")

        parsed_data = json.loads(generated_text)
        generated_questions = parsed_data.get("questions", [])

        existing_meta = supabase_db.table("past_papers").select("id").eq("board", board).eq("grade", grade).eq("subject", subject).eq("year", year).execute()
        if existing_meta.data and len(existing_meta.data) > 0:
            existing_id = existing_meta.data[0]["id"]
            supabase_db.table("past_paper_questions").delete().eq("past_paper_id", existing_id).execute()
            supabase_db.table("past_papers").delete().eq("id", existing_id).execute()
            
        meta_payload = {
            "board": board,
            "grade": grade,
            "subject": subject,
            "year": year
        }
        meta_res = supabase_db.table("past_papers").insert(meta_payload).execute()
        
        if not meta_res.data:
            raise Exception("Failed to save past paper metadata.")
            
        new_id = meta_res.data[0]["id"]

        questions_payload = []
        for q in generated_questions:
            questions_payload.append({
                "past_paper_id": new_id,
                "question_text": q.get("question_text"),
                "question_type": q.get("question_type", "MCQ"),
                "difficulty_level": q.get("difficulty_level", "Medium"),
                "options": q.get("options", []),
                "correct_option": q.get("correct_option"),
                "solution_steps": q.get("solution_steps"),
                "explanation_description": q.get("explanation_description")
            })

        questions_insert_response = supabase_db.table("past_paper_questions").insert(questions_payload).execute()
        
        if not questions_insert_response.data:
            raise Exception("Failed to save past paper questions.")

        new_paper = meta_res.data[0]
        new_paper["questions"] = questions_payload
        new_paper["quiz_id"] = new_id
        return new_paper

    except Exception as e:
        return {"error": str(e), "success": False}
