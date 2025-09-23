import streamlit as st
import qrcode
from io import BytesIO
import json

STATE_FILE = "state.json"

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

# -------------------------------
# Host UI
# -------------------------------
st.title("🎮 Host Screen")

# Generate QR code for players
game_url = st.experimental_get_url().split("?")[0] + "?role=player"
qr = qrcode.QRCode(version=1, box_size=8, border=2)
qr.add_data(game_url)
qr.make(fit=True)
img = qr.make_image(fill='black', back_color='white')
buf = BytesIO()
img.save(buf)
st.image(buf, width=200)
st.write("📱 Ask players to scan this QR code to join!")

# Load state
state = load_state()

if not state["started"]:
    if st.button("Start Game"):
        state["started"] = True
        save_state(state)
        st.success("✅ Game started!")
else:
    st.info("Game is running... Players are answering questions.")

# Show current leaderboard
st.subheader("🏆 Current Leaderboard")
if state["players"]:
    import pandas as pd
    df = pd.DataFrame(list(state["players"].items()), columns=["Player", "Score"]).sort_values(by="Score", ascending=False)
    st.table(df)
else:
    st.write("No players joined yet.")
