"""
Super Star Quiz App - Main Application
A fun, colorful, kid-friendly quiz application using Streamlit and Groq LLaMA 3
Generates 25 questions: 15 from PDF + 10 from Internet
"""

import streamlit as st
from streamlit_option_menu import option_menu
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_all_pdfs_in_folder,
    generate_full_quiz,
    generate_mcqs_from_text,
    calculate_score,
    save_test,
    load_saved_tests,
    delete_saved_test,
    analyze_difficulty_from_paper,
    SAVED_TESTS_DIR,
)
from english_improvement import display_english_improvement, display_memory_games


# Load environment variables
load_dotenv(override=True)

import database as db
db.init_db()

# Test folder path (contains PDF files)
TEST_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")

# Page configuration
st.set_page_config(
    page_title="BrainyBee Kids Learning",
    page_icon="assets/logo.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for kid-friendly styling
st.markdown("""
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main background and text styles */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
    }
    
    /* Center content */
    .block-container {
        max-width: 850px;
        padding: 2rem 1rem;
        margin: 0 auto;
    }
    
    /* BrainyBee Logo Animation */
    .logo-container { text-align: center; margin-bottom: 2rem; margin-top: 1rem; }
    .bee-logo-anim {
        font-size: 5rem;
        display: inline-block;
        animation: flyBee 4s ease-in-out infinite;
        text-shadow: 2px 4px 10px rgba(0,0,0,0.3);
    }
    @keyframes flyBee {
        0%, 100% { transform: translateY(0) rotate(-5deg); }
        50% { transform: translateY(-15px) rotate(5deg) scale(1.1); }
    }
    .logo-text {
        font-size: 3.5rem;
        font-weight: 900;
        text-shadow: 2px 3px 6px rgba(0,0,0,0.4);
        font-family: 'Outfit', sans-serif;
        letter-spacing: 1px;
        margin-top: -10px;
        background: linear-gradient(45deg, #FFD700, #ff8c00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .logo-subtext {
        font-size: 1.2rem;
        font-weight: 700;
        color: white;
        letter-spacing: 5px;
        text-transform: uppercase;
        margin-top: 5px;
        opacity: 0.9;
    }
    
    /* Title styling */
    h1 {
        text-align: center;
        color: #FFD700;
        font-size: 3em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 1.5rem;
        font-weight: 800;
        font-family: 'Outfit', sans-serif;
    }
    
    h2 {
        color: #FFD700;
        text-align: center;
        font-size: 2em;
        margin-top: 1.5rem;
        font-family: 'Outfit', sans-serif;
    }
    
    h3 {
        color: #FFF;
        font-size: 1.3em;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Card styling for questions */
    .question-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(245,245,255,0.95) 100%);
        border-radius: 18px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        color: #333;
        border-left: 5px solid #667eea;
        transition: transform 0.2s ease;
    }
    
    .question-card:hover {
        transform: translateY(-2px);
    }
    
    /* Source badge */
    .source-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75em;
        font-weight: 600;
        margin-top: 8px;
        letter-spacing: 0.5px;
    }
    
    .source-pdf {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .source-internet {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
    }
    
    .source-topic_prompt {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: white;
    }
    
    /* Button styling */
    button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-size: 1.1em;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Outfit', sans-serif;
    }
    
    button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Input field styling */
    input, textarea {
        border-radius: 10px;
        border: 2px solid #FFD700;
        padding: 0.8rem;
        font-size: 1.1em;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Result styling */
    .result-box {
        background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(245,245,255,0.95) 100%);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        color: #333;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    }
    
    .score-text {
        font-size: 2em;
        font-weight: bold;
        color: #667eea;
        font-family: 'Outfit', sans-serif;
    }
    
    .star-display {
        font-size: 3em;
        margin: 1rem 0;
        letter-spacing: 0.2em;
    }
    
    .balloon {
        font-size: 2em;
        animation: float 3s ease-in-out infinite;
        display: inline-block;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    /* Progress bar */
    .progress-text {
        font-size: 1.2em;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        margin: 1rem 0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Radio button styling */
    [type="radio"] {
        accent-color: #667eea;
        width: 20px;
        height: 20px;
    }
    
    /* Success message */
    .success-message {
        color: #2ecc71;
        font-size: 1.3em;
        font-weight: bold;
        text-align: center;
    }
    
    /* Info message */
    .info-message {
        color: #3498db;
        font-size: 1.1em;
        text-align: center;
    }
    
    /* Encouragement styling */
    .encouragement {
        color: #FFD700;
        font-size: 1.5em;
        text-align: center;
        font-weight: bold;
        margin: 1.5rem 0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Saved test card */
    .saved-test-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,240,255,0.9) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        color: #333;
        border-left: 4px solid #FFD700;
        transition: all 0.3s ease;
    }
    
    .saved-test-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    /* Quiz info banner */
    .quiz-info-banner {
        background: linear-gradient(135deg, rgba(255,215,0,0.15) 0%, rgba(255,215,0,0.05) 100%);
        border: 2px solid rgba(255,215,0,0.3);
        border-radius: 15px;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
        text-align: center;
        color: #FFD700;
        font-weight: 600;
    }
    
    /* PDF list */
    .pdf-list-item {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        margin: 0.3rem 0;
        color: #fff;
        font-size: 0.95em;
    }
    
    /* Model badge */
    .model-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00d2ff, #3a7bd5);
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
        margin: 0.5rem auto;
        text-align: center;
    }
    
    /* Answer feedback styles */
    .feedback-correct {
        background: linear-gradient(135deg, rgba(46, 204, 113, 0.15) 0%, rgba(46, 204, 113, 0.05) 100%);
        border: 2px solid rgba(46, 204, 113, 0.5);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        color: #27ae60;
        font-weight: 600;
        font-size: 1.1em;
        animation: fadeIn 0.3s ease;
    }
    
    .feedback-wrong {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.15) 0%, rgba(231, 76, 60, 0.05) 100%);
        border: 2px solid rgba(231, 76, 60, 0.5);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        color: #e74c3c;
        font-weight: 600;
        font-size: 1.1em;
        animation: fadeIn 0.3s ease;
    }
    
    .correct-answer-reveal {
        background: linear-gradient(135deg, rgba(52, 152, 219, 0.15) 0%, rgba(52, 152, 219, 0.05) 100%);
        border: 2px solid rgba(52, 152, 219, 0.4);
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin-top: 0.5rem;
        color: #2980b9;
        font-weight: 500;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

if "total_stars" not in st.session_state:
    st.session_state.total_stars = 0

if "quiz_generated" not in st.session_state:
    st.session_state.quiz_generated = False

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0

if "quiz_format" not in st.session_state:
    st.session_state.quiz_format = None

if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

if "pdf_files_used" not in st.session_state:
    st.session_state.pdf_files_used = []

if "test_saved" not in st.session_state:
    st.session_state.test_saved = False

if "active_page" not in st.session_state:
    st.session_state.active_page = "quiz"

if "answered_questions" not in st.session_state:
    st.session_state.answered_questions = set()

if "default_tab_index" not in st.session_state:
    st.session_state.default_tab_index = 0


def display_header():
    """Display the app header with title and total stars"""
    
    # Use GitHub Raw URL to absolutely guarantee it loads correctly on Streamlit Cloud
    img_url = "https://raw.githubusercontent.com/DineshTech007/BrainyBeeQuiz/main/assets/smiling_pointing_bee_transparent.png"
    img_html = f'<img class="hovering-bee" src="{img_url}">'

    html_code = """<style>
.header-wrapper {
position: relative;
display: flex;
flex-direction: row;
justify-content: center;
align-items: center;
height: 180px;
margin-bottom: 2rem;
margin-top: 1rem;
overflow: visible;
}
.logo-text-container {
display: flex;
flex-direction: column;
justify-content: center;
text-align: center;
z-index: 5;
background: rgba(102, 126, 234, 0.1);
padding: 10px 40px;
border-radius: 20px;
backdrop-filter: blur(5px);
}
@keyframes flyInRight {
0% { transform: translate(50vw, 0px) scale(0.8); opacity: 0; }
100% { transform: translate(0, 0) scale(1); opacity: 1; }
}
@keyframes hoverSmooth {
0% { transform: translateY(-12px); }
50% { transform: translateY(12px); }
100% { transform: translateY(-12px); }
}
.flying-in-container {
position: absolute;
left: 50%;
margin-left: 140px;
animation: flyInRight 4s ease-out forwards;
z-index: 6;
}
.hovering-bee {
width: 230px;
animation: hoverSmooth 2.5s ease-in-out infinite;
filter: drop-shadow(0 8px 12px rgba(0,0,0,0.4));
}

@media (max-width: 768px) {
    .header-wrapper {
        flex-direction: row;
        height: 120px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .flying-in-container {
        position: relative;
        left: auto;
        margin-left: 10px;
        margin-bottom: 0px;
    }
    .hovering-bee {
        width: 130px; /* Medium size on mobile */
    }
    .logo-text-container {
        padding: 10px 15px;
    }
}
</style>
<div class="header-wrapper">
<div class="logo-text-container">
<div class="logo-text" style="line-height: 1.1; margin:0;">BrainyBee</div>
<div class="logo-subtext" style="margin-top: 0;">Kids Learning</div>
</div>
<div class="flying-in-container">
""" + img_html + """
</div>
</div>
"""
    st.markdown(html_code, unsafe_allow_html=True)

    
    if st.session_state.user:
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown(f"<div class='progress-text'> {st.session_state.user['username']}'s Stars: {st.session_state.total_stars}</div>", 
                        unsafe_allow_html=True)
            with st.expander(" View Global Leaderboard"):
                leaders = db.get_global_leaderboard()
                if not leaders:
                    st.info("No players yet. Be the first to earn stars!")
                else:
                    for i, (uname, stars) in enumerate(leaders):
                        medal = "" if i == 0 else "" if i == 1 else "" if i == 2 else ""
                        st.markdown(f"<div style='background:rgba(255,255,255,0.1); padding:0.8rem; margin:0.3rem 0; border-radius:10px;'>{medal} <strong>{uname}</strong>: {stars} Stars</div>", unsafe_allow_html=True)
        with col3:
            if st.button(" Logout", key="logout_btn"):
                st.session_state.user = None
                st.rerun()
                
    st.markdown("<div style='text-align:center;'><span class='model-badge'> Powered by Advanced AI</span></div>", 
                unsafe_allow_html=True)


def get_pdf_files_in_test_folder():
    """Get list of PDF files in the test folder"""
    pdf_files = []
    if os.path.exists(TEST_FOLDER):
        for f in sorted(os.listdir(TEST_FOLDER)):
            if f.lower().endswith(".pdf"):
                pdf_files.append(f)
    return pdf_files


def get_text_from_files(uploaded_files):
    """Extract and combine text from uploaded files"""
    combined_text = ""
    
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = extract_text_from_docx(uploaded_file)
            else:
                st.warning(f"Unsupported file format: {uploaded_file.name}")
                continue
            
            if text:
                combined_text += f"\n\n--- Content from {uploaded_file.name} ---\n{text}"
        
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    return combined_text.strip()


def display_quiz_questions():
    """Display quiz questions one at a time with instant feedback"""
    if not st.session_state.mcqs:
        st.error("No questions to display. Please generate a quiz first.")
        return
    
    st.markdown("<h2> Answer the Questions</h2>", unsafe_allow_html=True)
    
    # Quiz info
    total_q = len(st.session_state.mcqs)
    pdf_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "pdf")
    net_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "internet")
    prompt_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "topic_prompt")
    answered_count = len(st.session_state.answered_questions)
    
    source_info = f" PDF: {pdf_q} | " if pdf_q > 0 else ""
    source_info += f" Prompt: {prompt_q} | " if prompt_q > 0 else ""
    source_info += f" Internet: {net_q}"
    
    st.markdown(f"""
        <div class='quiz-info-banner'>
             Total: {total_q} Questions | {source_info} |  Answered: {answered_count}/{total_q}
        </div>
    """, unsafe_allow_html=True)
    
    # Progress indicator
    progress = (st.session_state.current_question_index + 1) / len(st.session_state.mcqs)
    st.progress(progress)
    st.markdown(f"<div class='progress-text'>Question {st.session_state.current_question_index + 1} of {len(st.session_state.mcqs)}</div>", 
                unsafe_allow_html=True)
    
    # Display current question
    current_mcq = st.session_state.mcqs[st.session_state.current_question_index]
    q_index = st.session_state.current_question_index
    
    source = current_mcq.get("source", "unknown")
    if source == "pdf":
        label = " From PDF"
    elif source == "internet":
        label = " From Internet"
    else:
        label = " From Topic"
    
    source_badge = f"<span class='source-badge source-{source}'>{label}</span>"
    
    st.markdown(f"""
        <div class='question-card'>
            <h3> {current_mcq['question']}</h3>
            {source_badge}
        </div>
    """, unsafe_allow_html=True)
    
    # Check if this question has already been answered and locked
    already_answered = q_index in st.session_state.answered_questions
    
    # Display options as radio buttons (none selected by default)
    selected_option = st.radio(
        "Choose your answer:",
        options=current_mcq['options'],
        key=f"q_option_{q_index}",
        label_visibility="collapsed",
        disabled=already_answered,
        index=None
    )
    
    # Store selection
    if selected_option:
        st.session_state.user_answers[q_index] = selected_option
    
    # Check Answer button and instant feedback
    if not already_answered:
        if st.button(" Check Answer", key=f"check_{q_index}", use_container_width=True):
            if q_index in st.session_state.user_answers:
                st.session_state.answered_questions.add(q_index)
                st.rerun()
            else:
                st.warning("∩╕ Please select an option first!")
    
    # Show feedback if answered
    if already_answered:
        correct_answer = current_mcq['correct_answer']
        user_answer = st.session_state.user_answers.get(q_index, "")
        is_correct = user_answer == correct_answer
        
        if is_correct:
            st.markdown(f"""
                <div class='feedback-correct'>
                     Correct! Great job! 
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='feedback-wrong'>
                     Oops! That's not right.
                </div>
                <div class='correct-answer-reveal'>
                     The correct answer is: <strong>{correct_answer}</strong>
                </div>
            """, unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("¼∩╕ Previous", use_container_width=True):
            if st.session_state.current_question_index > 0:
                st.session_state.current_question_index -= 1
                st.rerun()
    
    with col2:
        if st.button("Submit Quiz ", use_container_width=True):
            if len(st.session_state.answered_questions) == len(st.session_state.mcqs):
                st.session_state.quiz_submitted = True
                st.rerun()
            else:
                remaining = len(st.session_state.mcqs) - len(st.session_state.answered_questions)
                st.warning(f"∩╕ Please answer all questions! {remaining} remaining.")
    
    with col3:
        if st.button("₧∩╕ Next", use_container_width=True):
            if st.session_state.current_question_index < len(st.session_state.mcqs) - 1:
                st.session_state.current_question_index += 1
                st.rerun()

    st.divider()
    if st.button(" Cancel Quiz & Go Back", use_container_width=True, type="secondary"):
        st.session_state.quiz_generated = False
        st.session_state.mcqs = []
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.current_question_index = 0
        st.session_state.quiz_format = None
        st.rerun()


def display_quiz_list_format():
    """Display all quiz questions in list format with instant feedback"""
    if not st.session_state.mcqs:
        st.error("No questions to display. Please generate a quiz first.")
        return
    
    st.markdown("<h2> Answer the Questions</h2>", unsafe_allow_html=True)
    
    # Quiz info
    total_q = len(st.session_state.mcqs)
    pdf_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "pdf")
    net_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "internet")
    prompt_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "topic_prompt")
    answered_count = len(st.session_state.answered_questions)
    
    source_info = f" PDF: {pdf_q} | " if pdf_q > 0 else ""
    source_info += f" Prompt: {prompt_q} | " if prompt_q > 0 else ""
    source_info += f" Internet: {net_q}"
    
    st.markdown(f"""
        <div class='quiz-info-banner'>
             Total: {total_q} Questions | {source_info} |  Answered: {answered_count}/{total_q}
        </div>
    """, unsafe_allow_html=True)
    
    # Display all questions
    for q_index, mcq in enumerate(st.session_state.mcqs):
        source = mcq.get("source", "unknown")
        if source == "pdf":
            label = " PDF"
        elif source == "internet":
            label = " Internet"
        else:
            label = " Prompt"
        
        source_badge = f"<span class='source-badge source-{source}'>{label}</span>"
        
        already_answered = q_index in st.session_state.answered_questions
        
        st.markdown(f"""
            <div class='question-card'>
                <h3> Question {q_index + 1}: {mcq['question']}</h3>
                {source_badge}
            </div>
        """, unsafe_allow_html=True)
        
        # Display options (none selected by default)
        selected_option = st.radio(
            "Choose your answer:",
            options=mcq['options'],
            key=f"q_option_list_{q_index}",
            label_visibility="collapsed",
            disabled=already_answered,
            index=None
        )
        
        if selected_option:
            st.session_state.user_answers[q_index] = selected_option
        
        # Check Answer button for this question
        if not already_answered:
            if st.button(" Check Answer", key=f"check_list_{q_index}", use_container_width=True):
                if q_index in st.session_state.user_answers:
                    st.session_state.answered_questions.add(q_index)
                    st.rerun()
                else:
                    st.warning("∩╕ Please select an option first!")
        
        # Show feedback if answered
        if already_answered:
            correct_answer = mcq['correct_answer']
            user_answer = st.session_state.user_answers.get(q_index, "")
            is_correct = user_answer == correct_answer
            
            if is_correct:
                st.markdown(f"""
                    <div class='feedback-correct'>
                         Correct! Great job! 
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='feedback-wrong'>
                         Oops! That's not right.
                    </div>
                    <div class='correct-answer-reveal'>
                         The correct answer is: <strong>{correct_answer}</strong>
                    </div>
                """, unsafe_allow_html=True)
        
        st.divider()
    
    # Submit button
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Cancel Quiz & Go Back", use_container_width=True, type="secondary"):
            st.session_state.quiz_generated = False
            st.session_state.mcqs = []
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.current_question_index = 0
            st.session_state.quiz_format = None
            st.rerun()
    with col2:
        if st.button(" Submit Quiz & See Final Score", use_container_width=True, type="primary"):
            if len(st.session_state.answered_questions) == len(st.session_state.mcqs):
                st.session_state.quiz_submitted = True
                st.rerun()
            else:
                remaining = len(st.session_state.mcqs) - len(st.session_state.answered_questions)
                st.warning(f"∩╕ Please check all answers first! {remaining} questions remaining.")


def display_results():
    """Display quiz results with score and reward system, and auto-save the test"""
    if not st.session_state.mcqs:
        return
    
    # Calculate score
    correct_answers = [mcq['correct_answer'] for mcq in st.session_state.mcqs]
    user_answers_list = [st.session_state.user_answers.get(i, "") for i in range(len(st.session_state.mcqs))]
    
    total, correct_count, percentage = calculate_score(user_answers_list, correct_answers)
    
    # Update total stars (only once)
    if not st.session_state.test_saved:
        st.session_state.total_stars += correct_count
        if st.session_state.user:
            st.session_state.total_stars = db.update_user_stars(st.session_state.user["id"], correct_count)
            st.session_state.user["total_stars"] = st.session_state.total_stars
            db.add_game_score(st.session_state.user["id"], "Exam Quiz: " + st.session_state.current_topic, correct_count)
    
    # Auto-save the test
    if not st.session_state.test_saved:
        try:
            test_data = {
                "topic": st.session_state.current_topic,
                "mcqs": st.session_state.mcqs,
                "user_answers": st.session_state.user_answers,
                "score": {
                    "total": total,
                    "correct": correct_count,
                    "percentage": round(percentage, 1)
                },
                "pdf_files": st.session_state.pdf_files_used
            }
            saved_path = save_test(test_data)
            st.session_state.test_saved = True
            st.toast(f" Test saved successfully!", icon="")
        except Exception as e:
            st.warning(f"∩╕ Could not save test: {str(e)}")
    
    # Display result
    st.markdown("<h2> Quiz Result</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class='result-box'>
            <div class='score-text'>You got {correct_count} out of {total} questions correct!</div>
            <div class='score-text'>Score: {percentage:.0f}%</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Source breakdown
    pdf_count = sum(1 for q in st.session_state.mcqs if q.get("source") == "pdf")
    net_count = sum(1 for q in st.session_state.mcqs if q.get("source") == "internet")
    prompt_count = sum(1 for q in st.session_state.mcqs if q.get("source") == "topic_prompt")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if pdf_count > 0:
            pdf_correct = sum(1 for i, mcq in enumerate(st.session_state.mcqs) 
                             if mcq.get("source") == "pdf" and st.session_state.user_answers.get(i) == mcq['correct_answer'])
            st.metric(" PDF Questions", f"{pdf_correct}/{pdf_count}")
    with col2:
        if net_count > 0:
            net_correct = sum(1 for i, mcq in enumerate(st.session_state.mcqs) 
                             if mcq.get("source") == "internet" and st.session_state.user_answers.get(i) == mcq['correct_answer'])
            st.metric(" Internet Questions", f"{net_correct}/{net_count}")
    with col3:
        if prompt_count > 0:
            prompt_correct = sum(1 for i, mcq in enumerate(st.session_state.mcqs) 
                               if mcq.get("source") == "topic_prompt" and st.session_state.user_answers.get(i) == mcq['correct_answer'])
            st.metric(" Topic Questions", f"{prompt_correct}/{prompt_count}")
    
    # Display stars earned
    stars_earned = "" * min(correct_count, 25)
    st.markdown(f"<div class='star-display'>Stars earned: {stars_earned}</div>", unsafe_allow_html=True)
    
    # Reward system messages
    if correct_count == total:
        st.markdown("""
            <div style="text-align: center;">
                <div class="balloon"></div>
                <div class="balloon"></div>
                <div class="balloon"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div class='encouragement'> Quiz Champion! </div>", unsafe_allow_html=True)
        st.balloons()
    elif percentage >= 80:
        st.markdown("<div class='encouragement'> Amazing Work! You're a Star! </div>", unsafe_allow_html=True)
        st.balloons()
    elif percentage >= 50:
        st.markdown("<div class='encouragement'> Great Job! Keep it up! </div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='encouragement'> Good effort! Practice makes perfect! </div>", unsafe_allow_html=True)
    
    # Show total stars
    st.markdown(f"<div class='progress-text'>Total Stars So Far: {st.session_state.total_stars}</div>", 
                unsafe_allow_html=True)
    
    # Display detailed answers
    with st.expander(" View Detailed Answers"):
        for i, mcq in enumerate(st.session_state.mcqs):
            user_answer = st.session_state.user_answers.get(i, "Not answered")
            correct_answer = mcq['correct_answer']
            is_correct = user_answer == correct_answer
            source = mcq.get("source", "unknown")
            if source == "pdf":
                source_label = " PDF"
            elif source == "internet":
                source_label = " Internet"
            else:
                source_label = " Topic"
            
            icon = "" if is_correct else ""
            st.markdown(f"**{icon} Question {i + 1}** [{source_label}]: {mcq['question']}")
            st.markdown(f"Your answer: **{user_answer}**")
            if not is_correct:
                st.markdown(f"Correct answer: **{correct_answer}**")
            st.divider()
    
    # Saved test confirmation
    st.markdown("""
        <div class='quiz-info-banner'>
             This test has been automatically saved! View it in the "Saved Tests" tab.
        </div>
    """, unsafe_allow_html=True)
    
    # Reset button
    if st.button(" Take Another Quiz", use_container_width=True):
        st.session_state.quiz_generated = False
        st.session_state.mcqs = []
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.current_question_index = 0
        st.session_state.quiz_format = None
        st.session_state.test_saved = False
        st.session_state.current_topic = ""
        st.session_state.pdf_files_used = []
        st.session_state.answered_questions = set()
        st.rerun()


def display_saved_tests(exam_type="all"):
    """Display saved test history"""
    st.markdown("<h2> Saved Tests</h2>", unsafe_allow_html=True)
    
    all_tests = load_saved_tests()
    tests = []
    for test in all_tests:
        topic = test.get("topic", "")
        # Identify 10th grade tests via topic name
        is_10th = "10th Syllabus" in topic or "10th Grade" in topic or "Marathi" in topic
        
        if exam_type == "10th" and is_10th:
            tests.append(test)
        elif exam_type == "cdf" and not is_10th:
            tests.append(test)
        elif exam_type == "all":
            tests.append(test)
            
    if not tests:
        st.markdown("""
            <div class='result-box'>
                <div style='font-size: 3em; margin-bottom: 1rem;'></div>
                <div style='font-size: 1.2em; color: #666;'>No saved tests yet!</div>
                <div style='font-size: 1em; color: #999; margin-top: 0.5rem;'>Take a quiz and your results will be saved automatically.</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"<div class='progress-text'> Total Saved Tests: {len(tests)}</div>", unsafe_allow_html=True)
    
    for test in tests:
        score = test.get("score", {})
        pct = score.get("percentage", 0)
        
        # Color based on score
        if pct >= 80:
            score_color = "#2ecc71"
            score_emoji = ""
        elif pct >= 50:
            score_color = "#f39c12"
            score_emoji = "æ"
        else:
            score_color = "#e74c3c"
            score_emoji = ""
        
        st.markdown(f"""
            <div class='saved-test-card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong style='font-size: 1.2em; color: #667eea;'>{score_emoji} {test.get('topic', 'Quiz')}</strong>
                        <br>
                        <span style='color: #888; font-size: 0.9em;'> {test.get('date_readable', 'Unknown date')}</span>
                    </div>
                    <div style='text-align: right;'>
                        <span style='font-size: 1.5em; font-weight: bold; color: {score_color};'>{pct}%</span>
                        <br>
                        <span style='color: #888; font-size: 0.85em;'>
                            {score.get('correct', 0)}/{score.get('total', 0)} correct
                        </span>
                    </div>
                </div>
                <div style='margin-top: 8px; color: #999; font-size: 0.85em;'>
                    {f" PDF: {test.get('pdf_questions_count', 0)} | " if test.get('pdf_questions_count', 0) > 0 else ""}
                    {f" Prompt: {test.get('prompt_questions_count', 0)} | " if test.get('prompt_questions_count', 0) > 0 else ""}
                     Internet: {test.get('internet_questions_count', 0)}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Expandable details
        with st.expander(f"ï View Details - {test.get('topic', 'Quiz')}", expanded=False):
            questions = test.get("questions", [])
            for q in questions:
                icon = "" if q.get("is_correct") else ""
                source_label = "" if q.get("source") == "pdf" else ""
                st.markdown(f"**{icon} Q{q.get('number', '?')}** [{source_label}]: {q.get('question', '')}")
                st.markdown(f"  Your answer: **{q.get('user_answer', 'N/A')}**")
                if not q.get("is_correct"):
                    st.markdown(f"  Correct: **{q.get('correct_answer', 'N/A')}**")
                st.divider()
            
            # Retake button
            if st.button(" Retake This Quiz", key=f"retake_{test.get('test_id', 'test')}", use_container_width=True):
                # Convert back to session mcqs format
                st.session_state.mcqs = [
                    {
                        "question": q["question"],
                        "options": q["options"],
                        "correct_answer": q["correct_answer"],
                        "source": q.get("source", "unknown")
                    } for q in test.get("questions", [])
                ]
                
                # Reset attempt state
                st.session_state.user_answers = {}
                st.session_state.answered_questions = set()
                st.session_state.current_question_index = 0
                st.session_state.quiz_generated = True
                st.session_state.quiz_submitted = False
                st.session_state.test_saved = False
                st.session_state.current_topic = test.get("topic", "Retaken Quiz")
                st.session_state.pdf_files_used = test.get("pdf_files_used", [])
                st.session_state.quiz_format = None # Let user pick format again
                st.session_state.default_tab_index = 0 # Switch to Take Quiz tab
                
                st.success(" Quiz loaded! Go to the 'Take Quiz' tab to start!")
                st.rerun()


def display_auth_page():
    display_header()
    
    auth_tabs = st.tabs([" Login", " Sign Up"])
    
    with auth_tabs[0]:
        st.markdown("<h3 style='text-align:center;'>Welcome back!</h3>", unsafe_allow_html=True)
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("Login", use_container_width=True, type="primary"):
                user = db.authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.total_stars = user["total_stars"]
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            
            st.markdown("<p style='text-align:center;'>OR</p>", unsafe_allow_html=True)
            if st.button("Log in with Google ┤", use_container_width=True):
                st.info("Google OAuth implies redirect setup. In this mockup, imagine you are logged in!")
            if st.button("Log in with Phone ▒", use_container_width=True):
                st.info("OTP verification implies Twilio/Firebase setup. Mockup action!")

    with auth_tabs[1]:
        st.markdown("<h3 style='text-align:center;'>Join BrainyBee!</h3>", unsafe_allow_html=True)
        new_username = st.text_input("Choose Username", key="reg_user")
        new_password = st.text_input("Choose Password", type="password", key="reg_pass")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_pass2")
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("Sign Up", use_container_width=True, type="primary"):
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_username) < 3 or len(new_password) < 4:
                    st.error("Username (min 3) or Password (min 4) too short.")
                else:
                    if db.create_user(new_username, new_password):
                        st.success("Account created! You can now log in.")
                    else:
                        st.error("Username already taken. Try another.")

def display_10th_exam():
    st.markdown("<p style='text-align:center;color:white;opacity:0.9;font-size:1.1em;'>Subject-wise 10th Grade Exams</p>", unsafe_allow_html=True)
    
    sub_tab_quiz, sub_tab_saved = st.tabs(["Take Subject Quiz", "Saved Tests"])
    
    with sub_tab_quiz:
        if st.session_state.quiz_submitted:
            display_results()
        elif st.session_state.quiz_generated:
            if st.session_state.quiz_format is None:
                st.markdown("""
                    <div class='quiz-info-banner'>
                        Quiz generated! Choose how you'd like to take it:
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("One at a Time", use_container_width=True):
                        st.session_state.quiz_format = "single"
                        st.rerun()
                with col2:
                    if st.button("All Questions", use_container_width=True):
                        st.session_state.quiz_format = "list"
                        st.rerun()
            elif st.session_state.quiz_format == "single":
                display_quiz_questions()
            elif st.session_state.quiz_format == "list":
                display_quiz_list_format()
        else:
            st.markdown("<h2>Select 10th Grade Subject</h2>", unsafe_allow_html=True)
            
            subjects = ["Marathi", "SST", "Science", "English", "IT", "Maths"]
            selected_subject = st.selectbox("Subject:", subjects, index=0)
            
            if selected_subject == "Marathi":
                st.markdown("<h3>Exam Type</h3>", unsafe_allow_html=True)
                exam_type = st.radio("Choose Exam Type:", ["Chapter-wise", "Grammar"], horizontal=True)
                
                selected_pdf_filename = None
                chapter_name = "Grammar"
                
                if exam_type == "Chapter-wise":
                    chapters = {
                        "Chapter 2 (संतवाणी)": "chapter2.pdf",
                        "Chapter 3 (शाल)": "chapter3.pdf",
                        "Chapter 4 (उपास)": "chapter4.pdf",
                        "Chapter 4.1 (मोठे होत असलेल्या मुलांनो)": "chapter4.1.pdf"
                    }
                    chapter_name = st.selectbox("Select Chapter:", list(chapters.keys()))
                    selected_pdf_filename = chapters[chapter_name]
                else:
                    selected_pdf_filename = "marathigrammer.pdf"
                
                st.markdown("<h3>Quiz Settings</h3>", unsafe_allow_html=True)
                
                total_q = st.number_input("Total Questions", min_value=1, max_value=50, value=20, key="mar_total")
                pdf_count = total_q
                ai_count = 0
                
                st.info(f"This will generate exactly **{total_q}** questions strictly from the {chapter_name} document.")
                
                if st.button(f"Generate {total_q}-Question Marathi Exam", use_container_width=True, type="primary"):
                    with st.spinner(f"Running Local OCR on {chapter_name} to read Marathi text (This may take 1-3 minutes)..."):
                        try:
                            marathi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "10thBooks", "Marathi")
                            
                            # Hardcoded difficulty context to save tokens (skipping old paper API call)
                            difficulty_context = "Subject: Marathi for 10th Grade CBSE/NCERT. The questions should match the difficulty level of a standard 10th Grade Board Exam, focusing on critical thinking, deep understanding of the text, and proper Marathi grammar and vocabulary."
                            
                            # old_paper_pdf = os.path.join(marathi_dir, "2026MarathiQuestionPaper.pdf")
                            # old_paper_docx = os.path.join(marathi_dir, "2026MarathiQuestionPaper.docx")
                            # old_paper_txt = os.path.join(marathi_dir, "2026MarathiQuestionPaper.txt")
                            # old_paper_text = ""
                            # if os.path.exists(old_paper_docx):
                            #     from utils import extract_text_from_docx
                            #     old_paper_text = extract_text_from_docx(old_paper_docx)
                            # elif os.path.exists(old_paper_txt):
                            #     with open(old_paper_txt, 'r', encoding='utf-8') as f:
                            #         old_paper_text = f.read()
                            # elif os.path.exists(old_paper_pdf):
                            #     old_paper_text = extract_text_from_pdf(old_paper_pdf)
                            #     
                            # if old_paper_text:
                            #     if len(old_paper_text) > 10000:
                            #         old_paper_text = old_paper_text[:10000] + "\n...[truncated to fit AI rate limits]"
                            #     diff = analyze_difficulty_from_paper(old_paper_text)
                            #     if diff:
                            #         difficulty_context += f" Important context from old exam: {diff}"
                            
                            # Extract text from selected chapter/grammar
                            pdf_text = ""
                            used_files = []
                            if selected_pdf_filename:
                                pdf_path = os.path.join(marathi_dir, selected_pdf_filename)
                                docx_path = pdf_path.replace(".pdf", ".docx")
                                txt_path = pdf_path.replace(".pdf", ".txt")
                                
                                if os.path.exists(docx_path):
                                    from utils import extract_text_from_docx
                                    text = extract_text_from_docx(docx_path)
                                    if text:
                                        if len(text) > 1500: text = text[:1500] + "\n...[truncated]"
                                        used_file = selected_pdf_filename.replace('.pdf', '.docx')
                                        pdf_text += f"\n\n--- Content from {used_file} ---\n{text}"
                                        used_files.append(used_file)
                                elif os.path.exists(txt_path):
                                    with open(txt_path, 'r', encoding='utf-8') as f:
                                        text = f.read()
                                    if text:
                                        if len(text) > 1500: text = text[:1500] + "\n...[truncated]"
                                        used_file = selected_pdf_filename.replace('.pdf', '.txt')
                                        pdf_text += f"\n\n--- Content from {used_file} ---\n{text}"
                                        used_files.append(used_file)
                                elif os.path.exists(pdf_path):
                                    text = extract_text_from_pdf(pdf_path)
                                    if text:
                                        if len(text) > 1500: text = text[:1500] + "\n...[truncated]"
                                        pdf_text += f"\n\n--- Content from {selected_pdf_filename} ---\n{text}"
                                        used_files.append(selected_pdf_filename)
                                else:
                                    st.warning(f"File {selected_pdf_filename} (or its .docx/.txt version) not found in {marathi_dir}. Falling back to AI only.")
                            
                            # User explicitly requested to ALWAYS include the full AksharBharti syllabus book 
                            # alongside the prep guide for chapter-wise exams!
                            if exam_type == "Chapter-wise" and selected_pdf_filename != "AksharBharti.pdf":
                                akshar_pdf = os.path.join(marathi_dir, "AksharBharti.pdf")
                                akshar_docx = os.path.join(marathi_dir, "AksharBharti.docx")
                                akshar_txt = os.path.join(marathi_dir, "AksharBharti.txt")
                                
                                akshar_text = ""
                                if os.path.exists(akshar_docx):
                                    from utils import extract_text_from_docx
                                    akshar_text = extract_text_from_docx(akshar_docx)
                                elif os.path.exists(akshar_txt):
                                    with open(akshar_txt, 'r', encoding='utf-8') as f:
                                        akshar_text = f.read()
                                elif os.path.exists(akshar_pdf):
                                    akshar_text = extract_text_from_pdf(akshar_pdf)
                                    
                                if akshar_text:
                                    if len(akshar_text) > 1500: akshar_text = akshar_text[:1500] + "\n...[truncated]"
                                    pdf_text += f"\n\n--- Content from AksharBharti (Official Syllabus Book) ---\n{akshar_text}"
                                    used_files.append("AksharBharti")
                            
                            level = "10th Grade Student / High School Student"
                            final_topic = f"Marathi {exam_type} - {chapter_name} (CBSE NCERT 10th Syllabus)"
                            
                            try:
                                mcqs_result = generate_full_quiz(
                                    pdf_text=pdf_text,
                                    topic=final_topic,
                                    level=level,
                                    pdf_count=pdf_count,
                                    prompt_count=ai_count,
                                    internet_count=0,
                                    difficulty_context=difficulty_context,
                                    prompt_level=level,
                                    prompt2_level=level,
                                )
                                st.session_state.mcqs = mcqs_result
                                
                                if not st.session_state.mcqs:
                                    st.error("AI returned 0 questions! It might have failed to read the text. Check console.")
                                    with open(r"f:\AbhirvaLearning\debug_error.txt", "w") as f:
                                        f.write(f"Failed to generate. PDF text len: {len(pdf_text)}")
                                else:
                                    st.session_state.quiz_generated = True
                                    st.session_state.user_answers = {}
                                    st.session_state.quiz_submitted = False
                                    st.session_state.current_question_index = 0
                                    st.session_state.quiz_format = None
                                    st.session_state.test_saved = False
                                    st.session_state.current_topic = final_topic
                                    st.session_state.pdf_files_used = used_files
                                    st.session_state.answered_questions = set()
                                    
                                    st.success(f"Marathi Exam generated successfully! ({len(st.session_state.mcqs)} questions)")
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"FATAL ERROR during generation: {e}")
                                import traceback
                                with open(r"f:\AbhirvaLearning\debug_gen_error.txt", "w", encoding="utf-8") as f:
                                    f.write(traceback.format_exc())
                        
                        except Exception as e:
                            st.error(f"Error extracting text from files: {str(e)}")

            elif selected_subject == "SST":
                st.markdown("<h3>Select SST Textbook</h3>", unsafe_allow_html=True)
                sst_books = {
                    "History (India and the Contemporary World-II)": "NCERT-Class-10-History.pdf",
                    "Geography (Contemporary India-II)": "NCERT-Class-10-Geography.pdf",
                    "Political Science (Democratic Politics-II)": "NCERT-Class-10-Political-Science.pdf",
                    "Economics (Understanding Economic Development)": "NCERT-Class-10-Economics.pdf"
                }
                book_name = st.selectbox("Select Textbook:", list(sst_books.keys()))
                selected_pdf_filename = sst_books[book_name]
                
                # Pre-calculated chapter page ranges based on NCERT TOCs
                sst_chapters = {
                    "NCERT-Class-10-History.pdf": {
                        "Chapter 1: The Rise of Nationalism in Europe": {"index": (3, 24), "pdf": (3, 24)},
                        "Chapter 2: The Nationalist Movement in Indo-China": {"index": (25, 48), "pdf": (25, 48)},
                        "Chapter 3: Nationalism in India": {"index": (49, 76), "pdf": (49, 76)},
                        "Chapter 4: The Making of a Global World": {"index": (77, 96), "pdf": (77, 96)},
                        "Chapter 5: The Age of Industrialisation": {"index": (97, 116), "pdf": (97, 116)},
                        "Chapter 6: Work, Life and Leisure": {"index": (117, 140), "pdf": (117, 140)},
                        "Chapter 7: Print Culture and the Modern World": {"index": (141, 158), "pdf": (141, 158)},
                        "Chapter 8: Novels, Society and History": {"index": (159, 180), "pdf": (159, 180)}
                    },
                    "NCERT-Class-10-Political-Science.pdf": {
                        "Chapter 1: Power Sharing": {"index": (1, 12), "pdf": (15, 26)},
                        "Chapter 2: Federalism": {"index": (13, 28), "pdf": (27, 42)},
                        "Chapter 3: Gender, Religion and Caste": {"index": (29, 45), "pdf": (43, 59)},
                        "Chapter 4: Political Parties": {"index": (46, 62), "pdf": (60, 76)},
                        "Chapter 5: Outcomes of Democracy": {"index": (63, 75), "pdf": (77, 89)}
                    },
                    "NCERT-Class-10-Economics.pdf": {
                        "Chapter 1: Development": {"index": (2, 17), "pdf": (23, 37)},
                        "Chapter 2: Sectors of the Indian Economy": {"index": (18, 37), "pdf": (38, 57)},
                        "Chapter 3: Money and Credit": {"index": (38, 53), "pdf": (58, 73)},
                        "Chapter 4: Globalisation and the Indian Economy": {"index": (54, 73), "pdf": (74, 93)},
                        "Chapter 5: Consumer Rights": {"index": (74, 94), "pdf": (4, 22)}
                    },
                    "NCERT-Class-10-Geography.pdf": {
                        "Chapter 1: Resources and Development": {"index": (1, 12), "pdf": (13, 24)},
                        "Chapter 2: Forest and Wildlife Resources": {"index": (13, 18), "pdf": (25, 30)},
                        "Chapter 3: Water Resources": {"index": (19, 29), "pdf": (31, 41)},
                        "Chapter 4: Agriculture": {"index": (30, 41), "pdf": (42, 53)},
                        "Chapter 5: Minerals and Energy Resources": {"index": (42, 57), "pdf": (54, 69)},
                        "Chapter 6: Manufacturing Industries": {"index": (58, 70), "pdf": (70, 82)},
                        "Chapter 7: Lifelines of National Economy": {"index": (71, 83), "pdf": (83, 95)}
                    }
                }
                
                st.markdown("<h3>Select Chapter</h3>", unsafe_allow_html=True)
                available_chapters = list(sst_chapters[selected_pdf_filename].keys())
                selected_chapter = st.selectbox("Chapter:", available_chapters)
                
                index_start, index_end = sst_chapters[selected_pdf_filename][selected_chapter]["index"]
                pdf_start, pdf_end = sst_chapters[selected_pdf_filename][selected_chapter]["pdf"]
                
                st.info(f"**Index Pages:** {index_start} to {index_end}  \n**Mapped PDF Pages:** {pdf_start} to {pdf_end}")
                
                st.markdown("<h3>Quiz Settings</h3>", unsafe_allow_html=True)
                total_q = st.number_input("Total Questions", min_value=1, max_value=50, value=20, key="sst_total")
                
                if st.button(f"Generate {total_q}-Question SST Exam", use_container_width=True, type="primary"):
                    with st.spinner(f"Extracting {selected_chapter} and generating quiz..."):
                        try:
                            sst_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "10thBooks", "SST")
                            pdf_path = os.path.join(sst_dir, selected_pdf_filename)
                            
                            pdf_text = ""
                            used_files = []
                            if os.path.exists(pdf_path):
                                text = extract_text_from_pdf(pdf_path, start_page=pdf_start, end_page=pdf_end)
                                if text:
                                    if len(text) > 12000:
                                        text = text[:12000] + "\n...[truncated]"
                                    pdf_text = text
                                    used_files.append(f"{selected_pdf_filename} (Index Pages {index_start}-{index_end})")
                                    
                                    # Verify heading by showing the first 150 characters
                                    preview_snippet = text[:150].replace('\n', ' ')
                                    st.success(f"**Verified Chapter Heading:** {preview_snippet}...")
                            else:
                                st.error(f"File {selected_pdf_filename} not found in {sst_dir}.")
                                
                            if not pdf_text:
                                st.error("No text could be extracted from those pages.")
                            else:
                                difficulty_context = "Subject: Social Studies (SST) for 10th Grade CBSE/NCERT. The questions should match the difficulty level of a standard 10th Grade Board Exam."
                                level = "10th Grade Student / High School Student"
                                final_topic = f"SST 10th Grade - {book_name} (Pages {index_start}-{index_end})"
                                
                                mcqs_result = generate_full_quiz(
                                    pdf_text=pdf_text,
                                    topic=final_topic,
                                    level=level,
                                    pdf_count=total_q,
                                    prompt_count=0,
                                    internet_count=0,
                                    difficulty_context=difficulty_context,
                                    prompt_level=level,
                                    prompt2_level=level,
                                )
                                st.session_state.mcqs = mcqs_result
                                
                                if not st.session_state.mcqs:
                                    st.error("AI returned 0 questions! It might have failed to read the text. Check console.")
                                else:
                                    st.session_state.quiz_generated = True
                                    st.session_state.user_answers = {}
                                    st.session_state.quiz_submitted = False
                                    st.session_state.current_question_index = 0
                                    st.session_state.quiz_format = None
                                    st.session_state.test_saved = False
                                    st.session_state.current_topic = final_topic
                                    st.session_state.pdf_files_used = used_files
                                    st.session_state.answered_questions = set()
                                    
                                    st.success(f"SST Exam generated successfully! ({len(st.session_state.mcqs)} questions)")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error generating quiz: {str(e)}")

            else:
                st.markdown("<h3>Specific Topic (Optional)</h3>", unsafe_allow_html=True)
                specific_topic = st.text_input("Enter a specific chapter or topic (e.g., 'Quadratic Equations', 'Chemical Reactions'):", "")
                
                st.markdown("<h3>Quiz Settings</h3>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    total_q = st.number_input("Number of Questions", min_value=1, max_value=50, value=20)
                
                st.markdown("<h3>Upload Reference Material (Optional)</h3>", unsafe_allow_html=True)
                uploaded_files = st.file_uploader(
                    "Upload textbook chapters or notes (PDF/DOCX):",
                    type=["pdf", "docx"],
                    accept_multiple_files=True
                )
                
                if st.button(f"Generate {total_q}-Question {selected_subject} Quiz", use_container_width=True, type="primary"):
                    with st.spinner(f"Generating 10th Grade {selected_subject} quiz..."):
                        try:
                            pdf_text = ""
                            used_files = []
                            
                            if uploaded_files:
                                for uf in uploaded_files:
                                    try:
                                        if uf.type == "application/pdf":
                                            text = extract_text_from_pdf(uf)
                                        elif uf.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                            text = extract_text_from_docx(uf)
                                        else:
                                            continue
                                        if text:
                                            pdf_text += f"\n\n--- Content from {uf.name} ---\n{text}"
                                            used_files.append(uf.name)
                                    except Exception:
                                        continue
                            
                            # Set level to 10th grade
                            level = "10th Grade Student / High School Student"
                            
                            # Build the topic prompt
                            final_topic = selected_subject
                            if specific_topic:
                                final_topic += f" - {specific_topic}"
                                
                            # If files are uploaded, use them for some questions
                            pdf_count = 0
                            internet_count = total_q
                            if pdf_text:
                                pdf_count = total_q // 2
                                internet_count = total_q - pdf_count
                                
                            st.session_state.mcqs = generate_full_quiz(
                                pdf_text=pdf_text,
                                topic=final_topic,
                                level=level,
                                pdf_count=pdf_count,
                                prompt_count=internet_count,
                                internet_count=0,
                                difficulty_context=f"Subject: {selected_subject} for 10th Grade CBSE/ICSE/State Board level",
                                prompt_level=level,
                                prompt2_level=level,
                            )

                            st.session_state.quiz_generated = True
                            st.session_state.user_answers = {}
                            st.session_state.quiz_submitted = False
                            st.session_state.current_question_index = 0
                            st.session_state.quiz_format = None
                            st.session_state.test_saved = False
                            st.session_state.current_topic = final_topic
                            st.session_state.pdf_files_used = used_files
                            st.session_state.answered_questions = set()
                            
                            st.success(f"Quiz generated successfully!")
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"Error generating quiz: {str(e)}")

    with sub_tab_saved:
        display_saved_tests(exam_type="10th")

def main():
    """Main application logic"""
    if "user" not in st.session_state or not st.session_state.user:
        display_auth_page()
        return

    display_header()
    
    # Sidebar for API key check and info
    with st.sidebar:
        if not os.getenv("GROQ_API_KEY"):
            st.error("Groq API key not found!")
            st.info("Please add your API key to the .env file")
            return
        else:
            st.success("API Key loaded")
        
        if st.session_state.quiz_generated:
            st.markdown(f"- **Total:** {len(st.session_state.mcqs)} Questions")
            pdf_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "pdf")
            net_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "internet")
            prompt_q = sum(1 for q in st.session_state.mcqs if q.get("source") == "topic_prompt")
            st.markdown(f"- PDF: {pdf_q}")
            st.markdown(f"- Internet: {net_q}")
            st.markdown(f"- Prompt: {prompt_q}")
        else:
            st.markdown("- No quiz generated yet")
        st.markdown("- Model: LLaMA 3.3 70B")
    
    # ┌─┬─ MAIN NAVIGATION ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─
    main_menu = option_menu(
        menu_title=None,
        options=["10th Exam", "CDF Exam"],
        icons=["book", "building"],
        menu_icon="cast",
        default_index=st.session_state.get("main_tab", 0),
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#FFD700", "font-size": "20px"},
            "nav-link": {
                "font-size": "18px", "font-weight": "800",
                "text-align": "center", "margin": "0px",
                "--hover-color": "rgba(255,255,255,0.15)",
                "padding": "0.7rem 1.0rem",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #ff8c00 0%, #FFD700 100%)",
                "border-radius": "12px",
                "color": "#333",
            },
        }
    )

    if main_menu == "10th Exam":
        st.session_state.main_tab = 0
        display_10th_exam()
        return

    st.session_state.main_tab = 1
    st.markdown("<h2>CDF Exam Games & Prep</h2>", unsafe_allow_html=True)
    
    # ┌─┬─ TOP-LEVEL NAVIGATION ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─
    top_menu = option_menu(
        menu_title=None,
        options=["🧠 Exam Genius AI", "🌈 English Improvement Games", "🃏 Memory Training Games", "📐 Maths Games"],
        icons=["journal-bookmark-fill", "stars", "card-heading", "calculator"],
        menu_icon="cast",
        default_index=st.session_state.get("top_tab", 0),
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#FFD700", "font-size": "20px"},
            "nav-link": {
                "font-size": "15px", "font-weight": "700",
                "text-align": "center", "margin": "0px",
                "--hover-color": "rgba(255,255,255,0.15)",
                "padding": "0.7rem 1.0rem",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "border-radius": "12px",
            },
        }
    )

    # ┌─┬─ PAGE: EXAM PREPARATION ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─
    if top_menu == "🧠 Exam Genius AI":
        st.session_state.top_tab = 0
        st.markdown("<p style='text-align:center;color:white;opacity:0.9;font-size:1.1em;'>AI-powered exam generation from your PDF reference materials and topics!</p>", unsafe_allow_html=True)

        # Sub-tabs for Take Quiz / Saved Tests
        sub_tab_quiz, sub_tab_saved = st.tabs([" Take Quiz", " Saved Tests"])

        # ÇÇ SUB-TAB: Take Quiz ÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇ
        with sub_tab_quiz:
            if st.session_state.quiz_submitted:
                display_results()
            elif st.session_state.quiz_generated:
                # Quiz format selection
                if st.session_state.quiz_format is None:
                    st.markdown("""
                        <div class='quiz-info-banner'>
                             Quiz generated! Choose how you'd like to take it:
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(" One at a Time", use_container_width=True):
                            st.session_state.quiz_format = "single"
                            st.rerun()
                    with col2:
                        if st.button("ï All Questions", use_container_width=True):
                            st.session_state.quiz_format = "list"
                            st.rerun()
                elif st.session_state.quiz_format == "single":
                    display_quiz_questions()
                elif st.session_state.quiz_format == "list":
                    display_quiz_list_format()
            else:
                # Quiz creation section
                st.markdown("<h2> Create Your Quiz</h2>", unsafe_allow_html=True)
                
                # Level/Difficulty select
                st.markdown("<h3> Difficulty Settings</h3>", unsafe_allow_html=True)
                diff_mode = st.radio("Determine difficulty by:", ["Reference Exam Paper", "Standard Grade Level"], horizontal=True, index=0)
                
                difficulty_context = ""
                level = "General"
                
                if diff_mode == "Standard Grade Level":
                    level = st.selectbox(
                        "Choose the target level:",
                        options=[
                            "Preschool", "1st Grade Student", "2nd Grade Student", "3rd Grade Student", 
                            "4th Grade Student", "5th Grade Student", "6th Grade Student", 
                            "7th Grade Student", "8th Grade Student", "High School Student", "General Adult"
                        ],
                        index=3, # Default 3rd Grade
                        help="This determines the word choice and difficulty of the questions"
                    )
                else:
                    ref_paper = st.file_uploader(
                        "Upload Reference Exam Paper (Optional - 'cdfexam.pdf' used by default):",
                        type=["pdf", "docx"],
                        help="Upload a previous exam paper to match its vocabulary and complexity"
                    )
                    if ref_paper:
                        with st.spinner(" Analyzing reference paper..."):
                            if ref_paper.type == "application/pdf":
                                ref_text = extract_text_from_pdf(ref_paper)
                            else:
                                ref_text = extract_text_from_docx(ref_paper)
                            
                            difficulty_context = analyze_difficulty_from_paper(ref_text)
                            if difficulty_context:
                                st.success(" Difficulty assessed from uploaded reference paper!")
                                with st.expander(" View Difficulty Assessment"):
                                    st.write(difficulty_context)
                    else:
                        default_pdf_path = os.path.join(TEST_FOLDER, "cdfexam.pdf")
                        if os.path.exists(default_pdf_path):
                            if "default_diff_context" not in st.session_state:
                                with st.spinner(" Analyzing default reference paper (cdfexam.pdf)..."):
                                    try:
                                        ref_text = extract_text_from_pdf(default_pdf_path)
                                        st.session_state.default_diff_context = analyze_difficulty_from_paper(ref_text)
                                    except Exception as e:
                                        st.session_state.default_diff_context = f"Matches the difficulty of cdfexam.pdf"
                            
                            difficulty_context = st.session_state.default_diff_context
                            if difficulty_context:
                                st.success(" Difficulty assessed from default paper (cdfexam.pdf)!")
                                with st.expander(" View Difficulty Assessment"):
                                    st.write(difficulty_context)
                        else:
                            st.info(" Please upload a paper to use custom difficulty (cdfexam.pdf not found).")

                # Topic input
                st.markdown("<h3> Primary Topic / Prompt</h3>", unsafe_allow_html=True)
                
                PRIMARY_TOPICS = [
                    "science around us (rocket, space, india sending rockets, new invention for children, smart classroom computers)",
                    "Artificial Intelligence and emerging technologies",
                    "Solar System and Space Exploration",
                    "Animals and Nature",
                    "Mathematics and Fractions",
                    "Indian History and Culture",
                    "Health and Human Body",
                    "Environment and Climate Change",
                    "Geography and World Capitals",
                    "Sports and Games",
                    "Custom (type below)",
                ]
                
                topic_choice = st.selectbox(
                    "Select a primary topic:",
                    options=PRIMARY_TOPICS,
                    index=0,
                    help="This will be used for internet research and to generate questions"
                )
                
                if topic_choice == "Custom (type below)":
                    topic = st.text_input(
                        "Enter your custom primary topic:",
                        placeholder="Type your primary topic here...",
                    )
                else:
                    topic = topic_choice

                GRADE_OPTIONS = [
                    "Preschool", "1st Grade Student", "2nd Grade Student", "3rd Grade Student",
                    "4th Grade Student", "5th Grade Student", "6th Grade Student",
                    "7th Grade Student", "8th Grade Student", "High School Student", "General Adult"
                ]
                DHRUVA_PDF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DhruvaCDFexam.pdf")

                # Primary difficulty mode
                primary_diff_mode = st.radio(
                    "Determine difficulty by:",
                    ["Reference Exam Paper", "Standard Grade Level"],
                    horizontal=True,
                    index=0,
                    key="primary_diff_mode"
                )

                if primary_diff_mode == "Standard Grade Level":
                    primary_prompt_level = st.selectbox(
                        " Grade level for Primary Topic questions:",
                        options=GRADE_OPTIONS,
                        index=2,  # Default: 2nd Grade Student
                        key="primary_grade_level",
                        help="Questions for the primary topic will be generated at this difficulty level"
                    )
                    primary_prompt_context = ""
                else:
                    primary_prompt_level = "General"
                    primary_ref_paper = st.file_uploader(
                        "Upload a reference exam paper for primary prompt (DhruvaCDFexam.pdf used by default):",
                        type=["pdf", "docx"],
                        key="primary_ref_upload",
                        help="Upload a previous exam paper so questions match its style/vocabulary"
                    )
                    if primary_ref_paper:
                        with st.spinner(" Analyzing primary reference paper..."):
                            if primary_ref_paper.type == "application/pdf":
                                primary_ref_text = extract_text_from_pdf(primary_ref_paper)
                            else:
                                primary_ref_text = extract_text_from_docx(primary_ref_paper)
                            primary_prompt_context = analyze_difficulty_from_paper(primary_ref_text)
                            if primary_prompt_context:
                                st.success(" Primary prompt difficulty assessed from uploaded paper!")
                                with st.expander(" View Primary Prompt Difficulty Assessment"):
                                    st.write(primary_prompt_context)
                    else:
                        if os.path.exists(DHRUVA_PDF_PATH):
                            if "primary_prompt_context" not in st.session_state:
                                with st.spinner(" Analyzing DhruvaCDFexam.pdf for primary prompt..."):
                                    try:
                                        primary_ref_text = extract_text_from_pdf(DHRUVA_PDF_PATH)
                                        st.session_state.primary_prompt_context = analyze_difficulty_from_paper(primary_ref_text)
                                    except Exception:
                                        st.session_state.primary_prompt_context = "Matches the difficulty of DhruvaCDFexam.pdf"
                            primary_prompt_context = st.session_state.primary_prompt_context
                            st.success(" Using DhruvaCDFexam.pdf as default reference for primary prompt!")
                        else:
                            primary_prompt_context = ""
                            st.info(" DhruvaCDFexam.pdf not found at root. Upload a reference paper above.")

                st.markdown("<h3> Secondary Topic / Prompt</h3>", unsafe_allow_html=True)
                
                SECONDARY_TOPICS = [
                    "my body and healthy habit",
                    "Economy and Development (budget announcements - simple concepts, digital payment and UPI, inflation basic idea, Viksit Bharat 24/7 vision)",
                    "Indian Culture and Festivals",
                    "Plants and Their Uses",
                    "Water Cycle and Weather",
                    "Famous Personalities of India",
                    "Civics and Government",
                    "Transport and Technology",
                    "Custom (type below)",
                ]
                
                topic2_choice = st.selectbox(
                    "Select a secondary topic:",
                    options=SECONDARY_TOPICS,
                    index=0,
                    help="This will be used for additional internet-researched questions"
                )
                
                if topic2_choice == "Custom (type below)":
                    topic2 = st.text_input(
                        "Enter your custom secondary topic:",
                        placeholder="Type your secondary topic here...",
                    )
                else:
                    topic2 = topic2_choice

                # Secondary difficulty mode
                secondary_diff_mode = st.radio(
                    "Determine difficulty by:",
                    ["Reference Exam Paper", "Standard Grade Level"],
                    horizontal=True,
                    index=0,
                    key="secondary_diff_mode"
                )

                if secondary_diff_mode == "Standard Grade Level":
                    secondary_prompt_level = st.selectbox(
                        " Grade level for Secondary Topic questions:",
                        options=GRADE_OPTIONS,
                        index=2,  # Default: 2nd Grade Student
                        key="secondary_grade_level",
                        help="Questions for the secondary topic will be generated at this difficulty level"
                    )
                    secondary_prompt_context = ""
                else:
                    secondary_prompt_level = "General"
                    secondary_ref_paper = st.file_uploader(
                        "Upload a reference exam paper for secondary prompt (DhruvaCDFexam.pdf used by default):",
                        type=["pdf", "docx"],
                        key="secondary_ref_upload",
                        help="Upload a previous exam paper so secondary prompt questions match its style/vocabulary"
                    )
                    if secondary_ref_paper:
                        with st.spinner(" Analyzing secondary reference paper..."):
                            if secondary_ref_paper.type == "application/pdf":
                                secondary_ref_text = extract_text_from_pdf(secondary_ref_paper)
                            else:
                                secondary_ref_text = extract_text_from_docx(secondary_ref_paper)
                            secondary_prompt_context = analyze_difficulty_from_paper(secondary_ref_text)
                            if secondary_prompt_context:
                                st.success(" Secondary prompt difficulty assessed from uploaded paper!")
                                with st.expander(" View Secondary Prompt Difficulty Assessment"):
                                    st.write(secondary_prompt_context)
                    else:
                        if os.path.exists(DHRUVA_PDF_PATH):
                            if "secondary_prompt_context" not in st.session_state:
                                with st.spinner(" Analyzing DhruvaCDFexam.pdf for secondary prompt..."):
                                    try:
                                        secondary_ref_text = extract_text_from_pdf(DHRUVA_PDF_PATH)
                                        st.session_state.secondary_prompt_context = analyze_difficulty_from_paper(secondary_ref_text)
                                    except Exception:
                                        st.session_state.secondary_prompt_context = "Matches the difficulty of DhruvaCDFexam.pdf"
                            secondary_prompt_context = st.session_state.secondary_prompt_context
                            st.success(" Using DhruvaCDFexam.pdf as default reference for secondary prompt!")
                        else:
                            secondary_prompt_context = ""
                            st.info(" DhruvaCDFexam.pdf not found at root. Upload a reference paper above.")
                

                # Quiz Configuration
                st.markdown("<h3>Ö∩╕ Quiz Configuration</h3>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    total_q = st.number_input("Total Number of Questions", min_value=1, max_value=100, value=25)
                with col2:
                    q_source_mode = st.radio("Primary Content Source", ["General File Content", "Topic Prompt"], index=0)

                st.markdown("<h4> Question Distribution</h4>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    inspiring_pdf_count = st.number_input(" Inspiring Personality (PDF)", min_value=0, max_value=100, value=5)
                with c2:
                    continent_pdf_count = st.number_input(" Continent/Ocean (PDF)", min_value=0, max_value=100, value=10)
                with c3:
                    pdf_count = st.number_input(" General PDF", min_value=0, max_value=100, value=0)
                
                c4, c5, c6 = st.columns(3)
                with c4:
                    prompt_count = st.number_input(" From Primary Prompt", min_value=0, max_value=100, value=5)
                with c5:
                    prompt2_count = st.number_input(" From Secondary Prompt", min_value=0, max_value=100, value=5)
                with c6:
                    internet_count = st.number_input(" From Internet", min_value=0, max_value=100, value=max(0, total_q - (inspiring_pdf_count + continent_pdf_count + pdf_count + prompt_count + prompt2_count)))

                # Validation message
                current_total = inspiring_pdf_count + continent_pdf_count + pdf_count + prompt_count + prompt2_count + internet_count
                if current_total != total_q:
                    st.warning(f"∩╕ Sum of questions ({current_total}) does not match Total ({total_q}). The distribution counts will be used.")

                # Removed generic test folder PDF multiselect
                
                # Additional file upload
                st.markdown("<h3> Or upload additional files (optional)</h3>", unsafe_allow_html=True)
                st.info("Upload extra PDF or DOCX files to include in the quiz")
                
                uploaded_files = st.file_uploader(
                    "Choose files:",
                    type=["pdf", "docx"],
                    accept_multiple_files=True,
                    help="You can upload additional PDF or DOCX files"
                )
                
                # Dynamic Info Banner based on selection
                st.markdown(f"""
                    <div class='quiz-info-banner'>
                         <strong>Quiz Plan:</strong> {current_total} questions total.<br>
                        {f" {inspiring_pdf_count} Inspiring  | " if inspiring_pdf_count > 0 else ""}{f" {continent_pdf_count} Continent | " if continent_pdf_count > 0 else ""}{f" {pdf_count} General PDF | " if pdf_count > 0 else ""}{f" {prompt_count} Primary Prompt | " if prompt_count > 0 else ""}{f" {prompt2_count} Secondary Prompt | " if prompt2_count > 0 else ""}{f" {internet_count} Internet" if internet_count > 0 else ""}
                    </div>
                """, unsafe_allow_html=True)
                
                # Generate button
                if st.button(f"¿ Generate {current_total}-Question Quiz", use_container_width=True, type="primary"):
                    if not topic and not topic2 and not uploaded_files and pdf_count == 0 and prompt_count == 0 and prompt2_count == 0 and inspiring_pdf_count == 0 and continent_pdf_count == 0:
                        st.error(" Please provide some content (Topic or PDFs)!")
                    else:
                        with st.spinner(f"ñû Generating your {level} quiz... This may take a moment..."):
                            try:
                                inspiring_pdf_text = extract_text_from_all_pdfs_in_folder(os.path.join(TEST_FOLDER, "inspiringpersonality"))
                                continent_pdf_text = extract_text_from_all_pdfs_in_folder(os.path.join(TEST_FOLDER, "continentandocean"))
                                
                                # Step 1: No longer relying on selected_pdfs from test root
                                pdf_text = ""
                                used_files = []
                                
                                # Step 2: Extract text from uploaded files
                                if uploaded_files:
                                    for uf in uploaded_files:
                                        try:
                                            if uf.type == "application/pdf":
                                                text = extract_text_from_pdf(uf)
                                            elif uf.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                                text = extract_text_from_docx(uf)
                                            else:
                                                continue
                                            if text:
                                                pdf_text += f"\n\n--- Content from {uf.name} ---\n{text}"
                                                used_files.append(uf.name)
                                        except Exception:
                                            continue
                                
                                # Step 3: Generate the quiz with custom counts and difficulty
                                st.session_state.mcqs = generate_full_quiz(
                                    pdf_text=pdf_text,
                                    topic=topic if topic else "",
                                    level=level,
                                    pdf_count=pdf_count,
                                    prompt_count=prompt_count,
                                    internet_count=internet_count,
                                    difficulty_context=difficulty_context,
                                    inspiring_pdf_text=inspiring_pdf_text,
                                    inspiring_pdf_count=inspiring_pdf_count,
                                    continent_pdf_text=continent_pdf_text,
                                    continent_pdf_count=continent_pdf_count,
                                    topic2=topic2 if topic2 else "",
                                    prompt2_count=prompt2_count,
                                    prompt_level=primary_prompt_level,
                                    prompt2_level=secondary_prompt_level,
                                    primary_prompt_context=primary_prompt_context,
                                    secondary_prompt_context=secondary_prompt_context,
                                )

                                st.session_state.quiz_generated = True
                                st.session_state.user_answers = {}
                                st.session_state.quiz_submitted = False
                                st.session_state.current_question_index = 0
                                st.session_state.quiz_format = None
                                st.session_state.test_saved = False
                                st.session_state.current_topic = topic if topic else "PDF Quiz"
                                st.session_state.pdf_files_used = used_files
                                st.session_state.answered_questions = set()
                                
                                st.success(f" Quiz generated! {current_total} total questions!")
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f" Error generating quiz: {str(e)}")
                                st.info(" Tips: Make sure your OpenAI API key is valid and you have sufficient credits")

        # ÇÇ SUB-TAB: Saved Tests ÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇ
        with sub_tab_saved:
            display_saved_tests(exam_type="cdf")

    # ÇÇ PAGE: ENGLISH IMPROVEMENT ÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇ
    elif top_menu == " English Improvement Games":
        st.session_state.top_tab = 1
        st.markdown("<p style='text-align:center;color:white;opacity:0.9;font-size:1.1em;'>Build up your vocabulary step-by-step with fun spelling and word-meaning games!</p>", unsafe_allow_html=True)
        display_english_improvement()
        
    # ÇÇ PAGE: MEMORY GAMES ÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇ
    elif top_menu == "â Memory Training Games":
        st.session_state.top_tab = 2
        st.markdown("<p style='text-align:center;color:white;opacity:0.9;font-size:1.1em;'>Boost your short-term memory capacity with challenging and interactive deck exercises!</p>", unsafe_allow_html=True)
        display_memory_games()

    # ÇÇ PAGE: MATHS GAMES ÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇ
    elif top_menu == " Maths Games":
        st.session_state.top_tab = 3 # Assuming this is the next available tab index
        st.markdown("<p style='text-align:center;color:white;opacity:0.9;font-size:1.1em;'>Practice your math skills by popping the balloons with correct answers!</p>", unsafe_allow_html=True)
        from maths_games import display_maths_games
        display_maths_games()

if __name__ == "__main__":
    main()
