"""
Utility functions for the Super Star Quiz App
Handles PDF/DOCX extraction, text processing, MCQ generation (PDF + Internet), and test saving
"""

import json
import os
import random
import re
from datetime import datetime

import PyPDF2
from docx import Document
from groq import Groq
from dotenv import load_dotenv

# Model to use
MODEL_NAME = "llama-3.1-8b-instant"

def get_groq_client():
    """Get a fresh Groq client using the current environment variables or Streamlit secrets."""
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            pass
            
    if not api_key:
        return None
        
    return Groq(api_key=api_key)

# Directory to save tests
SAVED_TESTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_tests")
os.makedirs(SAVED_TESTS_DIR, exist_ok=True)


import tempfile

def clean_extracted_text(text: str) -> str:
    """
    Cleans extracted PDF text by removing non-alphanumeric/garbage wingdings
    that confuse the LLM and break JSON output.
    Keeps English, basic punctuation, newlines, and Devanagari (Marathi/Hindi).
    """
    # Keep alphanumeric, whitespace, basic punctuation, and Devanagari (\u0900-\u097F)
    cleaned = re.sub(r'[^\w\s\.,;:\'\"\-\(\)\?!\u0900-\u097F]', ' ', text)
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned)
    return cleaned

def extract_text_from_pdf(pdf_file, start_page: int = None, end_page: int = None) -> str:
    """Extract text from a PDF file."""
    try:
        if isinstance(pdf_file, str):
            reader = PyPDF2.PdfReader(pdf_file)
        else:
            reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        total_pages = len(reader.pages)
        
        start_idx = max(0, start_page - 1) if start_page is not None else 0
        end_idx = min(total_pages, end_page) if end_page is not None else total_pages
        
        for i in range(start_idx, end_idx):
            extracted = reader.pages[i].extract_text()
            if extracted:
                text += extracted + "\n"
                
        return clean_extracted_text(text)
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


def extract_text_from_docx(docx_file) -> str:
    """
    Extract text from a DOCX file.
    
    Args:
        docx_file: File object or path to DOCX file
        
    Returns:
        str: Extracted text from the DOCX
    """
    try:
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading DOCX file: {str(e)}")


def extract_text_from_all_pdfs_in_folder(folder_path: str) -> str:
    """
    Extract and combine text from all PDF files in a given folder.
    
    Args:
        folder_path: Path to the folder containing PDF files
        
    Returns:
        str: Combined extracted text from all PDFs
    """
    combined_text = ""
    if not os.path.exists(folder_path):
        return combined_text
    
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(folder_path, filename)
            try:
                text = extract_text_from_pdf(filepath)
                if text:
                    combined_text += f"\n\n--- Content from {filename} ---\n{text}"
            except Exception:
                continue  # Skip files that can't be read
    
    return combined_text.strip()


def analyze_difficulty_from_paper(text: str) -> str:
    """
    Analyze a previous exam paper to extract difficulty characteristics like 
    vocabulary level, question complexity, and response style.
    """
    if not text or len(text.strip()) == 0:
        return ""
        
    client = get_groq_client()
    if not client:
        return ""
        
    try:
        prompt = f"You are an educational consultant. Analyze the provided exam paper and describe its difficulty level, typical question structure, vocabulary complexity, and the depth of knowledge required. Provide a concise summary that can be used to generate similar questions.\n\nAnalyze the difficulty of this exam paper:\n\n{text[:4000]}"
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def generate_mcqs_from_pdf_text(text: str, topic: str = "", num_questions: int = 15, level: str = "8-year-old children", difficulty_context: str = "") -> list:
    """
    Generate multiple-choice questions from PDF/document text using Groq API.
    
    Args:
        text (str): The text content to generate questions from
        topic (str): The topic of the quiz
        num_questions (int): Number of questions to generate (default: 15)
        level (str): The difficulty level/target audience (default: "8-year-old children")
        difficulty_context (str): Context for question generation
        
    Returns:
        list: List of dictionaries containing question, options, correct answer, and source
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("No text provided to generate questions")
    
    client = get_groq_client()
    if not client:
        raise Exception("Groq API key not found. Please add it to the .env file.")
    
    # Use more text for better coverage
    text = text[:120000]
    
    import time
    all_mcqs = []
    questions_remaining = num_questions
    batch_size = 10
    
    previous_questions_text = ""
    
    while questions_remaining > 0:
        current_batch = min(batch_size, questions_remaining)
        
        # Determine language based on topic
        lang_instruction = "ALL QUESTIONS, OPTIONS, AND ANSWERS MUST BE WRITTEN IN MARATHI (DEVANAGARI SCRIPT)." if "marathi" in topic.lower() else ""

        prompt = f"""You are an expert quiz creator for {level}. 
