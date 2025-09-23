import streamlit as st
import random
import pandas as pd
import time
import qrcode
import json
from io import BytesIO

STATE_FILE = "state.json"
QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# -------------------------------
# Helpers
# -------------------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"started": False, "current_q": 0, "players": {}, "questions": random.sample(questions, len(questions)), "question_start": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

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
query_params = st.query_params
role = query_params.get("role", ["host"])[0]  # default host

# -------------------------------
# Host Screen
# -------------------------------
if role == "host":
    st.title("🎮 AI-Powered Quiz Game - Host Screen")

    game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=player"

    # QR code
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
            st.success("✅ Game started! Players will now see questions.")
        st.stop()

    st.subheader(f"Current Question: {state['current_q'] + 1}/{len(state['questions'])}")
    q = state["questions"][state["current_q"]]
    st.write(f"❓ {q['question']}")
    st.write("Options: " + ", ".join(q["options"]))

    # Timer countdown
    if state["question_start"] is not None:
        elapsed = int(time.time() - state["question_start"])
        remaining = max(0, QUESTION_TIME - elapsed)
        st.write(f"⏳ Time left: {remaining} sec")

        if remaining == 0:
            if state["current_q"] + 1 < len(state["questions"]):
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

# -------------------------------
# Player Screen
# -------------------------------
elif role == "player":
    st.title("🎮 Player Screen")

    state = load_state()

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        name = st.text_input("Enter your name:")
        if st.button("Join Game") and name:
            st.session_state.player_name = name
            if name not in state["players"]:
                state["players"][name] = 0
            save_state(state)
            st.success(f"Welcome {name}! Waiting for host to start...")
        st.stop()

    player = st.session_state.player_name

    if not state["started"]:
        st.info("⏳ Waiting for host to start the game...")
        st.stop()

    q_index = state["current_q"]
    questions = state["questions"]
    q = questions[q_index]

    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Timer
    elapsed = int(time.time() - state["question_start"])
    remaining = max(0, QUESTION_TIME - elapsed)

    st.subheader(f"❓ Question {q_index + 1}: {q['question']}")
    st.session_state.selected_answer = st.radio("Choose your answer:", q["options"], key=f"q{q_index}")
    st.write(f"⏳ Time left: {remaining} sec")

    if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
        st.session_state.answered = True
        st.session_state.feedback_time = time.time()
        if st.session_state.selected_answer == q["answer"]:
            state["players"][player] += POINTS_PER_QUESTION
        save_state(state)

    # Feedback
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

        elapsed_feedback = time.time() - st.session_state.feedback_time
        if elapsed_feedback > FEEDBACK_TIME:
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.rerun()
        else:
            st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
            time.sleep(1)
            st.rerun()
    else:
        time.sleep(1)
        st.rerun()

    # Leaderboard
    st.subheader("🏆 Leaderboard - Top 3")
    if state["players"]:
        df = pd.DataFrame(list(state["players"].items()), columns=["Name","Score"]).sort_values(by="Score", ascending=False).head(3)
        st.table(df)
