import streamlit as st
import json
import random
import time
import qrcode
from io import BytesIO

STATE_FILE = "state.json"

# -------------------------------
# Helpers
# -------------------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"game_started": False, "current_q": 0, "players": {}}

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

    game_url = "http://localhost:8501/?role=player"  # change for deployment
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(game_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"Share this link: {game_url}")

    state = load_state()
    if st.button("Start Game"):
        state["game_started"] = True
        save_state(state)
        st.success("✅ Game started! Players should now see questions.")

# -------------------------------
# Player Screen
# -------------------------------
elif role == "player":
    st.title("🎮 AI-Powered Quiz Game")

    state = load_state()
    if "player_name" not in st.session_state:
        st.session_state.player_name = st.text_input("Enter your name:")

    if st.session_state.player_name:
        if st.session_state.player_name not in state["players"]:
            state["players"][st.session_state.player_name] = 0
            save_state(state)

        if not state["game_started"]:
            st.info("⏳ Waiting for host to start the game...")
        else:
            q_index = state["current_q"]
            if q_index < len(questions):
                q = questions[q_index]
                st.subheader(f"❓ {q['question']}")
                answer = st.radio("Choose your answer:", q["options"])
                if st.button("Submit"):
                    if answer == q["answer"]:
                        st.success("✅ Correct! +5 points")
                        state["players"][st.session_state.player_name] += 5
                    else:
                        st.error(f"❌ Wrong! Correct: {q['answer']}")
                    state["current_q"] += 1
                    save_state(state)
                    st.experimental_rerun()
            else:
                st.success("🎉 Quiz Over!")
                leaderboard = sorted(state["players"].items(), key=lambda x: x[1], reverse=True)[:3]
                st.table(leaderboard)
