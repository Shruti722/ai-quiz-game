import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO
import json

STATE_FILE = "state.json"

# -------------------------------
# Config
# -------------------------------
QUESTION_TIME = 15  # seconds per question
FEEDBACK_TIME = 3   # seconds feedback display
POINTS_PER_QUESTION = 5

# -------------------------------
# Question bank
# -------------------------------
questions = [
    {"q": "Which of the following best describes structured data?",
     "options": ["Images", "Tables with rows and columns", "Videos", "Audio"],
     "answer": "Tables with rows and columns"},
    {"q": "What is the primary purpose of data visualization?",
     "options": ["Encrypt data", "Analyze trends and patterns", "Store data", "Delete data"],
     "answer": "Analyze trends and patterns"},
    {"q": "What is the main function of an AI agent?",
     "options": ["Sense, Decide, Act", "Store data", "Only predict numbers", "Encrypt files"],
     "answer": "Sense, Decide, Act"},
    {"q": "Which of these is an example of an AI agent?",
     "options": ["ChatGPT", "Word Document", "Excel File", "PowerPoint"],
     "answer": "ChatGPT"},
    {"q": "Which feature can AI agents have?",
     "options": ["Learning from environment", "Only remembering static data", "Watching videos", "Printing documents"],
     "answer": "Learning from environment"},
]

# -------------------------------
# State helpers
# -------------------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"started": False, "current_q": 0, "players": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Role detection
# -------------------------------
query_params = st.query_params
role = query_params.get("role", ["host"])[0]

# -------------------------------
# Host screen
# -------------------------------
if role == "host":
    st.title("🎮 AI-Powered Quiz Game - Host Screen")

    # QR Code
    game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=player"  # <- Replace with your URL
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(game_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"Or share this link: {game_url}")

    state = load_state()

    if not state["started"]:
        if st.button("Start Game"):
            state["started"] = True
            state["current_q"] = 0
            save_state(state)
            st.success("✅ Game started!")
    else:
        st.info("Game is running... Players are answering questions.")

    # Leaderboard
    st.subheader("🏆 Current Leaderboard")
    if state["players"]:
        df = pd.DataFrame(list(state["players"].items()), columns=["Player", "Score"])
        df = df.sort_values(by="Score", ascending=False).head(3)
        st.table(df)
    else:
        st.write("No players joined yet.")

# -------------------------------
# Player screen
# -------------------------------
elif role == "player":
    st.title("🎮 AI-Powered Quiz Game")

    if "player_name" not in st.session_state:
        st.session_state.player_name = st.text_input("Enter your name:")

    state = load_state()

    # Wait for host to start
    if not state["started"]:
        st.info("⏳ Waiting for host to start the game...")
        st.stop()

    # Register player
    if st.session_state.player_name and st.session_state.player_name not in state["players"]:
        state["players"][st.session_state.player_name] = 0
        save_state(state)
        st.success(f"Welcome {st.session_state.player_name}! Get ready to play.")

    player = st.session_state.player_name
    q_index = state["current_q"]

    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None
    if "feedback_time" not in st.session_state:
        st.session_state.feedback_time = None

    # Game in progress
    if q_index < len(questions):
        question = questions[q_index]
        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, QUESTION_TIME - elapsed)

        st.subheader(f"❓ Question {q_index + 1}: {question['q']}")

        if not st.session_state.answered:
            st.session_state.selected_answer = st.radio("Choose your answer:", question["options"])

        st.write(f"⏳ Time left: {remaining} sec")

        # Submit or timeout
        if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.feedback_time = time.time()
            if st.session_state.selected_answer == question["answer"]:
                state["players"][player] += POINTS_PER_QUESTION
                st.success(f"✅ Correct! (+{POINTS_PER_QUESTION} points)")
            else:
                st.error(f"❌ Wrong! Correct answer: {question['answer']}")
            save_state(state)

        # Show feedback countdown
        if st.session_state.answered:
            elapsed_feedback = time.time() - st.session_state.feedback_time
            if elapsed_feedback >= FEEDBACK_TIME:
                # Next question
                state["current_q"] += 1
                save_state(state)
                st.session_state.start_time = time.time()
                st.session_state.answered = False
                st.session_state.selected_answer = None
                st.experimental_rerun()
            else:
                st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
                st.experimental_rerun()
    else:
        st.success("🎉 Quiz Over! Check leaderboard on host screen.")
