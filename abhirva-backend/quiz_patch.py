                
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

def generate_and_save_past_paper(board: str, grade: str, subject: str, year: str, num_questions: int = 10) -> dict:
    """
    Forces generation of a new Past Paper via Gemini API and saves it to Supabase.
    """
    try:
        print(f"[INFO] Generating Past Paper via Gemini API for {board} | {grade} | {subject} | {year}...")
        
        pdf_path = find_past_paper_pdf(subject, year)
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
