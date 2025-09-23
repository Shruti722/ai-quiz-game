import streamlit as st
import json
import os

STATE_FILE = "state.json"

# ---------------------------
# Helpers
# ---------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"started": False, "current_q": 0, "players": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ---------------------------
# Role Detection
# ---------------------------
params = st.query_params  # Streamlit v1.32+
role = params.get("role", ["host"])[0]  # default = host

state = load_state()

# ---------------------------
# Host Screen
# ---------------------------
if role == "host":
    st.title("🎮 Quiz Game - Host Screen")

    if not state["started"]:
        if st.button("🚀 Start Game"):
            state["started"] = True
            state["current_q"] = 1
            save_state(state)
            st.success("Game started!")
    else:
        st.write(f"Game already started. Current Q: {state['current_q']}")

    if st.button("🔄 Reset Game"):
        state = {"started": False, "current_q": 0, "players": {}}
        save_state(state)
        st.warning("Game reset!")

# ---------------------------
# Player Screen
# ---------------------------
elif role == "player":
    st.title("🎮 Quiz Game - Player")

    name = st.text_input("Enter your name:")

    if name and name not in state["players"]:
        state["players"][name] = 0
        save_state(state)
        st.success(f"Welcome, {name}! Waiting for host to start...")

    if state["started"]:
        st.info(f"Game started! Current Q: {state['current_q']}")
    else:
        st.warning("Waiting for host to start...")
