import streamlit as st
import qrcode
from io import BytesIO
import json

STATE_FILE = "state.json"

# Helpers
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
# Streamlit host screen
# -------------------------------
st.title("🎮 AI Quiz - Host Screen")

# QR code
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

# Load state
state = load_state()

if st.button("Start Game"):
    state["started"] = True
    save_state(state)
    st.success("✅ Game started!")

# Show current question index
st.write(f"Current question index: {state['current_q']}")

# Show live scores
st.subheader("🏆 Live Scores")
if state["players"]:
    import pandas as pd
    df = pd.DataFrame(state["players"].items(), columns=["Name", "Score"]).sort_values(by="Score", ascending=False)
    st.table(df)
else:
    st.write("No players yet.")
