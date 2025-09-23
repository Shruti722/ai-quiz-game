import streamlit as st
import qrcode
import base64
import json
import time
from io import BytesIO

STATE_FILE = "state.json"
QUESTIONS_FILE = "questions.json"

# Load questions
with open(QUESTIONS_FILE, "r") as f:
    QUESTIONS = json.load(f)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"started": False, "current_q": 0, "players": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def generate_qr(url):
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"

st.title("🎮 AI-Powered Quiz Game - Host")

state = load_state()

# QR Code for players to join
st.subheader("📱 Players join by scanning this QR code:")
qr_img = generate_qr("http://localhost:8502")  # change if deploying
st.image(qr_img)

# Start game button
if st.button("🚀 Start Game"):
    state["started"] = True
    state["current_q"] = 0
    state["players"] = {}
    save_state(state)
    st.success("Game started!")

# Move to next question manually (admin control if needed)
if st.button("➡️ Next Question"):
    if state["started"] and state["current_q"] < len(QUESTIONS) - 1:
        state["current_q"] += 1
        save_state(state)

# Leaderboard
st.subheader("🏆 Live Leaderboard - Top 3")
players = state["players"]
sorted_lb = sorted(players.items(), key=lambda x: x[1], reverse=True)[:3]
for i, (name, score) in enumerate(sorted_lb, 1):
    st.write(f"{i}. {name} - {score} points")
