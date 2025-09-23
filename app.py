import streamlit as st
import qrcode, base64, json
from io import BytesIO

game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"
STATE_FILE = "state.json"

def load_state():
    try:
        return json.load(open(STATE_FILE))
    except:
        return {"started": False, "current_q": 0, "players": {}}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w"))

def generate_qr(url):
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"

st.title("🎮 Host Screen")

state = load_state()

qr_img = generate_qr(game_url + "/player")   # ✅ players go to player page
st.image(qr_img, caption="Scan to join as Player")

if st.button("🚀 Start Game"):
    state = {"started": True, "current_q": 0, "players": {}}
    save_state(state)
    st.success("Game started!")
