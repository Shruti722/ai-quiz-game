import streamlit as st
import json
import random
import time
import qrcode
from io import BytesIO
from pathlib import Path

STATE_FILE = Path("state.json")

# -------------------------------
# Helpers
# -------------------------------
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    else:
        return {"game_started": False, "current_q": 0, "players": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Config
# -------------------------------
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
# Role detection
# -------------------------------
role = "host"  # default
if "role" in st.query_params:
    role = st.query_params["role"][0]

# -------------------------------
# Initialize session state safely
# -------------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.player_name = ""
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.start_time = None
    st.session_state.feedback_time = None
    st.session_state.selected_answer = None

# -------------------------------
# Host Screen
# -------------------------------
if role == "host":
    st.title("🎮 AI-Powered Quiz Game - Host Screen")

    # Generate QR code for players
    game_url = st.get_url() + "?role=player"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(game_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"📱 Share this link with players: {game_url}")

    state = load_state()
    if st.button("Start Game") and not state["game_started"]:
        state["game_started"] = True
        state["current_q"] = 0
        state["players"] = {player: 0 for player in state.get("players", {})}  # reset scores
        save_state(state)
        st.success("✅ Game started!")

    # Show leaderboard
    if state["players"]:
        st.subheader("🏆 Leaderboard")
        leaderboard = sorted(state["players"].items(), key=lambda x: x[1], reverse=True)[:3]
        st.table(leaderboard)

# -------------------------------
# Player Screen
# -------------------------------
elif role == "player":
    st.title("🎮 AI-Powered Quiz Game - Player")

    state = load_state()

    # Enter player name
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your name:")

    if st.session_state.player_name:
        if st.session_state.player_name not in state["players"]:
            state["players"][st.session_state.player_name] = 0
            save_state(state)

        # Waiting for host
        if not state["game_started"]:
            st.info("⏳ Waiting for host to start the game...")
        else:
            q_index = state["current_q"]
            if q_index < len(questions):
                q = questions[q_index]

                # Timer initialization
                if st.session_state.start_time is None:
                    st.session_state.start_time = time.time()

                elapsed = int(time.time() - st.session_state.start_time)
                remaining = max(0, QUESTION_TIME - elapsed)

                st.subheader(f"❓ Question {q_index + 1}: {q['question']}")
                st.session_state.selected_answer = st.radio(
                    "Choose your answer:", q["options"], key=f"q{q_index}"
                )

                st.write(f"⏳ Time left: {remaining} sec")

                # Submit answer
                if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
                    st.session_state.answered = True
                    st.session_state.feedback_time = time.time()
                    if st.session_state.selected_answer == q["answer"]:
                        st.session_state.score += POINTS_PER_QUESTION
                        state["players"][st.session_state.player_name] = st.session_state.score
                        save_state(state)

                # Feedback
                if st.session_state.answered:
                    if st.session_state.selected_answer == q["answer"]:
                        st.success(f"✅ Correct! (+{POINTS_PER_QUESTION} points)")
                    else:
                        st.error(f"❌ Wrong! Correct answer: {q['answer']}")

                    elapsed_feedback = time.time() - st.session_state.feedback_time
                    if elapsed_feedback > FEEDBACK_TIME:
                        st.session_state.start_time = None
                        st.session_state.answered = False
                        st.session_state.selected_answer = None
                        state["current_q"] += 1
                        save_state(state)
                        st.experimental_rerun()
                    else:
                        st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
                        time.sleep(1)
                        st.experimental_rerun()
            else:
                st.success(f"🎉 Quiz Finished! Your score: {st.session_state.score}")
                st.subheader("🏆 Leaderboard - Top 3")
                leaderboard = sorted(state["players"].items(), key=lambda x: x[1], reverse=True)[:3]
                st.table(leaderboard)