Your task is to create exactly {current_batch} multiple-choice questions based STRICTLY on the following text content.

Important guidelines:
- Use language and concepts suitable for {level}
- Make questions fun and engaging
- Focus on the actual academic/story content
- Ensure all 4 options are plausible but only one is correct
- CRITICAL: All 4 options MUST be completely distinct entities. DO NOT use synonyms, alternate spellings, or different titles for the same person/thing as separate options (e.g., do not use both "डॉ. अंबेडकर" and "डॉ. बाबासाहेब आंबेडकर", or "शिवाजी महाराज" and "छत्रपती शिवाजी").
- Avoid tricky or misleading questions
- Include diverse question types (factual, understanding, application)
- {lang_instruction}

{f"CRITICAL INSTRUCTION - DO NOT REPEAT ANY OF THESE PREVIOUSLY GENERATED QUESTIONS:\n{previous_questions_text}\n" if previous_questions_text else ""}

Text to create questions from:
{text}

Additional Difficulty Context (if provided):
{difficulty_context if difficulty_context else f"Target level is {level}"}

Generate exactly {current_batch} questions. Return ONLY a valid JSON object with a single key "mcqs" containing an array of questions, with this exact structure:
{{
  "mcqs": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "source": "pdf"
    }}
  ]
}}

Ensure:
1. CRITICAL: The exact string value of 'correct_answer' MUST be identically present inside the 'options' array. Do not use synonyms. Copy the exact text.
2. All 4 options are completely different.
3. Return ONLY the JSON object, no other text
4. The JSON must be valid and parseable
5. Each question must have "source": "pdf" """
        
        try:
            full_prompt = f"System: You are a helpful quiz creation assistant for children. You generate questions strictly from the provided text.\n\nUser: {prompt}"
            
            # If we are doing a second batch, sleep for 60 seconds to avoid the 6000 TPM limit of the 8B model!
            if len(all_mcqs) > 0:
                print("Waiting 60 seconds to bypass Groq 6000 TPM rate limit...")
                time.sleep(60)
                
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            # Clean up potential markdown blocks from LLMs
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            mcqs = _parse_mcq_response(response_text)
            
            # Format questions nicely before adding
            import random
            for mcq in mcqs:
                if 'options' in mcq and isinstance(mcq['options'], dict):
                    mcq['options'] = list(mcq['options'].values())
                if 'correct_answer' not in mcq and 'answer' in mcq:
                    mcq['correct_answer'] = mcq['answer']
                
                # SAFETY NET: Ensure the correct_answer is actually in the options array!
                if 'correct_answer' in mcq and 'options' in mcq and isinstance(mcq['options'], list):
                    if mcq['correct_answer'] not in mcq['options']:
                        if len(mcq['options']) > 0:
                            # Replace a random option with the exact correct_answer to make it clickable
                            replace_idx = random.randint(0, len(mcq['options']) - 1)
                            mcq['options'][replace_idx] = mcq['correct_answer']
                            
                # Ensure source field
                mcq["source"] = "pdf"
            
            all_mcqs.extend(mcqs)
            
            # Update previous questions text so the AI knows what to avoid repeating
            for mcq in mcqs:
                previous_questions_text += f"- {mcq.get('question', '')}\n"
                
            if len(mcqs) == 0:
                break
                
            questions_remaining -= len(mcqs)
            
        except Exception as e:
            # Stop generation if we encounter an error, maybe we already have some questions
            error_msg = f"Error generating PDF batch: {e}"
            print(error_msg)
            import traceback
            with open(r"f:\AbhirvaLearning\debug_utils_error.txt", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            break
            
    return all_mcqs[:num_questions]


def generate_mcqs_from_internet(topic: str, num_questions: int = 10, level: str = "8-year-old children", difficulty_context: str = "") -> list:

    """
    Generate multiple-choice questions by searching the internet for the topic.
    Uses OpenAI's web search capability to find current information.
    Falls back to model knowledge if web search is unavailable.
    
    Args:
        topic (str): The topic to search the internet for
        num_questions (int): Number of questions to generate (default: 10)
        level (str): The difficulty level/target audience (default: "8-year-old children")
        
    Returns:
        list: List of dictionaries containing question, options, correct answer, and source
    """
    if not topic or len(topic.strip()) == 0:
        raise ValueError("No topic provided for internet-based questions")
    
    research_text = ""
    web_search_used = False
    
    client = get_groq_client()
    if not client:
        raise Exception("Groq API key not found. Please add it to the .env file.")
        
    # Step 1: Use Groq to gather knowledge
    try:
        research_prompt = (
            f"You are a knowledgeable research assistant. Provide detailed, accurate, and comprehensive "
            f"information about: {topic}. Include interesting facts, key details, important figures, "
            f"dates, and educational content suitable for {level}."
        )
        research_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": research_prompt}],
            temperature=0.5,
            max_tokens=2000
        )
        research_text = research_response.choices[0].message.content.strip()
        web_search_used = True
    except Exception:
        # Fallback
        research_text = topic
        
    # Step 2: Generate MCQs from the researched content in batches
    search_note = "from internet research" if web_search_used else "about this topic using your broad knowledge"
    
    import time
    all_mcqs = []
    questions_remaining = num_questions
    batch_size = 10
    
    previous_questions_text = ""
    
    while questions_remaining > 0:
        current_batch = min(batch_size, questions_remaining)
        
        # Determine language based on topic
        lang_instruction = "ALL QUESTIONS, OPTIONS, AND ANSWERS MUST BE WRITTEN IN MARATHI (DEVANAGARI SCRIPT)." if "marathi" in topic.lower() else ""
        
        prompt = f"""You are an expert quiz creator for {level}.
