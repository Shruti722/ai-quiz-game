import streamlit as st
import qrcode
import base64
from io import BytesIO
import json

# -------------------------------
# Config
# -------------------------------
STATE_FILE = "state.json"
game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"

# -------------------------------
# Helpers
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

def generate_qr(url: str):
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"

# -------------------------------
# Host UI
# -------------------------------
st.title("🎮 Host Screen")

# Load current state
state = load_state()

# QR code pointing to PLAYER page
qr_img = generate_qr(game_url + "/player")   # ✅ directs players to /player
st.image(qr_img, caption="Scan to join the game")

# Show joined players
if state["players"]:
    st.subheader("👥 Joined Players")
    for name in state["players"].keys():
        st.write(f"- {name}")
else:
    st.info("Waiting for players to join...")

# Start game button
if st.button("🚀 Start Game"):
    state = {"started": True, "current_q": 0, "players": state["players"]}
    save_state(state)
    st.success("Game started! Players should now see the first question.")

# Leaderboard
if state["players"]:
    st.subheader("🏆 Leaderboard")
    sorted_scores = sorted(state["players"].items(), key=lambda x: x[1], reverse=True)
    for i, (name, score) in enumerate(sorted_scores[:3], start=1):
        st.write(f"{i}. {name} - {score} pts")
