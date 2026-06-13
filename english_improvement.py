"""
English Improvement Module - Super Star Quiz App
Rich vocabulary learning games for kids (age 8)
Powered by GPT-4.1 Mini
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import random
import os
from groq import Groq
from dotenv import load_dotenv

import database as db

load_dotenv(override=True)

# ─────────────────────────────────────────────
# Groq helper
# ─────────────────────────────────────────────
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def ai_generate(prompt: str, system: str = "") -> str:
    """Call Groq LLaMA 3 and return the text response."""
    client = get_groq_client()
    if not client:
        return ""
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        response_text = response.choices[0].message.content.strip()
        
        # Clean up potential markdown blocks from LLMs
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return response_text.strip()
    except Exception as e:
        return f"ERROR: {e}"



# ─────────────────────────────────────────────
# AI Word generators
# ─────────────────────────────────────────────
SYSTEM_VOCAB = (
    "You are a friendly English teacher for 8-year-old children. "
    "Only generate age-appropriate vocabulary. "
    "Always respond with valid JSON only — no markdown, no extra text."
)

def generate_word_pairs(theme: str, pair_type: str, count: int = 6) -> list[dict]:
    """
    Generate word pairs: synonym or antonym.
    Returns list of {word, pair, sentence}
    """
    prompt = (
        f"Generate {count} unique English {pair_type} pairs suitable for an 8-year-old child.\n"
        f"Theme: {theme}\n"
        f"Return a JSON array of objects with keys: word, pair, sentence.\n"
        f"Example: [{{\"word\":\"happy\",\"pair\":\"joyful\",\"sentence\":\"She felt happy at her birthday party.\"}}]\n"
        f"Use simple, common words. Only return the JSON array."
    )
    raw = ai_generate(prompt, SYSTEM_VOCAB)
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def generate_word_builder_set(theme: str, count: int = 5) -> list[dict]:
    """
    Generate words for the Word Builder game.
    Returns list of {word, hint, sentence}
    """
    prompt = (
        f"Generate {count} English words (4-7 letters each) for an 8-year-old child.\n"
        f"Theme: {theme}\n"
        f"Return a JSON array with keys: word, hint, sentence.\n"
        f"Example: [{{\"word\":\"brave\",\"hint\":\"Not afraid\",\"sentence\":\"The brave knight saved the princess.\"}}]\n"
        f"Use simple words. Only return the JSON array."
    )
    raw = ai_generate(prompt, SYSTEM_VOCAB)
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def generate_vocab_quiz(theme: str, difficulty: str, count: int = 5) -> list[dict]:
    """
    Generate vocabulary MCQ questions.
    Returns list of {question, options, correct_answer, explanation}
    """
    prompt = (
        f"Generate {count} vocabulary multiple-choice questions for an 8-year-old child.\n"
        f"Theme: {theme}, Difficulty: {difficulty}\n"
        f"Each question tests word meaning, synonym, antonym, or usage.\n"
        f"Return a JSON array with keys: question, options (list of 4), correct_answer, explanation.\n"
        f"Example: [{{\"question\":\"What does 'brave' mean?\","
        f"\"options\":[\"Afraid\",\"Strong\",\"Not afraid\",\"Small\"],"
        f"\"correct_answer\":\"Not afraid\","
        f"\"explanation\":\"Brave means showing courage and not being afraid.\"}}]\n"
        f"Only return the JSON array."
    )
    raw = ai_generate(prompt, SYSTEM_VOCAB)
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def generate_encouragement(score_pct: float) -> str:
    prompt = (
        f"A child scored {score_pct:.0f}% on a vocabulary game. "
        f"Write one short, fun, encouraging message (max 15 words) for them. "
        f"No JSON, just the message."
    )
    return ai_generate(prompt, "You are a cheerful, encouraging teacher for 8-year-old kids.")


# ─────────────────────────────────────────────
# Session state initializer
# ─────────────────────────────────────────────
def init_english_state():
    defaults = {
        "eng_stars": 0,
        "eng_badges": [],
        "eng_game": None,           # "memory" | "builder" | "quiz"
        "eng_theme": "Animals",
        "eng_game_data": None,
        "eng_score": 0,
        "eng_total": 0,
        "eng_completed": False,
        # Memory Match
        "mm_cards": [],
        "mm_flipped": [],
        "mm_matched": set(),
        "mm_attempts": 0,
        # Word Builder
        "wb_index": 0,
        "wb_guess": "",
        "wb_results": [],
        # Quiz
        "vq_index": 0,
        "vq_answers": {},
        "vq_answered": set(),
        "vq_submitted": False,
        # Rich UI triggers 
        "trigger_confetti": False,
        "trigger_sound": None,
        # Sequence Game
        "cm_seq_start": False,
        "cm_seq_suit": "♠",
        "cm_seq_cards": [],
        "cm_seq_target": 0,
        "cm_seq_flipped": set(),
        "cm_seq_failed": False,
        "cm_seq_wrong": None,
        "cm_seq_wrong_idx": None,
        # Card Match Game
        "cm_match_start": False,
        "cm_match_cards": [],
        "cm_match_flipped": [],
        "cm_match_matched": set(),
        "cm_match_attempts": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
# JS / HTML Injections for Rich UI 
# ─────────────────────────────────────────────
def render_rich_ui_scripts():
    """Injects high-performance Confetti and Sound Effects (Howler.js/Audio)"""
    
    html_code = ""

    # Check triggers
    if st.session_state.trigger_confetti:
        html_code += """
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            var duration = 3 * 1000;
            var animationEnd = Date.now() + duration;
            var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };
            function randomInRange(min, max) { return Math.random() * (max - min) + min; }
            var interval = setInterval(function() {
                var timeLeft = animationEnd - Date.now();
                if (timeLeft <= 0) { return clearInterval(interval); }
                var particleCount = 50 * (timeLeft / duration);
                confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
                confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
            }, 250);
        </script>
        """
        st.session_state.trigger_confetti = False
        
    if st.session_state.trigger_sound:
        # Pre-encoded short audio files or external URLs
        sound_url = ""
        if st.session_state.trigger_sound == "wow":
            # A cheerful chime
            sound_url = "https://cdn.pixabay.com/download/audio/2021/08/04/audio_0625c1539c.mp3" 
        elif st.session_state.trigger_sound == "success":
            # Level up / achievement sound
            sound_url = "https://cdn.pixabay.com/download/audio/2021/08/04/audio_bb630cc098.mp3"
        elif st.session_state.trigger_sound == "sparkle":
            sound_url = "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde807.mp3"
        elif st.session_state.trigger_sound == "wrong":
            sound_url = "https://cdn.pixabay.com/download/audio/2021/08/04/audio_c6ccf3232f.mp3"
        elif st.session_state.trigger_sound == "flip":
            sound_url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_73d4e73fbf.mp3"
            
        if sound_url:
            html_code += f"""
            <audio autoplay>
                <source src="{sound_url}" type="audio/mpeg">
            </audio>
            """
        st.session_state.trigger_sound = None

    if html_code:
        components.html(html_code, height=0, width=0)

# ─────────────────────────────────────────────
# CSS for English Improvement tab
# ─────────────────────────────────────────────
ENGLISH_CSS = """
<style>
/* ── Floating Background Animations ──────────────────────── */
.floating-bg {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    overflow: hidden;
    z-index: -1;
    background: linear-gradient(135deg, #2a0845, #6441A5);
    pointer-events: none;
}
.circle {
    position: absolute;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    animation: animate 25s linear infinite;
    bottom: -150px;
}
.circle:nth-child(1) { left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
.circle:nth-child(2) { left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
.circle:nth-child(3) { left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
.circle:nth-child(4) { left: 40%; width: 60px; height: 60px; animation-delay: 0s; animation-duration: 18s; }
.circle:nth-child(5) { left: 65%; width: 20px; height: 20px; animation-delay: 0s; }
.circle:nth-child(6) { left: 75%; width: 110px; height: 110px; animation-delay: 3s; }
.circle:nth-child(7) { left: 35%; width: 150px; height: 150px; animation-delay: 7s; }
.circle:nth-child(8) { left: 50%; width: 25px; height: 25px; animation-delay: 15s; animation-duration: 45s; }
.circle:nth-child(9) { left: 20%; width: 15px; height: 15px; animation-delay: 2s; animation-duration: 35s; }
.circle:nth-child(10) { left: 85%; width: 150px; height: 150px; animation-delay: 0s; animation-duration: 11s; }

@keyframes animate {
    0% { transform: translateY(0) rotate(0deg); opacity: 1; border-radius: 0; }
    100% { transform: translateY(-1000px) rotate(720deg); opacity: 0; border-radius: 50%; }
}

/* ── Overrides for main container to look transparent ────── */
.stApp { background: transparent !important; }

/* ── Game Hub ───────────────────────────── */
.game-hub-title {
    text-align: center;
    font-size: 3.2em;
    font-weight: 900;
    color: #FFD700;
    text-shadow: 3px 3px 12px rgba(0,0,0,0.5);
    margin-bottom: 0.2rem;
    font-family: 'Outfit', 'Inter', sans-serif;
    letter-spacing: 2px;
}
.game-hub-sub {
    text-align: center;
    font-size: 1.25em;
    color: rgba(255,255,255,0.95);
    margin-bottom: 1.8rem;
    font-family: 'Inter', sans-serif;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
}

/* ── Stats bar ──────────────────────────── */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 3rem;
    background: rgba(255,255,255,0.15);
    border-radius: 24px;
    padding: 1.2rem 2.5rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}
.stat-item {
    text-align: center;
}
.stat-number {
    font-size: 1.8em;
    font-weight: 800;
    color: #FFD700;
    line-height: 1;
}
.stat-label {
    font-size: 0.78em;
    color: rgba(255,255,255,0.75);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

@media (max-width: 600px) {
    .stats-bar {
        flex-wrap: wrap;
        gap: 1.5rem;
        padding: 1rem;
    }
    .stat-number {
        font-size: 1.5em;
    }
}

/* ── Game Cards ─────────────────────────── */
.game-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.22), rgba(255,255,255,0.08));
    border-radius: 24px;
    padding: 2.2rem 1.5rem;
    text-align: center;
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
    border: 2px solid rgba(255,255,255,0.3);
    backdrop-filter: blur(12px);
    height: 100%;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}
.game-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    border-color: #FFD700;
}
.game-icon {
    font-size: 3.5em;
    margin-bottom: 0.4rem;
    display: block;
}
.game-title {
    font-size: 1.25em;
    font-weight: 700;
    color: #FFD700;
    margin-bottom: 0.3rem;
    font-family: 'Outfit', sans-serif;
}
.game-desc {
    font-size: 0.9em;
    color: rgba(255,255,255,0.8);
    line-height: 1.4;
}

