import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
from datetime import datetime
import google.generativeai as genai
import traceback

# —————————––
# Config
# —————————––

STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"
QUESTION_TIME = 20
POINTS_PER_QUESTION = 5
AUTO_REFRESH_INTERVAL = 1000  # milliseconds

# —————————––
# Page Config
# —————————––

st.set_page_config(
    page_title="AI Quiz Game",
    page_icon="🎮",
    layout="wide"
)

# —————————––
# Gemini Setup
# —————————––

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-1.5-flash"  # Using flash for faster response

# —————————––
# Fallback Questions
# —————————––

FALLBACK_QUESTIONS = [
    {"question": "What does the standard deviation measure?", "options": ["The central value of data", "The spread of data around the mean", "The most common value", "The difference between max and min"], "answer": "The spread of data around the mean"},
    {"question": "Which company built AlphaGo, the AI agent that beat a Go world champion?", "options": ["OpenAI", "DeepMind", "IBM", "Microsoft"], "answer": "DeepMind"},
    {"question": "Which measure of central tendency is most affected by extreme values?", "options": ["Mean", "Median", "Mode", "Range"], "answer": "Mean"},
    {"question": "Which of these best describes ‘data literacy’?", "options": ["Ability to read and work with data", "Ability to code", "Ability to memorize statistics", "Ability to create charts only"], "answer": "Ability to read and work with data"},
    {"question": "What is a ‘multi-agent system’?", "options": ["AI working in isolation", "Multiple AI agents interacting", "Humans and AI working together", "One AI agent with multiple tasks"], "answer": "Multiple AI agents interacting"},
    {"question": "Which famous AI agent defeated Garry Kasparov in chess?", "options": ["AlphaGo", "Siri", "Deep Blue", "Watson"], "answer": "Deep Blue"},
    {"question": "What is the primary purpose of data visualization?", "options": ["To make data look pretty", "To identify patterns and insights", "To store data", "To clean data"], "answer": "To identify patterns and insights"},
    {"question": "Which AI agent famously won Jeopardy! against human champions?", "options": ["Siri", "Watson", "Alexa", "BERT"], "answer": "Watson"},
    {"question": "Which of these is an example of a reactive AI agent?", "options": ["Chess AI", "Personal Assistant", "Self-driving car", "Spam filter"], "answer": "Spam filter"},
    {"question": "What does a histogram show?", "options": ["Trends over time", "Distribution of data", "Relationship between variables", "Averages only"], "answer": "Distribution of data"},
]

# —————————––
# State Management with File Locking
# —————————––

def get_default_state():
    """Returns the default state structure"""
    return {
        "game_started": False,
        "current_question": 0,
        "scores": [],
        "game_over": False,
        "players": {},
        "questions": [],
        "host_question_start": time.time(),
        "last_updated": time.time(),
        "game_id": datetime.now().strftime("%Y%m%d_%H%M%S")
    }

def save_state(state):
    """Save state with error handling"""
    try:
        state["last_updated"] = time.time()
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)  # Atomic rename
        return True
    except Exception as e:
        st.error(f"Error saving state: {e}")
        return False

def load_state():
    """Load state with error handling"""
    if not os.path.exists(STATE_FILE):
        state = get_default_state()
        save_state(state)
        return state

    try:
        with open(STATE_FILE, "r") as f:
            content = f.read()
            if not content:
                raise ValueError("Empty state file")
            state = json.loads(content)

        # Validate state
        default_state = get_default_state()
        for key, value in default_state.items():
            if key not in state:
                state[key] = value

        return state
    except Exception as e:
        st.warning(f"State file corrupted, resetting: {e}")
        state = get_default_state()
        save_state(state)
        return state

def reset_game():
    """Complete game reset"""
    state = get_default_state()
    state["questions"] = get_ai_questions()
    save_state(state)
    return state

# —————————––
# Question Generator
# —————————––

@st.cache_data(ttl=3600)
def get_ai_questions():
    """Generate questions using Gemini AI with fallback"""
    prompt = """
    Create exactly 10 multiple-choice quiz questions about Data Literacy and AI Agents.
    Mix basic and intermediate difficulty levels.

    Return ONLY a valid JSON array with this exact structure:
    [
      {
        "question": "Question text here?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "answer": "The correct option exactly as written in options"
      }
    ]
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        questions = json.loads(text.strip())

        if not isinstance(questions, list) or len(questions) < 5:
            raise ValueError("Invalid questions format")

        for q in questions:
            if not all(k in q for k in ["question", "options", "answer"]):
                raise ValueError("Missing required fields")
            if len(q["options"]) != 4:
                raise ValueError("Must have exactly 4 options")
            if q["answer"] not in q["options"]:
                raise ValueError("Answer must be in options")

        return questions[:10]

    except Exception as e:
        st.warning(f"Using fallback questions due to: {e}")
        return FALLBACK_QUESTIONS

# —————————––
# Auto-refresh Component
# —————————––

def auto_refresh():
    """Custom auto-refresh implementation"""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    current_time = time.time()
    if current_time - st.session_state.last_refresh > 1:
        st.session_state.last_refresh = current_time
        st.rerun()

auto_refresh_script = """
<script>
setTimeout(function(){
    window.location.reload();
}, 1000);
</script>
"""

# —————————––
# Initialize Session State
# —————————––

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.player_name = ""
    st.session_state.answered = False
    st.session_state.selected_answer = None
    st.session_state.last_question_index = -1
    st.session_state.player_score = 0

# Load state
state = load_state()

# Generate questions if needed
if not state["questions"]:
    with st.spinner("Generating quiz questions..."):
        state["questions"] = get_ai_questions()
        save_state(state)

# —————————––
# Mode Selection
# —————————––

params = st.query_params
role = params.get("role", "Host")

with st.sidebar:
    st.title("🎮 Quiz Game Settings")
    mode = st.selectbox(
        "Select mode:",
        ["Host", "Player"],
        index=0 if role == "Host" else 1,
        key="mode_selector"
    )

    st.divider()
    st.caption(f"Game ID: {state.get('game_id', 'Unknown')}")
    st.caption(f"Questions: {len(state['questions'])}")
    st.caption(f"Time per question: {QUESTION_TIME}s")

# —————————––
# Host & Player Screens follow...
# (keep your existing host/player code below unchanged, now indentation is fixed)
# —————————––