Your task is to create exactly {current_batch} multiple-choice questions {search_note} about: "{topic}"

Here is the information gathered:
{research_text[:6000]}

Additional Difficulty Context (if provided):
{difficulty_context if difficulty_context else f"Target level is {level}"}

Important guidelines:
- Use language and concepts suitable for {level}
- Make questions fun and engaging
- Ensure all 4 options are plausible but only one is correct
- CRITICAL: All 4 options MUST be completely distinct entities. DO NOT use synonyms, alternate spellings, or different titles for the same person/thing as separate options.
- Avoid tricky or misleading questions
- Include diverse question types (factual, understanding, application)
- Make sure the content is educational and age-appropriate for {level}
- Include interesting and surprising facts to make learning fun
- {lang_instruction}

{f"CRITICAL INSTRUCTION - DO NOT REPEAT ANY OF THESE PREVIOUSLY GENERATED QUESTIONS:\n{previous_questions_text}\n" if previous_questions_text else ""}

Generate exactly {current_batch} questions. Return ONLY a valid JSON object with a single key "mcqs" containing an array of questions, with this exact structure:
{{
  "mcqs": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "source": "internet"
    }}
  ]
}}

Ensure:
1. CRITICAL: The exact string value of 'correct_answer' MUST be identically present inside the 'options' array. Do not use synonyms. Copy the exact text.
2. All 4 options are completely different.
3. Return ONLY the JSON object, no other text
4. The JSON must be valid and parseable
5. Each question must have "source": "internet" """
        
        try:
            full_prompt = f"System: You are a knowledgeable quiz creation assistant. You generate interesting questions about specific topics.\n\nUser: {prompt}"
            
            # If we are doing a second batch, sleep for 60 seconds to avoid the 6000 TPM limit of the 8B model!
            if len(all_mcqs) > 0:
                print("Waiting 60 seconds to bypass Groq 6000 TPM rate limit...")
                time.sleep(60)
                
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            
            mcqs = _parse_mcq_response(response_text)
            
            # Format questions nicely before adding
            import random
            for mcq in mcqs:
                if 'options' in mcq and isinstance(mcq['options'], dict):
                    mcq['options'] = list(mcq['options'].values())
                if 'correct_answer' not in mcq and 'answer' in mcq:
                    mcq['correct_answer'] = mcq['answer']
                    
                # SAFETY NET: Ensure the correct_answer is actually in the options array!
                if 'correct_answer' in mcq and 'options' in mcq and isinstance(mcq['options'], list):
                    if mcq['correct_answer'] not in mcq['options']:
                        if len(mcq['options']) > 0:
                            # Replace a random option with the exact correct_answer to make it clickable
                            replace_idx = random.randint(0, len(mcq['options']) - 1)
                            mcq['options'][replace_idx] = mcq['correct_answer']
                            
                mcq["source"] = "internet"
            
            all_mcqs.extend(mcqs)
            
            # Update previous questions text so the AI knows what to avoid repeating
            for mcq in mcqs:
                previous_questions_text += f"- {mcq.get('question', '')}\n"
                
            if len(mcqs) == 0:
                break
                
            questions_remaining -= len(mcqs)
            
        except Exception as e:
            error_msg = f"Error generating internet-based MCQs batch: {e}"
            print(error_msg)
            import traceback
            with open(r"f:\AbhirvaLearning\debug_utils_error.txt", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            break
            
    return all_mcqs[:num_questions]


def generate_full_quiz(
    pdf_text: str, 
    topic: str, 
    level: str = "8-year-old children",
    pdf_count: int = 0,
    prompt_count: int = 0,
    internet_count: int = 0,
    difficulty_context: str = "",
    inspiring_pdf_text: str = "",
    inspiring_pdf_count: int = 0,
    continent_pdf_text: str = "",
    continent_pdf_count: int = 0,
    topic2: str = "",
    prompt2_count: int = 0,
    prompt_level: str = "2nd Grade Student",
    prompt2_level: str = "2nd Grade Student",
    primary_prompt_context: str = "",
    secondary_prompt_context: str = "",
) -> list:
    """
    Generate a full quiz with customizable question distribution and difficulty.
    
    Args:
        pdf_text (str): Text extracted from PDFs
        topic (str): User provided topic/prompt
        level (str): Grade/difficulty level
        pdf_count (int): Number of questions from PDF content
        prompt_count (int): Number of questions from Topic Prompt
        internet_count (int): Number of questions from Internet research
        difficulty_context (str): Context from a reference paper to match difficulty
        primary_prompt_context (str): Difficulty context for primary prompt questions
        secondary_prompt_context (str): Difficulty context for secondary prompt questions
    """
    all_mcqs = []
    
    # 1. Questions from PDF
    if pdf_text and pdf_count > 0:
        try:
            pdf_mcqs = generate_mcqs_from_pdf_text(
                text=pdf_text,
                topic=topic,
                num_questions=pdf_count,
                level=level,
                difficulty_context=difficulty_context
            )
            all_mcqs.extend(pdf_mcqs)
        except Exception as e:
            print(f"Error generating PDF questions: {e}")

    # 1b. Questions from Inspiring Personality PDF
    if inspiring_pdf_count > 0 and inspiring_pdf_text and inspiring_pdf_text.strip():
        try:
            pers_mcqs = generate_mcqs_from_pdf_text(
                inspiring_pdf_text, 
                num_questions=inspiring_pdf_count, 
                level=level, 
                difficulty_context=difficulty_context
            )
            for mcq in pers_mcqs:
                mcq["category"] = "Inspiring Personality"
            all_mcqs.extend(pers_mcqs)
        except Exception as e:
            print(f"Error generating Inspiring Personality PDF questions: {e}")

    # 1c. Questions from Continent PDF
    if continent_pdf_count > 0 and continent_pdf_text and continent_pdf_text.strip():
        try:
            cont_mcqs = generate_mcqs_from_pdf_text(
                continent_pdf_text, 
                num_questions=continent_pdf_count, 
                level=level, 
                difficulty_context=difficulty_context
            )
            for mcq in cont_mcqs:
                mcq["category"] = "Continent & Ocean"
            all_mcqs.extend(cont_mcqs)
        except Exception as e:
            print(f"Error generating Continent PDF questions: {e}")

    # 2. Questions from Prompt (Internet research on specific topic)
    if prompt_count > 0 and topic:
        try:
            prompt_mcqs = generate_mcqs_from_internet(
                topic, 
                num_questions=prompt_count, 
                level=prompt_level, 
                difficulty_context=primary_prompt_context
            )
            for mcq in prompt_mcqs:
                mcq["source"] = "topic_prompt"
            all_mcqs.extend(prompt_mcqs)
        except Exception as e:
            print(f"Error generating prompt questions: {e}")

    # 2b. Questions from Secondary Prompt (topic2)
    if prompt2_count > 0 and topic2:
        try:
            prompt2_mcqs = generate_mcqs_from_internet(
                topic2, 
                num_questions=prompt2_count, 
                level=prompt2_level, 
                difficulty_context=secondary_prompt_context
            )
            for mcq in prompt2_mcqs:
                mcq["source"] = "topic_prompt"
            all_mcqs.extend(prompt2_mcqs)
        except Exception as e:
            print(f"Error generating secondary prompt questions: {e}")

    # 3. Questions from Internet
    if internet_count > 0:
        try:
            cont_count = (internet_count + 1) // 2
            pers_count = internet_count // 2
            
            if cont_count > 0:
                cont_mcqs = generate_mcqs_from_internet(
                    "Continents and Oceans of the World", 
                    num_questions=cont_count, 
                    level=level, 
                    difficulty_context=difficulty_context
                )
                for mcq in cont_mcqs:
                    mcq["category"] = "Continent & Ocean"
                all_mcqs.extend(cont_mcqs)
                
            if pers_count > 0:
                pers_mcqs = generate_mcqs_from_internet(
                    "Inspiring Personalities and Famous Figures in History", 
                    num_questions=pers_count, 
                    level=level, 
                    difficulty_context=difficulty_context
                )
                for mcq in pers_mcqs:
                    mcq["category"] = "Inspiring Personality"
                all_mcqs.extend(pers_mcqs)
        except Exception as e:
            print(f"Error generating internet questions: {e}")
    
    # Shuffle all questions
    random.shuffle(all_mcqs)
    
    # Shuffle options within each question so the correct answer isn't always in the same position
    for mcq in all_mcqs:
        random.shuffle(mcq['options'])
    
    return all_mcqs




def _extract_topic_from_text(text: str) -> str:
    """Extract a topic/summary from the given text using OpenAI."""
    client = get_groq_client()
    if not client:
        raise Exception("Groq API key not found. Please add it to the .env file.")
        
    try:
        prompt = f"Extract the main topic or subject from the given text. Return only the topic name, nothing else.\n\nWhat is the main topic of this text?\n\n{text[:2000]}"
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "General Knowledge for Kids"


def _parse_mcq_response(response_text: str) -> list:
    """Parse MCQ JSON response from the API."""
    try:
        data = json.loads(response_text)
        if isinstance(data, dict) and "mcqs" in data:
            mcqs = data["mcqs"]
        elif isinstance(data, list):
            mcqs = data
        else:
            raise ValueError("Invalid JSON format")
    except json.JSONDecodeError:
        # Try to extract JSON from the response if it has extra text
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            mcqs = json.loads(json_match.group())
        else:
            raise ValueError("Could not parse MCQs from API response")
    return mcqs


def _validate_mcqs(mcqs: list):
    """Validate MCQ list structure."""
    if not isinstance(mcqs, list) or len(mcqs) == 0:
        raise ValueError("Invalid MCQ format returned")
    
    for mcq in mcqs:
        if not all(key in mcq for key in ['question', 'options', 'correct_answer']):
            raise ValueError("Missing required fields in MCQ")
        if len(mcq['options']) != 4:
            raise ValueError("Each question must have exactly 4 options")
        if mcq['correct_answer'] not in mcq['options']:
            raise ValueError("Correct answer must be one of the options")


def generate_mcqs_from_text(text: str, num_questions: int = 5) -> list:
    """
    Legacy function - Generate MCQs from text (kept for backward compatibility).
    Now uses gpt-4.1-mini model.
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("No text provided to generate questions")
    
    text = text[:100000]
    
    # Determine language based on topic
    lang_instruction = "ALL QUESTIONS, OPTIONS, AND ANSWERS MUST BE WRITTEN IN MARATHI (DEVANAGARI SCRIPT)." if "marathi" in topic.lower() else ""

    prompt = f"""You are an expert quiz creator. 
Generate exactly {num_questions} multiple-choice questions about '{topic}'.

Target audience: {level}
Difficulty Context: {difficulty_context}

Important guidelines:
- Make questions accurate and educational
- Ensure all 4 options are plausible but only one is correct
- Make sure the content is age-appropriate
{lang_instruction}

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Correct option text here"
  }}
]

Ensure:
1. The correct_answer must exactly match one of the options
2. All options are different and meaningful
3. Return ONLY the JSON array, no other text
4. The JSON must be valid and parseable"""

    client = get_client()
    if not client:
        raise Exception("OpenAI API key not found. Please add it to the .env file.")
        
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful quiz creation assistant for children."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        response_text = response.choices[0].message.content.strip()
        mcqs = _parse_mcq_response(response_text)
        _validate_mcqs(mcqs)
        return mcqs
    
    except Exception as e:
        raise Exception(f"Error generating MCQs: {str(e)}")


