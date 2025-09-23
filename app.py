import streamlit as st
import qrcode
import json
import random
import time
from io import BytesIO
import pandas as pd
import os

STATE_FILE = "state.json"
QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# -------------------------------
# Question bank
# -------------------------------
questions = [
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
# Helpers
# -------------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        state = {"started": False, "current_q": 0, "players": {}, "questions": [], "question_start": None}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        return state
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        # Ensure keys exist
        state.setdefault("started", False)
        state.setdefault("current_q", 0)
        state.setdefault("players", {})
        state.setdefault("questions", [])
        state.setdefault("question_start", None)
        return state
    except:
        return {"started": False, "current_q": 0, "players": {}, "questions": [], "question_start": None}

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
    st.title("🎮 AI-Powered Quiz Game - Host")

    # QR Code
    game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=player"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(game_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write("📱 Ask players to scan this QR code to join!")
    st.write(f"Or share this link: {game_url}")

    state = load_state()

    if not state["started"]:
        if st.button("Start Game"):
            state["started"] = True
            state["current_q"] = 0
            state["questions"] = random.sample(questions, len(questions))
            state["question_start"] = time.time()
            save_state(state)
            st.success("✅ Game started!")
        st.stop()

    # Show current question and countdown
    q_index = state["current_q"]
    q = state["questions"][q_index]
    st.subheader(f"Question {q_index + 1}/{len(state['questions'])}")
    st.write(f"❓ {q['question']}")
    st.write("Options: " + ", ".join(q["options"]))

    elapsed = int(time.time() - state["question_start"])
    remaining = max(0, QUESTION_TIME - elapsed)
    st.write(f"⏳ Time left: {remaining} sec")

    if remaining == 0:
        if q_index + 1 < len(state["questions"]):
            state["current_q"] += 1
            state["question_start"] = time.time()
        else:
            state["started"] = False
        save_state(state)
        st.experimental_rerun()

    # Leaderboard
    st.subheader("🏆 Leaderboard - Top 3")
    if state["players"]:
        df = pd.DataFrame(list(state["players"].items()), columns=["Name","Score"]).sort_values(by="Score", ascending=False).head(3)
        st.table(df)
    else:
        st.write("No players yet.")
