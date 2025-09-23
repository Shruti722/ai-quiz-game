import streamlit as st
import pandas as pd
import random
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
    state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Load state
# -------------------------------
with open(STATE_FILE, "r") as f:
    state = json.load(f)

# -------------------------------
# Question bank (5 questions)
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
POINTS_PER_QUESTION = 5

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

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

    # Start Game
    if not state["game_started"]:
        if st.button("Start Game"):
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
            st.success("Game started!")

    # Restart Game
    if st.button("Restart Game"):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        st.success("Game has been reset! Players can rejoin.")

    # Show leaderboard or progress
    if state["game_started"]:
        if state["game_over"]:
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_question'] + 1}/{len(questions)}")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# Player Screen
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    else:
        st.write(f"Welcome, **{st.session_state.player_name}**!")

        if not state["game_started"]:
            st.warning("Waiting for host to start the game...")
            st.stop()

        if state["game_over"]:
            st.success("🎉 Game Over! Thank you for playing.")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Final Leaderboard")
                st.table(df[["Rank", "name", "score"]])
            st.stop()

        q_index = state["current_question"]
        q = questions[q_index]

        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, QUESTION_TIME - elapsed)

        st.write(f"**Question {q_index + 1}: {q['question']}**")
        st.session_state.selected_answer = st.radio(
            "Choose your answer:",
            q["options"],
            key=f"q{q_index}"
        )
        st.write(f"⏳ Time left: {remaining} sec")

        # Submit button
        if st.button("Submit") and not st.session_state.answered:
            st.session_state.answered = True

            # Update score
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

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

        # Show feedback for full 15 sec
        if st.session_state.answered:
            if st.session_state.selected_answer == q["answer"]:
                st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
            else:
                st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

        # Move to next question after timer
        if elapsed >= QUESTION_TIME:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            if q_index < len(questions) - 1:
                state["current_question"] += 1
            else:
                state["game_over"] = True

            with open(STATE_FILE, "w") as f:
                json.dump(state, f)

            # Reset session state for next question
            st.session_state.selected_answer = None
            st.session_state.answered = False
            st.session_state.start_time = time.time()
            st.experimental_rerun()