def calculate_score(user_answers: list, correct_answers: list) -> tuple:
    """
    Calculate quiz score and return score details.
    
    Args:
        user_answers (list): List of user's answers
        correct_answers (list): List of correct answers
        
    Returns:
        tuple: (total_questions, correct_count, percentage)
    """
    if len(user_answers) != len(correct_answers):
        raise ValueError("Answer lists must have the same length")
    
    correct_count = sum(1 for user, correct in zip(user_answers, correct_answers) 
                       if user == correct)
    total = len(correct_answers)
    percentage = (correct_count / total) * 100 if total > 0 else 0
    
    return total, correct_count, percentage


def save_test(test_data: dict) -> str:
    """
    Save a completed test to a JSON file.
    
    Args:
        test_data (dict): Dictionary containing test details:
            - topic: str
            - mcqs: list of MCQ dicts
            - user_answers: dict of user answers
            - score: dict with total, correct, percentage
            - timestamp: str
            - pdf_files: list of PDF file names used
            
    Returns:
        str: Path to the saved test file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic_slug = re.sub(r'[^\w\s-]', '', test_data.get('topic', 'quiz')).strip().replace(' ', '_')[:30]
    filename = f"test_{topic_slug}_{timestamp}.json"
    filepath = os.path.join(SAVED_TESTS_DIR, filename)
    
    # Prepare save data
    save_data = {
        "test_id": f"{topic_slug}_{timestamp}",
        "topic": test_data.get("topic", ""),
        "timestamp": datetime.now().isoformat(),
        "date_readable": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "pdf_files_used": test_data.get("pdf_files", []),
        "total_questions": len(test_data.get("mcqs", [])),
        "pdf_questions_count": sum(1 for q in test_data.get("mcqs", []) if q.get("source") == "pdf"),
        "internet_questions_count": sum(1 for q in test_data.get("mcqs", []) if q.get("source") == "internet"),
        "prompt_questions_count": sum(1 for q in test_data.get("mcqs", []) if q.get("source") == "topic_prompt"),
        "score": test_data.get("score", {}),
        "questions": []
    }
    
    # Add question details
    mcqs = test_data.get("mcqs", [])
    user_answers = test_data.get("user_answers", {})
    
    for i, mcq in enumerate(mcqs):
        user_answer = user_answers.get(i, "Not answered")
        is_correct = user_answer == mcq.get("correct_answer", "")
        
        save_data["questions"].append({
            "number": i + 1,
            "question": mcq.get("question", ""),
            "options": mcq.get("options", []),
            "correct_answer": mcq.get("correct_answer", ""),
            "user_answer": user_answer,
            "is_correct": is_correct,
            "source": mcq.get("source", "unknown")
        })
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    return filepath


def load_saved_tests() -> list:
    """
    Load all saved tests from the saved_tests directory.
    
    Returns:
        list: List of test data dictionaries, sorted by timestamp (newest first)
    """
    tests = []
    
    if not os.path.exists(SAVED_TESTS_DIR):
        return tests
    
    for filename in os.listdir(SAVED_TESTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(SAVED_TESTS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    test_data = json.load(f)
                    test_data["_filename"] = filename
                    tests.append(test_data)
            except Exception:
                continue
    
    # Sort by timestamp (newest first)
    tests.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return tests


def delete_saved_test(filename: str) -> bool:
    """
    Delete a saved test file.
    
    Args:
        filename: Name of the test file to delete
        
    Returns:
        bool: True if deleted successfully
    """
    filepath = os.path.join(SAVED_TESTS_DIR, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False