/* ── Memory Match ───────────────────────── */
.mm-card {
    border-radius: 14px;
    padding: 1rem 0.5rem;
    text-align: center;
    cursor: pointer;
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2em;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    border: 2.5px solid rgba(255,255,255,0.25);
    margin-bottom: 0.5rem;
    word-break: break-word;
    line-height: 1.3;
}
.mm-card-back {
    background: repeating-linear-gradient(45deg, #764ba2, #764ba2 10px, #667eea 10px, #667eea 20px);
    box-shadow: inset 0 0 0 4px rgba(255,255,255,0.2);
    font-size: 3em;
    color: transparent !important;
    animation: flipBack 0.5s ease-out forwards;
}
.mm-card-flipped {
    background: linear-gradient(135deg, #f093fb, #f5576c);
    color: white;
    animation: flipIn 0.5s ease-out forwards;
}
.mm-card-matched {
    background: linear-gradient(135deg, #43e97b, #38f9d7);
    color: white;
    border-color: #43e97b !important;
    animation: matchPop 0.6s ease forwards;
}
.mm-card-wrong {
    background: linear-gradient(135deg, #ff416c, #ff4b2b);
    color: white;
    border-color: #ff416c !important;
    animation: shakeWrong 0.5s ease forwards;
}

@keyframes flipIn {
    0% { transform: perspective(1000px) rotateY(-180deg) scale(1.05); opacity: 0.6; }
    100% { transform: perspective(1000px) rotateY(0deg) scale(1); opacity: 1; }
}

@keyframes flipBack {
    0% { transform: perspective(1000px) rotateY(180deg) scale(1.05); opacity: 0.6; }
    100% { transform: perspective(1000px) rotateY(0deg) scale(1); opacity: 1; }
}

@keyframes shakeWrong {
    0%, 100% { transform: perspective(1000px) rotateY(0deg) translateX(0); }
    20%, 60% { transform: perspective(1000px) rotateY(0deg) translateX(-8px); }
    40%, 80% { transform: perspective(1000px) rotateY(0deg) translateX(8px); }
}

@keyframes matchPop {
    0% { transform: perspective(1000px) scale(1); }
    50% { transform: perspective(1000px) scale(1.15) rotateZ(5deg); box-shadow: 0 0 20px #43e97b; }
    100% { transform: perspective(1000px) scale(1); }
}

/* ── Word builder ───────────────────────── */
.letter-tile {
    display: inline-block;
    background: linear-gradient(135deg, #f093fb, #f5576c);
    color: white;
    font-size: 1.6em;
    font-weight: 800;
    width: 52px;
    height: 52px;
    line-height: 52px;
    text-align: center;
    border-radius: 10px;
    margin: 4px;
    cursor: pointer;
    box-shadow: 0 3px 8px rgba(0,0,0,0.25);
    transition: transform 0.15s ease;
    user-select: none;
}
.letter-tile:hover {
    transform: translateY(-4px) scale(1.1);
}
.answer-slot {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 2px dashed rgba(255,255,255,0.4);
    width: 52px;
    height: 52px;
    line-height: 52px;
    text-align: center;
    border-radius: 10px;
    margin: 4px;
    font-size: 1.4em;
    font-weight: 800;
    color: #FFD700;
}
.hint-box {
    background: rgba(255,215,0,0.15);
    border: 2px solid rgba(255,215,0,0.4);
    border-radius: 14px;
    padding: 0.8rem 1.2rem;
    color: #FFD700;
    font-weight: 600;
    text-align: center;
    margin: 0.8rem 0;
}
.feedback-wow {
    background: linear-gradient(135deg, rgba(67, 233, 123, 0.2), rgba(56, 249, 215, 0.1));
    border: 2px solid #43e97b;
    border-radius: 14px;
    padding: 1rem 1.5rem;
    color: #43e97b;
    font-weight: 700;
    font-size: 1.2em;
    text-align: center;
    animation: fadeInUp 0.4s ease;
}
.feedback-oops {
    background: linear-gradient(135deg, rgba(240, 147, 251, 0.2), rgba(245, 87, 108, 0.1));
    border: 2px solid #f5576c;
    border-radius: 14px;
    padding: 1rem 1.5rem;
    color: #f5576c;
    font-weight: 700;
    font-size: 1.2em;
    text-align: center;
    animation: fadeInUp 0.4s ease;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Vocab Quiz ─────────────────────────── */
.vq-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.97), rgba(245,240,255,0.95));
    border-radius: 18px;
    padding: 1.8rem 2rem;
    color: #333;
    margin-bottom: 1rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    border-left: 5px solid #764ba2;
}
.vq-question {
    font-size: 1.25em;
    font-weight: 700;
    color: #333;
    margin-bottom: 0.5rem;
}
.explanation-box {
    background: rgba(102,126,234,0.1);
    border: 2px solid rgba(102,126,234,0.3);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #667eea;
    font-size: 0.95em;
    margin-top: 0.5rem;
}

/* ── Celebration ────────────────────────── */
.celebration-box {
    background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,165,0,0.1));
    border: 3px solid #FFD700;
    border-radius: 22px;
    padding: 2rem;
    text-align: center;
    margin: 1.5rem 0;
    animation: pulseGlow 1.5s ease-in-out infinite alternate;
}
@keyframes pulseGlow {
    from { box-shadow: 0 0 10px rgba(255,215,0,0.4); }
    to   { box-shadow: 0 0 30px rgba(255,215,0,0.9); }
}
.badge-item {
    display: inline-block;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 20px;
    padding: 4px 14px;
    color: white;
    font-size: 0.85em;
    font-weight: 600;
    margin: 3px;
}
.progress-ring {
    text-align: center;
    font-size: 1.1em;
    color: rgba(255,255,255,0.85);
    margin: 0.5rem 0;
}

/* ── Playing Cards ──────────────────────── */
.play-card {
    background: white;
    position: relative;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.8em;
    font-weight: 800;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    border: 3px solid #ddd;
    user-select: none;
    margin-bottom: 0.5rem;
}
.play-card:hover {
    transform: perspective(1000px) translateY(-5px) scale(1.02);
    box-shadow: 0 8px 15px rgba(0,0,0,0.3);
}
.card-red { color: #e74c3c; animation: flipIn 0.5s ease-out forwards; }
.card-black { color: #2c3e50; animation: flipIn 0.5s ease-out forwards; }
.card-back {
    background: repeating-linear-gradient(45deg, #2a0845, #2a0845 10px, #6441A5 10px, #6441A5 20px);
    box-shadow: inset 0 0 0 5px white;
    color: transparent;
    animation: flipBack 0.5s ease-out forwards;
}
.card-matched {
    border-color: #43e97b !important;
    box-shadow: 0 0 15px #43e97b !important;
    animation: matchPop 0.6s ease forwards;
}
.card-wrong {
    border-color: #ff416c !important;
    box-shadow: 0 0 15px #ff416c !important;
    animation: shakeWrong 0.5s ease forwards;
}
</style>
"""


# ─────────────────────────────────────────────
# Award stars & badges helper
# ─────────────────────────────────────────────
BADGE_THRESHOLDS = [
    (5, "🌟 Star Learner"),
    (10, "🔥 Word Wizard"),
    (20, "🏆 Vocab Champion"),
    (35, "🚀 English Explorer"),
    (50, "👑 Word Master"),
]

def award_stars(n: int):
    st.session_state.eng_stars += n
    st.session_state.total_stars = st.session_state.get("total_stars", 0) + n
    
    # Save to database if user is logged in
    user = st.session_state.get("user")
    if user:
        st.session_state.total_stars = db.update_user_stars(user["id"], n)
        user["total_stars"] = st.session_state.total_stars

    # Check badges
    for threshold, badge in BADGE_THRESHOLDS:
        if st.session_state.eng_stars >= threshold and badge not in st.session_state.eng_badges:
            st.session_state.eng_badges.append(badge)
            st.toast(f"🎖️ New Badge: {badge}!", icon="🎉")


# Card-as-button CSS injected once per game render
MEMORY_CARD_BTN_CSS = """
<style>
/* Hide the invisible marker exactly */
div.element-container:has(.card-btn-marker) {
    display: none !important;
}

/* Base style for all marked cards/buttons */
div.element-container:has(.card-btn-marker) + div.element-container div[data-testid="stButton"] > button {
    border-radius: 12px !important;
    min-height: 120px !important;
    width: 100% !important;
    font-size: 2em !important;
    font-weight: 800 !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    border: 3px solid #ddd !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    color: #333 !important;
    background: white !important;
    opacity: 1 !important; /* Override disabled opacity */
}

/* Text inside the button */
div.element-container:has(.card-btn-marker) + div.element-container div[data-testid="stButton"] > button p {
    color: inherit !important;
    font-size: inherit !important;
    margin: 0 !important;
    font-weight: inherit !important;
}

/* Hover effect */
div.element-container:has(.card-btn-marker) + div.element-container div[data-testid="stButton"] > button:hover:not(:disabled) {
    transform: perspective(1000px) translateY(-5px) scale(1.02) !important;
    box-shadow: 0 8px 15px rgba(0,0,0,0.3) !important;
    border-color: #FFD700 !important;
}

/* ───────────────────────────────────────────────────────── */
/* SPECIFIC STYLES */
/* ───────────────────────────────────────────────────────── */

/* word memory back */
div.element-container:has(.card-btn-marker.mem-back) + div.element-container div[data-testid="stButton"] > button {
    background: repeating-linear-gradient(45deg,#764ba2,#764ba2 10px,#667eea 10px,#667eea 20px) !important;
    color: transparent !important;
}

/* word memory flipped */
div.element-container:has(.card-btn-marker.mem-flipped) + div.element-container div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#f093fb,#f5576c) !important;
    color: white !important;
    font-size: 1.1em !important;
}

/* word memory matched */
div.element-container:has(.card-btn-marker.mem-matched) + div.element-container div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#43e97b,#38f9d7) !important;
    color: white !important;
    border-color: #43e97b !important;
    font-size: 1.1em !important;
}

/* word memory wrong */
div.element-container:has(.card-btn-marker.mem-wrong) + div.element-container div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#ff416c,#ff4b2b) !important;
    color: white !important;
    border-color: #ff416c !important;
    font-size: 1.1em !important;
}

/* playing card back */
div.element-container:has(.card-btn-marker.pc-back) + div.element-container div[data-testid="stButton"] > button {
    background: repeating-linear-gradient(45deg,#2a0845,#2a0845 10px,#6441A5 10px,#6441A5 20px) !important;
    color: transparent !important;
}

/* playing card red */
div.element-container:has(.card-btn-marker.pc-red) + div.element-container div[data-testid="stButton"] > button {
    color: #e74c3c !important;
    border-color: #e74c3c !important;
}

/* playing card black */
div.element-container:has(.card-btn-marker.pc-black) + div.element-container div[data-testid="stButton"] > button {
    color: #2c3e50 !important;
    border-color: #2c3e50 !important;
}

/* playing card matched */
div.element-container:has(.card-btn-marker.pc-matched) + div.element-container div[data-testid="stButton"] > button {
    border-color: #43e97b !important;
    box-shadow: 0 0 16px #43e97b !important;
}

/* playing card wrong */
div.element-container:has(.card-btn-marker.pc-wrong) + div.element-container div[data-testid="stButton"] > button {
    border-color: #ff416c !important;
    box-shadow: 0 0 16px #ff416c !important;
}

/* ───────────────────────────────────────────────────────── */
/* MOBILE RESPONSIVENESS for 4-column grids */
/* ───────────────────────────────────────────────────────── */
@media (max-width: 600px) {
    div[data-testid="stHorizontalBlock"]:has(.card-btn-marker) {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
        gap: 5px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.card-btn-marker) > div[data-testid="column"] {
        flex: 1 1 calc(25% - 10px) !important;
        min-width: 0 !important;
        width: auto !important;
    }
    div.element-container:has(.card-btn-marker) + div.element-container div[data-testid="stButton"] > button {
        min-height: 80px !important;
        font-size: 1.25em !important;
        padding: 0.2rem !important;
        border-radius: 8px !important;
    }
}
</style>
"""

def _apply_mem_css():
    st.markdown(MEMORY_CARD_BTN_CSS, unsafe_allow_html=True)

def _mem_card_btn(label: str, key: str, style: str, disabled: bool = False) -> bool:
    """Render a styled memory card as an st.button. Returns True if clicked."""
    st.markdown(f'<div class="card-btn-marker {style}"></div>', unsafe_allow_html=True)
    return st.button(label, key=key, use_container_width=True, disabled=disabled)

# ─────────────────────────────────────────────
# 1. MEMORY MATCH GAME
# ─────────────────────────────────────────────
def _build_mm_cards(pairs: list[dict], pair_type: str) -> list[dict]:
    """Build shuffled card list from word pairs."""
    cards = []
    for i, p in enumerate(pairs):
        cards.append({"id": f"w{i}", "text": p["word"],     "group": i, "type": "word"})
        cards.append({"id": f"p{i}", "text": p["pair"],     "group": i, "type": "pair"})
    random.shuffle(cards)
    return cards


def display_memory_match():
    st.markdown("<div class='game-hub-title'>🃏 Memory Card Match</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Match each word with its synonym or antonym! Click a card to flip it.</div>", unsafe_allow_html=True)

    # Setup
    if not st.session_state.mm_cards:
        col1, col2, col3 = st.columns(3)
        with col1:
            theme = st.selectbox("Theme", ["Animals", "Nature", "Food", "Sports", "School", "Space"], key="mm_theme")
        with col2:
            pair_type = st.selectbox("Type", ["synonym", "antonym"], key="mm_type",
                                     format_func=lambda x: "Synonyms (same meaning)" if x == "synonym" else "Antonyms (opposites)")
        with col3:
            num_pairs = st.selectbox("Pairs", [4, 5, 6], key="mm_pairs")

        if st.button("🚀 Generate Cards with AI", use_container_width=True, type="primary"):
            with st.spinner("🤖 AI is creating your word pairs..."):
                pairs = generate_word_pairs(theme, pair_type, num_pairs)
            if not pairs:
                st.error("❌ Could not generate pairs. Check your API key.")
                return
            st.session_state.mm_cards = _build_mm_cards(pairs, pair_type)
            st.session_state.mm_flipped = []
            st.session_state.mm_matched = set()
            st.session_state.mm_attempts = 0
            st.session_state.eng_completed = False
            st.rerun()
        return

    _apply_mem_css()
    cards = st.session_state.mm_cards
    flipped = st.session_state.mm_flipped
    matched = st.session_state.mm_matched
    total_pairs = len(cards) // 2

    # Stats
    st.markdown(f"""
    <div class='stats-bar'>
        <div class='stat-item'><div class='stat-number'>{len(matched)}/{total_pairs}</div><div class='stat-label'>Matched</div></div>
        <div class='stat-item'><div class='stat-number'>{st.session_state.mm_attempts}</div><div class='stat-label'>Attempts</div></div>
        <div class='stat-item'><div class='stat-number'>{st.session_state.eng_stars}⭐</div><div class='stat-label'>Stars</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Completion check
    if len(matched) == total_pairs:
        score_pct = max(0, 100 - st.session_state.mm_attempts * 5)
        stars = max(1, total_pairs - (st.session_state.mm_attempts - total_pairs))
        if not st.session_state.eng_completed:
            award_stars(stars)
            st.session_state.eng_completed = True
            st.session_state.trigger_confetti = True
            st.session_state.trigger_sound = "success"
        
        enc = generate_encouragement(score_pct)
        st.markdown(f"""
        <div class='celebration-box'>
            <div style='font-size:3em;'>🎉🌟🎊</div>
            <div style='font-size:1.5em;font-weight:800;color:#FFD700;'>All Pairs Matched!</div>
            <div style='font-size:1.1em;color:rgba(255,255,255,0.9);margin-top:0.5rem;'>{enc}</div>
            <div style='font-size:1em;color:#FFD700;margin-top:0.5rem;'>+{stars} ⭐ Stars Earned!</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.mm_cards = []
            st.session_state.eng_completed = False
            st.rerun()
        return

    # Card grid (4 per row)
    cols_per_row = 4
    rows = [cards[i:i+cols_per_row] for i in range(0, len(cards), cols_per_row)]
    for row in rows:
        cols = st.columns(cols_per_row)
        for col, card in zip(cols, row):
            card_id = card["id"]
            is_matched = card["group"] in matched
            is_flipped = card_id in flipped
            locked = len(flipped) >= 2 and card_id not in flipped

            if is_matched:
                btn_style, btn_label = "mem-matched", card["text"]
            elif is_flipped:
                btn_style = "mem-wrong" if len(flipped) == 2 else "mem-flipped"
                btn_label = card["text"]
            else:
                btn_style, btn_label = "mem-back", "❓"

            with col:
                if _mem_card_btn(btn_label, f"mm_{card_id}", btn_style,
                                 disabled=(is_matched or locked)):
                    if card_id not in flipped and len(flipped) < 2:
                        flipped.append(card_id)
                        st.session_state.trigger_sound = "flip"
                        if len(flipped) == 2:
                            st.session_state.mm_attempts += 1
                            c1 = next(c for c in cards if c["id"] == flipped[0])
                            c2 = next(c for c in cards if c["id"] == flipped[1])
                            if c1["group"] == c2["group"] and c1["type"] != c2["type"]:
                                matched.add(c1["group"])
                                st.session_state.mm_matched = matched
                                st.session_state.mm_flipped = []
                                st.session_state.trigger_sound = "success"
                            else:
                                st.session_state.mm_flipped = flipped
                                st.session_state.trigger_sound = "wrong"
                        else:
                            st.session_state.mm_flipped = flipped
                        st.rerun()

    # Clear mismatched (Auto-flip via JS + hidden button logic)
    if len(flipped) == 2:
        c1 = next(c for c in cards if c["id"] == flipped[0])
        c2 = next(c for c in cards if c["id"] == flipped[1])
        if not (c1["group"] == c2["group"] and c1["type"] != c2["type"]):
            # Inject JS to auto clear
            components.html("""
            <script>
            setTimeout(function(){
                var btns=window.parent.document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){if(btns[i].innerText.trim()==='🔁 Try Again'){btns[i].click();break;}}
            },1200);
            </script>""", height=0, width=0)
            st.markdown("<div style='height:0;overflow:hidden'>", unsafe_allow_html=True)
            if st.button("🔁 Try Again", key="mm_clear"):
                st.session_state.mm_flipped = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True, key="mm_back"):
        st.session_state.eng_game = None
        st.session_state.mm_cards = []
        st.session_state.eng_completed = False
        st.rerun()


# ─────────────────────────────────────────────
# 2. WORD BUILDER GAME
# ─────────────────────────────────────────────
def display_word_builder():
    st.markdown("<div class='game-hub-title'>🔤 Word Builder</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Unscramble the letters to build the word!</div>", unsafe_allow_html=True)

    # Setup
    if st.session_state.eng_game_data is None:
        col1, col2 = st.columns(2)
        with col1:
            theme = st.selectbox("Choose a theme:", ["Animals", "Nature", "Food", "Sports", "Science", "Space"], key="wb_theme")
        with col2:
            count = st.selectbox("Number of words:", [4, 5, 6], key="wb_count")

        if st.button("🚀 Generate Words with AI", use_container_width=True, type="primary"):
            with st.spinner("🤖 AI is picking words for you..."):
                words = generate_word_builder_set(theme, count)
            if not words:
                st.error("❌ Could not generate words. Check your API key.")
                return
            # Shuffle letters for each word
            for w in words:
                letters = list(w["word"].upper())
                random.shuffle(letters)
                w["shuffled"] = letters
                w["answered"] = False
                w["correct"] = None
            st.session_state.eng_game_data = words
            st.session_state.wb_index = 0
            st.session_state.wb_results = []
            st.session_state.eng_completed = False
            st.rerun()
        return

    words = st.session_state.eng_game_data
    idx = st.session_state.wb_index

    if idx >= len(words):
        # Final results
        correct = sum(1 for r in st.session_state.wb_results if r)
        total = len(words)
        pct = (correct / total) * 100
        stars = correct
        if not st.session_state.eng_completed:
            award_stars(stars)
            st.session_state.eng_completed = True
            if pct >= 70:
                st.session_state.trigger_confetti = True
                st.session_state.trigger_sound = "wow"
            else:
                st.session_state.trigger_sound = "sparkle"
                
        enc = generate_encouragement(pct)
        st.markdown(f"""
        <div class='celebration-box'>
            <div style='font-size:3em;'>🎊✨🌟</div>
            <div style='font-size:1.5em;font-weight:800;color:#FFD700;'>Word Builder Complete!</div>
            <div style='font-size:1.2em;color:rgba(255,255,255,0.9);margin:0.5rem 0;'>
                You got <strong>{correct}/{total}</strong> words correct!
            </div>
            <div style='font-size:1em;color:rgba(255,255,255,0.8);'>{enc}</div>
            <div style='color:#FFD700;margin-top:0.5rem;font-weight:700;'>+{stars} ⭐ Stars!</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.eng_game_data = None
            st.session_state.wb_results = []
            st.session_state.eng_completed = False
            st.rerun()
        if st.button("🏠 Back to Games", use_container_width=True):
            st.session_state.eng_game = None
            st.session_state.eng_game_data = None
            st.session_state.eng_completed = False
            st.rerun()
        return

    # Progress
    st.markdown(f"<div class='progress-ring'>Word {idx+1} of {len(words)}</div>", unsafe_allow_html=True)
    st.progress((idx + 1) / len(words))

    word_obj = words[idx]
    shuffled = word_obj["shuffled"]
    correct_word = word_obj["word"].upper()
    hint = word_obj.get("hint", "")
    sentence = word_obj.get("sentence", "")

    # Hint
    st.markdown(f"<div class='hint-box'>💡 Hint: {hint}</div>", unsafe_allow_html=True)

    # Show shuffled tiles
    tiles_html = "".join(f"<span class='letter-tile'>{l}</span>" for l in shuffled)
    st.markdown(f"<div style='text-align:center;margin:1rem 0;'>{tiles_html}</div>", unsafe_allow_html=True)

    # Answer input
    guess = st.text_input(
        "Type the word:",
        key=f"wb_guess_{idx}",
        placeholder="Type your answer here...",
        max_chars=len(correct_word) + 2
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit Answer", use_container_width=True, type="primary"):
            is_correct = guess.strip().upper() == correct_word
            st.session_state.wb_results.append(is_correct)
            word_obj["answered"] = True
            word_obj["correct"] = is_correct
            word_obj["user_guess"] = guess.strip()
            st.rerun()

    with col2:
        if st.button("⏭️ Skip Word", use_container_width=True):
            st.session_state.wb_results.append(False)
            word_obj["answered"] = True
            word_obj["correct"] = False
            word_obj["user_guess"] = ""
            st.session_state.wb_index += 1
            st.rerun()

    # Show feedback if answered
    if word_obj.get("answered"):
        if word_obj["correct"]:
            st.markdown(f"""
            <div class='feedback-wow'>
                🎉 WOW! That's correct! ⭐<br>
                <span style='font-size:0.85em;font-weight:500;color:rgba(255,255,255,0.9);'>
                    "{sentence}"
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='feedback-oops'>
                😅 Oops! The answer was: <strong>{correct_word}</strong><br>
                <span style='font-size:0.85em;font-weight:500;'>"{sentence}"</span>
            </div>
            """, unsafe_allow_html=True)

        if st.button("➡️ Next Word", use_container_width=True):
            st.session_state.wb_index += 1
            st.rerun()

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True):
        st.session_state.eng_game = None
        st.session_state.eng_game_data = None
        st.session_state.eng_completed = False
        st.rerun()


# ─────────────────────────────────────────────
# 3. ADAPTIVE VOCABULARY QUIZ
# ─────────────────────────────────────────────
def display_vocab_quiz():
    st.markdown("<div class='game-hub-title'>📝 Vocabulary Quiz</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Test your word knowledge!</div>", unsafe_allow_html=True)

    # Setup
    if st.session_state.eng_game_data is None:
        col1, col2, col3 = st.columns(3)
        with col1:
            theme = st.selectbox("Theme:", ["Animals", "Nature", "Food", "Sports", "Science", "Space", "Feelings", "Colors"], key="vq_theme")
        with col2:
            difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"], key="vq_diff")
        with col3:
            count = st.selectbox("Questions:", [4, 5, 6, 8], key="vq_count")

        if st.button("🚀 Generate Quiz with AI", use_container_width=True, type="primary"):
            with st.spinner("🤖 AI is creating your quiz..."):
                questions = generate_vocab_quiz(theme, difficulty, count)
            if not questions:
                st.error("❌ Could not generate quiz. Check your API key.")
                return
            st.session_state.eng_game_data = questions
            st.session_state.vq_index = 0
            st.session_state.vq_answers = {}
            st.session_state.vq_answered = set()
            st.session_state.vq_submitted = False
            st.session_state.eng_completed = False
            st.rerun()
        return

    questions = st.session_state.eng_game_data
    answered = st.session_state.vq_answered
    answers = st.session_state.vq_answers

    if st.session_state.vq_submitted:
        # Results
        correct = sum(
            1 for i, q in enumerate(questions)
            if answers.get(i) == q["correct_answer"]
        )
        total = len(questions)
        pct = (correct / total) * 100
        stars = correct
        if not st.session_state.eng_completed:
            award_stars(stars)
            st.session_state.eng_completed = True
            if pct >= 60:
                st.session_state.trigger_confetti = True
                st.session_state.trigger_sound = "success"
                
        enc = generate_encouragement(pct)

        st.markdown(f"""
        <div class='celebration-box'>
            <div style='font-size:3em;'>{'🏆' if pct >= 80 else '🌟' if pct >= 60 else '💪'}</div>
            <div style='font-size:1.5em;font-weight:800;color:#FFD700;'>Quiz Complete!</div>
            <div style='font-size:1.3em;color:rgba(255,255,255,0.9);'>
                {correct}/{total} Correct &nbsp;|&nbsp; {pct:.0f}%
            </div>
            <div style='margin-top:0.5rem;color:rgba(255,255,255,0.85);'>{enc}</div>
            <div style='color:#FFD700;font-weight:700;margin-top:0.4rem;'>+{stars} ⭐ Stars!</div>
        </div>
        """, unsafe_allow_html=True)

        # Review answers
        with st.expander("📖 Review Answers"):
            for i, q in enumerate(questions):
                ua = answers.get(i, "Not answered")
                correct_ans = q["correct_answer"]
                is_c = ua == correct_ans
                icon = "✅" if is_c else "❌"
                st.markdown(f"**{icon} Q{i+1}:** {q['question']}")
                st.markdown(f"Your answer: **{ua}**")
                if not is_c:
                    st.markdown(f"Correct: **{correct_ans}**")
                if q.get("explanation"):
                    st.markdown(f"<div class='explanation-box'>💡 {q['explanation']}</div>", unsafe_allow_html=True)
                st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Quiz", use_container_width=True):
                st.session_state.eng_game_data = None
                st.session_state.eng_completed = False
                st.rerun()
        with col2:
            if st.button("🏠 Back to Games", use_container_width=True):
                st.session_state.eng_game = None
                st.session_state.eng_game_data = None
                st.session_state.eng_completed = False
                st.rerun()
        return

    # Show quiz one at a time
    idx = st.session_state.vq_index
    if idx >= len(questions):
        st.session_state.vq_submitted = True
        st.rerun()
        return

    q = questions[idx]
    already_answered = idx in answered

    st.markdown(f"""
    <div class='progress-ring'>Question {idx+1} of {len(questions)} &nbsp;|&nbsp; ✅ Answered: {len(answered)}/{len(questions)}</div>
    """, unsafe_allow_html=True)
    st.progress((idx + 1) / len(questions))

    st.markdown(f"""
    <div class='vq-card'>
        <div class='vq-question'>❓ {q['question']}</div>
    </div>
    """, unsafe_allow_html=True)

    selected = st.radio(
        "Pick an answer:",
        options=q["options"],
        key=f"vq_radio_{idx}",
        label_visibility="collapsed",
        disabled=already_answered,
        index=None,
    )

    if selected:
        answers[idx] = selected
        st.session_state.vq_answers = answers

    if not already_answered:
        if st.button("🔍 Check Answer", use_container_width=True):
            if idx in answers:
                answered.add(idx)
                st.session_state.vq_answered = answered
                st.rerun()
            else:
                st.warning("⚠️ Please select an option first!")
    else:
        ua = answers.get(idx, "")
        correct_ans = q["correct_answer"]
        is_correct = ua == correct_ans
        if is_correct:
            st.markdown("<div class='feedback-wow'>✅ Correct! Fantastic! 🌟</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='feedback-oops'>
                ❌ Not quite! The correct answer is: <strong>{correct_ans}</strong>
            </div>
            """, unsafe_allow_html=True)
        if q.get("explanation"):
            st.markdown(f"<div class='explanation-box'>💡 {q['explanation']}</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Prev", use_container_width=True):
            if idx > 0:
                st.session_state.vq_index -= 1
                st.rerun()
    with col2:
        if st.button("🎯 Submit All", use_container_width=True):
            if len(answered) == len(questions):
                st.session_state.vq_submitted = True
                st.rerun()
            else:
                st.warning(f"⚠️ Answer all questions first! ({len(questions) - len(answered)} remaining)")
    with col3:
        if st.button("➡️ Next", use_container_width=True):
            if idx < len(questions) - 1:
                st.session_state.vq_index += 1
                st.rerun()

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True):
        st.session_state.eng_game = None
        st.session_state.eng_game_data = None
        st.session_state.eng_completed = False
        st.rerun()




# ─────────────────────────────────────────────
# 4. MEMORY CARD SEQUENCE GAME
# ─────────────────────────────────────────────
def display_card_sequence():
    st.markdown("<div class='game-hub-title'>🃏 Sequence Memory</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Find the cards in order from A to K without breaking the sequence!</div>", unsafe_allow_html=True)
    
    if not st.session_state.get("cm_seq_start"):
        col1, _ = st.columns([1, 2])
        with col1:
            suit = st.selectbox("Choose a suit:", ["♠ Spades", "♥ Hearts", "♦ Diamonds", "♣ Clubs"])
        
        if st.button("🚀 Start Game", type="primary"):
            st.session_state.cm_seq_suit = suit[0]
            ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
            cards = [{"rank": r, "suit": suit[0], "idx": i} for i, r in enumerate(ranks)]
            random.shuffle(cards)
            st.session_state.cm_seq_cards = cards
            st.session_state.cm_seq_target = 0
            st.session_state.cm_seq_flipped = set()
            st.session_state.cm_seq_failed = False
            st.session_state.cm_seq_start = True
            st.session_state.eng_completed = False
            st.rerun()
        return

    cards = st.session_state.cm_seq_cards
    target = st.session_state.cm_seq_target
    flipped = st.session_state.cm_seq_flipped
    failed = st.session_state.cm_seq_failed
    
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    if target >= 13:
        if not st.session_state.eng_completed:
            award_stars(10)
            st.session_state.eng_completed = True
            st.session_state.trigger_confetti = True
            st.session_state.trigger_sound = "success"
        
        st.markdown(f"""
        <div class='celebration-box'>
            <div style='font-size:3em;'>🎉🌟🎊</div>
            <div style='font-size:1.5em;font-weight:800;color:#FFD700;'>Amazing Memory!</div>
            <div style='font-size:1.1em;color:rgba(255,255,255,0.9);margin-top:0.5rem;'>You found all 13 cards in order!</div>
            <div style='font-size:1em;color:#FFD700;margin-top:0.5rem;'>+10 ⭐ Stars Earned!</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.cm_seq_start = False
            st.rerun()
        return

    st.markdown(f"<h3 style='text-align:center;'>Next Card to Find: <strong style='color:#FFD700; font-size:1.5em;'>{ranks[target]}</strong></h3>", unsafe_allow_html=True)
    
    if failed:
        st.error(f"❌ Oops! You clicked {st.session_state.cm_seq_wrong}. You needed {ranks[target]}. The sequence is broken!")
        if st.button("🔄 Retry", use_container_width=True, type="primary"):
            st.session_state.cm_seq_target = 0
            st.session_state.cm_seq_flipped = set()
            st.session_state.cm_seq_failed = False
            st.rerun()
    
    cols_per_row = 4
    for i in range(0, 13, cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < 13:
                card = cards[idx]
                is_flipped = idx in flipped or (failed and idx == st.session_state.cm_seq_wrong_idx)
                
                with col:
                    if is_flipped:
                        color_style = "pc-red" if card["suit"] in ["♥", "♦"] else "pc-black"
                        if failed and idx == st.session_state.cm_seq_wrong_idx:
                            style = f"{color_style} pc-wrong"
                        else:
                            style = f"{color_style} pc-matched"
                        label = f"{card['rank']} {card['suit']}"
                    else:
                        style = "pc-back"
                        label = " "

                    if _mem_card_btn(label, f"seq_{idx}", style, disabled=(is_flipped or failed)):
                        st.session_state.trigger_sound = "flip"
                        if card["idx"] == target:
                            st.session_state.cm_seq_flipped.add(idx)
                            st.session_state.cm_seq_target += 1
                        else:
                            st.session_state.cm_seq_failed = True
                            st.session_state.cm_seq_wrong = f"{card['rank']}{card['suit']}"
                            st.session_state.cm_seq_wrong_idx = idx
                            st.session_state.trigger_sound = "wrong"
                        st.rerun()

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True, key="seq_back"):
        st.session_state.eng_game = None
        st.session_state.cm_seq_start = False
        st.rerun()

# ─────────────────────────────────────────────
# 5. PLAY CARD MATCH GAME
# ─────────────────────────────────────────────
def display_playcard_match():
    st.markdown("<div class='game-hub-title'>🃏 Card Match</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Find the matching playing cards!</div>", unsafe_allow_html=True)
    
    if not st.session_state.get("cm_match_start"):
        col1, _ = st.columns(2)
        with col1:
            num_pairs = st.selectbox("Pairs", [4, 6, 8], key="c_match_pairs")
        
        if st.button("🚀 Start Game", type="primary"):
            suits = ["♠", "♥", "♦", "♣"]
            ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
            deck = [f"{r}{s}" for r in ranks for s in suits]
            selected = random.sample(deck, num_pairs)
            cards = [{"id": f"{i}_a", "val": v, "group": i} for i, v in enumerate(selected)] + \
                    [{"id": f"{i}_b", "val": v, "group": i} for i, v in enumerate(selected)]
            random.shuffle(cards)
            st.session_state.cm_match_cards = cards
            st.session_state.cm_match_flipped = []
            st.session_state.cm_match_matched = set()
            st.session_state.cm_match_attempts = 0
            st.session_state.cm_match_start = True
            st.session_state.eng_completed = False
            st.rerun()
        return

    _apply_mem_css()
    cards = st.session_state.cm_match_cards
    flipped = st.session_state.cm_match_flipped
    matched = st.session_state.cm_match_matched
    total_pairs = len(cards) // 2

    # Stats
    st.markdown(f"""
    <div class='stats-bar'>
        <div class='stat-item'><div class='stat-number'>{len(matched)}/{total_pairs}</div><div class='stat-label'>Matched</div></div>
        <div class='stat-item'><div class='stat-number'>{st.session_state.cm_match_attempts}</div><div class='stat-label'>Attempts</div></div>
    </div>
    """, unsafe_allow_html=True)

    if len(matched) == total_pairs:
        stars = max(1, total_pairs - (st.session_state.cm_match_attempts - total_pairs))
        if not st.session_state.eng_completed:
            award_stars(stars)
            st.session_state.eng_completed = True
            st.session_state.trigger_confetti = True
            st.session_state.trigger_sound = "success"
        
        st.markdown(f"""
        <div class='celebration-box'>
            <div style='font-size:3em;'>🎉🌟🎊</div>
            <div style='font-size:1.5em;font-weight:800;color:#FFD700;'>All Pairs Matched!</div>
            <div style='font-size:1em;color:#FFD700;margin-top:0.5rem;'>+{stars} ⭐ Stars Earned!</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.cm_match_start = False
            st.rerun()
        return

    cols_per_row = 4
    rows = [cards[i:i+cols_per_row] for i in range(0, len(cards), cols_per_row)]
    
    for row in rows:
        cols = st.columns(cols_per_row)
        for col, card in zip(cols, row):
            card_id = card["id"]
            is_matched = card["group"] in matched
            is_flipped = card_id in flipped
            locked = len(flipped) >= 2 and card_id not in flipped
            
            val = card["val"]
            c_rank = val[:-1]
            c_suit = val[-1]
            is_red = "♥" in val or "♦" in val

            if is_matched:
                style = "pc-red pc-matched" if is_red else "pc-black pc-matched"
                label = f"{c_rank} {c_suit}"
            elif is_flipped:
                color_style = "pc-red" if is_red else "pc-black"
                style = color_style + " pc-wrong" if len(flipped) == 2 else color_style
                label = f"{c_rank} {c_suit}"
            else:
                style, label = "pc-back", " "

            with col:
                if _mem_card_btn(label, f"cm_{card_id}", style, disabled=(is_matched or locked)):
                    if card_id not in flipped and len(flipped) < 2:
                        flipped.append(card_id)
                        st.session_state.trigger_sound = "flip"
                        if len(flipped) == 2:
                            st.session_state.cm_match_attempts += 1
                            c1 = next(c for c in cards if c["id"] == flipped[0])
                            c2 = next(c for c in cards if c["id"] == flipped[1])
                            if c1["group"] == c2["group"]:
                                matched.add(c1["group"])
                                st.session_state.cm_match_matched = matched
                                st.session_state.cm_match_flipped = []
                                st.session_state.trigger_sound = "success"
                            else:
                                st.session_state.cm_match_flipped = flipped
                                st.session_state.trigger_sound = "wrong"
                        else:
                            st.session_state.cm_match_flipped = flipped
                        st.rerun()

    if len(flipped) == 2:
        c1 = next(c for c in cards if c["id"] == flipped[0])
        c2 = next(c for c in cards if c["id"] == flipped[1])
        if c1["group"] != c2["group"]:
            components.html("""
            <script>
            setTimeout(function(){
                var btns=window.parent.document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){if(btns[i].innerText.trim()==='🔁 Clear Mismatch'){btns[i].click();break;}}
            },1200);
            </script>""", height=0, width=0)
            st.markdown("<div style='height:0;overflow:hidden'>", unsafe_allow_html=True)
            if st.button("🔁 Clear Mismatch", key="cm_clear"):
                st.session_state.cm_match_flipped = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True, key="cm_back"):
        st.session_state.eng_game = None
        st.session_state.cm_match_start = False
        st.rerun()


# ─────────────────────────────────────────────
# 6. COUNTRY FLAG MEMORY GAME
# ─────────────────────────────────────────────
FLAG_DATA = [
    {"flag": "🇺🇸", "code": "us", "name": "USA"}, {"flag": "🇬🇧", "code": "gb", "name": "United Kingdom"},
    {"flag": "🇨🇦", "code": "ca", "name": "Canada"}, {"flag": "🇦🇺", "code": "au", "name": "Australia"},
    {"flag": "🇮🇳", "code": "in", "name": "India"}, {"flag": "🇯🇵", "code": "jp", "name": "Japan"},
    {"flag": "🇫🇷", "code": "fr", "name": "France"}, {"flag": "🇩🇪", "code": "de", "name": "Germany"},
    {"flag": "🇧🇷", "code": "br", "name": "Brazil"}, {"flag": "🇮🇹", "code": "it", "name": "Italy"},
    {"flag": "🇪🇸", "code": "es", "name": "Spain"}, {"flag": "🇨🇳", "code": "cn", "name": "China"},
    {"flag": "🇰🇷", "code": "kr", "name": "South Korea"}, {"flag": "🇷🇺", "code": "ru", "name": "Russia"},
    {"flag": "🇿🇦", "code": "za", "name": "South Africa"}, {"flag": "🇲🇽", "code": "mx", "name": "Mexico"}
]

def display_flag_game():
    st.markdown("<div class='game-hub-title'>🚩 Country Flag Quiz</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Guess the correct country for each flag!</div>", unsafe_allow_html=True)

    if not st.session_state.get("flag_started"):
        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            st.session_state.flag_pool = random.sample(FLAG_DATA, min(len(FLAG_DATA), 10))
            st.session_state.flag_idx = 0
            st.session_state.flag_score = 0
            st.session_state.flag_started = True
            st.session_state.flag_answered = False
            st.session_state.eng_completed = False
            st.rerun()
        return

    pool = st.session_state.flag_pool
    idx = st.session_state.flag_idx

    if idx >= len(pool):
        stars = st.session_state.flag_score // 2
        if not st.session_state.eng_completed:
            award_stars(stars)
            st.session_state.eng_completed = True
            st.session_state.trigger_confetti = True
        
        st.markdown(f"""
        <div class='celebration-box'>
            <div style='font-size:1.5em;font-weight:800;color:#FFD700;'>Quiz Finished!</div>
            <div style='font-size:1.2em;'>Score: {st.session_state.flag_score}/{len(pool)}</div>
            <div style='color:#FFD700;'>+{stars} ⭐ Stars!</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.flag_started = False
            st.rerun()
        return

    current = pool[idx]
    st.markdown(f"<div style='text-align:center; margin: 2rem 0;'><img src='https://flagcdn.com/w320/{current['code'].lower()}.png' style='height: 150px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);'></div>", unsafe_allow_html=True)

    if not st.session_state.flag_answered:
        # Generate 4 options
        if not st.session_state.get("flag_options"):
            wrong = [f["name"] for f in FLAG_DATA if f["name"] != current["name"]]
            options = random.sample(wrong, 3) + [current["name"]]
            random.shuffle(options)
            st.session_state.flag_options = options
        
        options = st.session_state.flag_options
        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"flag_opt_{i}", use_container_width=True):
                    st.session_state.flag_answered = True
                    st.session_state.flag_correct = (opt == current["name"])
                    if st.session_state.flag_correct:
                        st.session_state.flag_score += 1
                        st.session_state.trigger_sound = "success"
                    else:
                        st.session_state.trigger_sound = "wrong"
                    st.rerun()
    else:
        if st.session_state.flag_correct:
            st.success(f"✅ Correct! It's {current['name']}")
        else:
            st.error(f"❌ Incorrect! It was {current['name']}")
        
        if st.button("Next Flag ➡️", use_container_width=True):
            st.session_state.flag_idx += 1
            st.session_state.flag_answered = False
            st.session_state.flag_options = None
            st.rerun()

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True, key="flag_back"):
        st.session_state.eng_game = None
        st.session_state.flag_started = False
        st.rerun()


# ─────────────────────────────────────────────
# 7. NUMBER MEMORY GAME
# ─────────────────────────────────────────────
def display_number_memory():
    st.markdown("<div class='game-hub-title'>🔢 Number Memory</div>", unsafe_allow_html=True)
    st.markdown("<div class='game-hub-sub'>Remember the number sequence and type it back!</div>", unsafe_allow_html=True)

    if not st.session_state.get("num_mem_start"):
        st.markdown("<div style='text-align:center; padding: 2rem;'>Try to remember as many digits as you can!</div>", unsafe_allow_html=True)
        if st.button("🚀 Start Level 1", type="primary", use_container_width=True):
            st.session_state.num_mem_level = 1
            st.session_state.num_mem_current = "".join([str(random.randint(0, 9)) for _ in range(3)])
            st.session_state.num_mem_show = True
            st.session_state.num_mem_start = True
            st.session_state.num_mem_timer = 3000 # 3 seconds
            st.session_state.eng_completed = False
            st.rerun()
        return

    level = st.session_state.num_mem_level
    current_num = st.session_state.num_mem_current

    if st.session_state.num_mem_show:
        st.markdown(f"<div style='text-align:center; font-size:6em; font-weight:900; color:#FFD700; margin: 3rem 0;'>{current_num}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;'>Remember this number!</div>", unsafe_allow_html=True)
        
        # In a real app, we'd use a timer. In Streamlit, we'll use a button to say "I'm Ready"
        if st.button("I'm Ready! 🧠", use_container_width=True):
            st.session_state.num_mem_show = False
            st.rerun()
    else:
        guess = st.text_input("What was the number?", key="num_mem_guess")
        if st.button("Check 🔍", use_container_width=True, type="primary"):
            if guess.strip() == current_num:
                st.success("✅ Correct! Amazing memory!")
                st.session_state.trigger_sound = "success"
                st.session_state.num_mem_level += 1
                # Increase difficulty
                new_len = 3 + st.session_state.num_mem_level
                st.session_state.num_mem_current = "".join([str(random.randint(0, 9)) for _ in range(new_len)])
                st.session_state.num_mem_show = True
                st.rerun()
            else:
                st.error(f"❌ Oops! The number was {current_num}. Game Over!")
                st.session_state.trigger_sound = "wrong"
                stars = (level - 1) * 2
                if not st.session_state.eng_completed:
                    award_stars(stars)
                    st.session_state.eng_completed = True
                
                st.markdown(f"<div style='text-align:center; font-size:1.5em;'>You reached Level {level}! Earned {stars} ⭐ Stars.</div>", unsafe_allow_html=True)
                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.num_mem_start = False
                    st.rerun()

    st.markdown("---")
    if st.button("🏠 Back to Games", use_container_width=True, key="num_mem_back"):
        st.session_state.eng_game = None
        st.session_state.num_mem_start = False
        st.rerun()

# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────
def display_english_improvement():
    """Main entry point called from app.py"""
    init_english_state()
    st.markdown(ENGLISH_CSS, unsafe_allow_html=True)
    render_rich_ui_scripts()

    # ── Badges row ──────────────────────────
    if st.session_state.eng_badges:
        badges_html = " ".join(f"<span class='badge-item'>{b}</span>" for b in st.session_state.eng_badges)
        st.markdown(f"<div style='text-align:center;margin-bottom:0.5rem;'>{badges_html}</div>", unsafe_allow_html=True)

    # ── Route to active game ─────────────────
    game = st.session_state.eng_game

    if game == "memory":
        display_memory_match()
    elif game == "builder":
        display_word_builder()
    elif game == "quiz":
        display_vocab_quiz()
    else:
        # ── Game Hub ─────────────────────────
        st.markdown("""
        <div class="floating-bg">
            <div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div>
            <div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='game-hub-title'>🌈 English Word Games</div>", unsafe_allow_html=True)
        st.markdown("<div class='game-hub-sub'>Pick a game and start learning vocabulary! Earn ⭐ stars and unlock badges!</div>", unsafe_allow_html=True)

        # Stats bar
        st.markdown(f"""
        <div class='stats-bar'>
            <div class='stat-item'>
                <div class='stat-number'>{st.session_state.eng_stars}</div>
                <div class='stat-label'>Game Stars</div>
            </div>
            <div class='stat-item'>
                <div class='stat-number'>{len(st.session_state.eng_badges)}</div>
                <div class='stat-label'>Badges</div>
            </div>
            <div class='stat-item'>
                <div class='stat-number'>{st.session_state.get("total_stars", 0)}</div>
                <div class='stat-label'>Total Stars</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Game cards
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>🃏</span>
                <div class='game-title'>Memory Match</div>
                <div class='game-desc'>Match words with their synonyms or antonyms. Flip the cards!</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Memory Match 🃏", use_container_width=True, key="go_memory"):
                st.session_state.eng_game = "memory"
                st.session_state.mm_cards = []
                st.session_state.mm_flipped = []
                st.session_state.mm_matched = set()
                st.session_state.mm_attempts = 0
                st.session_state.eng_completed = False
                st.rerun()

        with c2:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>🔤</span>
                <div class='game-title'>Word Builder</div>
                <div class='game-desc'>Unscramble the jumbled letters to spell the correct word!</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Word Builder 🔤", use_container_width=True, key="go_builder"):
                st.session_state.eng_game = "builder"
                st.session_state.eng_game_data = None
                st.session_state.wb_index = 0
                st.session_state.wb_results = []
                st.session_state.eng_completed = False
                st.rerun()

        with c3:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>📝</span>
                <div class='game-title'>Vocab Quiz</div>
                <div class='game-desc'>Answer AI-powered vocabulary questions. Adapt your difficulty!</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Vocab Quiz 📝", use_container_width=True, key="go_quiz"):
                st.session_state.eng_game = "quiz"
                st.session_state.eng_game_data = None
                st.session_state.vq_index = 0
                st.session_state.vq_answers = {}
                st.session_state.vq_answered = set()
                st.session_state.vq_submitted = False
                st.session_state.eng_completed = False
                st.rerun()

        # How to earn badges (Global to hub)
        st.markdown("---")
        st.markdown("""
        <div style='text-align:center;color:rgba(255,255,255,0.75);font-size:0.92em;'>
            🏅 <strong style='color:#FFD700;'>Earn Badges:</strong>
            5⭐ Star Learner &nbsp;|&nbsp;
            10⭐ Word Wizard &nbsp;|&nbsp;
            20⭐ Vocab Champion &nbsp;|&nbsp;
            35⭐ English Explorer &nbsp;|&nbsp;
            50⭐ Word Master
        </div>
        """, unsafe_allow_html=True)


def display_memory_games():
    """Main entry for Card Memory games"""
    init_english_state()
    st.markdown(ENGLISH_CSS, unsafe_allow_html=True)
    render_rich_ui_scripts()

    # ── Badges row ──────────────────────────
    if st.session_state.eng_badges:
        badges_html = " ".join(f"<span class='badge-item'>{b}</span>" for b in st.session_state.eng_badges)
        st.markdown(f"<div style='text-align:center;margin-bottom:0.5rem;'>{badges_html}</div>", unsafe_allow_html=True)

    # ── Route to active memory game ─────────────────
    game = st.session_state.eng_game

    if game == "seq_memory":
        display_card_sequence()
    elif game == "card_match":
        display_playcard_match()
    elif game == "flag_game":
        display_flag_game()
    elif game == "num_memory":
        display_number_memory()
    else:
        st.markdown("""
        <div class="floating-bg">
            <div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='game-hub-title'>🃏 Card Memory Games</div>", unsafe_allow_html=True)
        st.markdown("<div class='game-hub-sub'>Train your mind with these fun playing card challenges!</div>", unsafe_allow_html=True)
        
        # Stats bar
        st.markdown(f"""
        <div class='stats-bar'>
            <div class='stat-item'><div class='stat-number'>{st.session_state.eng_stars}</div><div class='stat-label'>Game Stars</div></div>
            <div class='stat-item'><div class='stat-number'>{len(st.session_state.eng_badges)}</div><div class='stat-label'>Badges</div></div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>🃏</span>
                <div class='game-title'>Sequence</div>
                <div class='game-desc'>Pick cards in A-K order.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Sequence", use_container_width=True, key="go_seq_hub"):
                st.session_state.eng_game = "seq_memory"
                st.session_state.cm_seq_start = False
                st.rerun()
                
        with c2:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>🎴</span>
                <div class='game-title'>Matching</div>
                <div class='game-desc'>Find matching card pairs.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Matching", use_container_width=True, key="go_match_hub"):
                st.session_state.eng_game = "card_match"
                st.session_state.cm_match_start = False
                st.rerun()

        with c3:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>🚩</span>
                <div class='game-title'>Flags</div>
                <div class='game-desc'>Guess country from flags.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Flags", use_container_width=True, key="go_flag_hub"):
                st.session_state.eng_game = "flag_game"
                st.session_state.flag_started = False
                st.rerun()

        with c4:
            st.markdown("""
            <div class='game-card'>
                <span class='game-icon'>🔢</span>
                <div class='game-title'>Numbers</div>
                <div class='game-desc'>Remember digits in order!</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Play Numbers", use_container_width=True, key="go_num_hub"):
                st.session_state.eng_game = "num_memory"
                st.session_state.num_mem_start = False
                st.rerun()

        st.markdown("---")
        st.markdown("""
        <div style='text-align:center;color:rgba(255,255,255,0.75);font-size:0.92em;'>
            🏅 <strong style='color:#FFD700;'>Earn Badges:</strong>
            5⭐ Star Learner &nbsp;|&nbsp;
            10⭐ Word Wizard &nbsp;|&nbsp;
            20⭐ Vocab Champion &nbsp;|&nbsp;
            35⭐ English Explorer &nbsp;|&nbsp;
            50⭐ Word Master
        </div>
        """, unsafe_allow_html=True)
