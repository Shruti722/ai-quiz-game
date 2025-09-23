import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os

STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"

# -------------------------------
# Initialize state.json if not exists
# -------------------------------
if not os.path.exists(STATE_FILE):
    state = {
        "game_started": False,
        "current_question": 0,
        "scores": []
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Load state
# -------------------------------
with open(STATE_FILE, "r") as f:
    state = json.load(f)

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

QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Player", "Host"])

# -------------------------------
# Host Screen
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code below to join:")

    # QR code
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)

    st.write(f"Players joined: {len(state['scores'])}")
    
    if not state["game_started"]:
        if st.button("Start Game"):
            state["game_started"] = True
            state["current_question"] = 0
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
            st.success("Game started!")
    else:
        st.write(f"Game in progress... Current Question: {state['current_question'] + 1}/{len(questions)}")
        df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False).head(3)
        st.subheader("🏆 Leaderboard - Top 3")
        st.table(df)

# -------------------------------
# Player Screen
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    else:
        st.write(f"Welcome, **{st.session_state.player_name}**!")

        # Wait for host to start
        if not state["game_started"]:
            st.warning("Waiting for host to start the game...")
            st.stop()

        q_index = state["current_question"]
        if q_index >= len(questions):
            st.success("Game finished!")
            df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False).head(3)
            st.subheader("🏆 Leaderboard - Top 3")
            st.table(df)
            st.stop()

        q = questions[q_index]

        if "selected_answer" not in st.session_state:
            st.session_state.selected_answer = None
        if "answered" not in st.session_state:
            st.session_state.answered = False
        if "start_time" not in st.session_state:
            st.session_state.start_time = time.time()
        if "feedback_time" not in st.session_state:
            st.session_state.feedback_time = None

        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, QUESTION_TIME - elapsed)

        st.write(f"**Question {q_index + 1}: {q['question']}**")
        st.session_state.selected_answer = st.radio(
            "Choose your answer:",
            q["options"],
            index=0,
            key=f"q{q_index}"
        )

        st.write(f"⏳ Time left: {remaining} sec")

        if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.feedback_time = time.time()

            # Load state again for score update
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            # Update score
            correct = st.session_state.selected_answer == q["answer"]
            found = False
            for s in state["scores"]:
                if s["name"] == st.session_state.player_name:
                    if correct:
                        s["score"] += POINTS_PER_QUESTION
                    found = True
            if not found:
                state["scores"].append({
                    "name": st.session_state.player_name,
                    "score": POINTS_PER_QUESTION if correct else 0
                })

            with open(STATE_FILE, "w") as f:
                json.dump(state, f)

        # Feedback display
        if st.session_state.answered:
            if st.session_state.selected_answer == q["answer"]:
                st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
            else:
                st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

            elapsed_feedback = time.time() - st.session_state.feedback_time
            if elapsed_feedback > FEEDBACK_TIME:
                # Move to next question
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                if state["current_question"] < len(questions) - 1:
                    state["current_question"] += 1
                    with open(STATE_FILE, "w") as f:
                        json.dump(state, f)
                st.session_state.selected_answer = None
                st.session_state.answered = False
                st.session_state.start_time = time.time()
                st.experimental_rerun()
            else:
                st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
                time.sleep(1)
                st.experimental_rerun()
        else:
            time.sleep(1)
            st.experimental_rerun()
