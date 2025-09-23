import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
import threading
import google.generativeai as genai
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Configuration
# -------------------------------
STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# Configure Gemini API (replace with your key)
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")  # <-- put your API key here

# -------------------------------
# Static fallback questions
# -------------------------------
STATIC_QUESTIONS = [
    {"question": "Which of the following best describes structured data?",
     "options": ["Images", "Tables with rows and columns", "Videos", "Audio"],
     "answer": "Tables with rows and columns"},
    {"question": "What is the primary purpose of data visualization?",
     "options": ["Encrypt data", "Analyze trends and patterns", "Store data", "Delete data"],
     "answer": "Analyze trends and patterns"},
    {"question": "What is the main function of an AI agent?",
     "options": ["Sense, Decide, Act", "Store data", "Only predict numbers", "Encrypt files"],
     "answer": "Sense, Decide, Act"},
    {"question": "Which of these is an example of an AI agent?",
     "options": ["ChatGPT", "Word Document", "Excel File", "PowerPoint"],
     "answer": "ChatGPT"},
    {"question": "Which feature can AI agents have?",
     "options": ["Learning from environment", "Only remembering static data", "Watching videos", "Printing documents"],
     "answer": "Learning from environment"},
]

# -------------------------------
# State management
# -------------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        state = {"players": {}, "current_q": 0, "game_started": False,
                 "questions": STATIC_QUESTIONS, "ai_questions_ready": False, "game_over": False}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def reset_game():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

# -------------------------------
# Generate AI questions in background
# -------------------------------
def generate_ai_questions():
    try:
        model = genai.GenerativeModel("gemini-1.5-turbo")
        prompt = """
        Create 5 multiple-choice quiz questions about Data Literacy and AI Agents.
        Provide them as a JSON list with keys: question, options, answer.
        Example:
        [
          {"question": "What is structured data?", 
           "options": ["Images", "Tables with rows/columns", "Videos", "Audio"], 
           "answer": "Tables with rows/columns"}
        ]
        """
        response = model.generate_content(prompt)
        ai_questions = json.loads(response.text)
        state = load_state()
        state["questions"] = ai_questions
        state["ai_questions_ready"] = True
        save_state(state)
    except Exception as e:
        # fallback to static questions
        state = load_state()
        state["ai_questions_ready"] = False
        save_state(state)

# -------------------------------
# Auto-refresh for game state updates
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App UI
# -------------------------------
st.set_page_config(page_title="AI Quiz Game", layout="centered")
role = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# HOST SCREEN
# -------------------------------
if role == "Host":
    st.title("🎮 Quiz Game Host")
    state = load_state()

    # Show QR Code for players
    st.subheader("📱 Share with Players")
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL + "?role=Player")
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)

    st.write(f"Players joined: {len(state['players'])}")

    # Start Game
    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["game_started"] = True
            state["current_q"] = 0
            state["game_over"] = False
            state["questions"] = STATIC_QUESTIONS  # instant display
            state["ai_questions_ready"] = False
            save_state(state)
            st.success("Game started! Players can now see the first question.")
            # start background AI question generation
            threading.Thread(target=generate_ai_questions, daemon=True).start()

    # Restart Game
    if st.button("🔄 Restart Game"):
        reset_game()
        st.success("Game reset! Players can rejoin.")

    # Leaderboard & game progress
    state = load_state()
    if state["game_started"]:
        if state["game_over"]:
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['players']:
                df = pd.DataFrame([{"name": k, "score": v} for k, v in state["players"].items()])
                df = df.sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_q'] + 1} / {len(state['questions'])}")
            if state['players']:
                df = pd.DataFrame([{"name": k, "score": v} for k, v in state["players"].items()])
                df = df.sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# PLAYER SCREEN
# -------------------------------
if role == "Player":
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    if not st.session_state.player_name:
        st.stop()

    st.write(f"Welcome, **{st.session_state.player_name}**!")

    state = load_state()

    # Register player instantly
    if st.session_state.player_name not in state["players"]:
        state["players"][st.session_state.player_name] = 0
        save_state(state)

    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state['players']:
            df = pd.DataFrame([{"name": k, "score": v} for k, v in state["players"].items()])
            df = df.sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # Initialize session state for question
    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Current question
    q_index = state["current_q"]
    q = state["questions"][q_index]

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"{st.session_state.player_name}_{q_index}"
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]
        if correct:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
            state["players"][st.session_state.player_name] += POINTS_PER_QUESTION
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")
        save_state(state)

    # Move to next question after timer ends
    if elapsed >= QUESTION_TIME:
        if q_index < len(state["questions"]) - 1:
            state["current_q"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        # Reset session for next question
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
