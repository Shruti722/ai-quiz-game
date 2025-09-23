import streamlit as st
import json
import time

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
# Question bank
# -------------------------------
questions = [
    {"q": "What is 2 + 2?", "options": ["3", "4", "5"], "answer": "4"},
    {"q": "What is the capital of France?", "options": ["Paris", "Rome", "Berlin"], "answer": "Paris"},
    {"q": "What is the main function of an AI agent?", "options": ["Sense, Decide, Act", "Store data", "Encrypt files"], "answer": "Sense, Decide, Act"}
]

# -------------------------------
# Player UI
# -------------------------------
st.title("🎮 Player Screen")

# Player name input
if "player_name" not in st.session_state:
    name = st.text_input("Enter your name:")
    if st.button("Join Game") and name:
        state = load_state()
        if name not in state["players"]:
            state["players"][name] = 0
        save_state(state)
        st.session_state["player_name"] = name
        st.success(f"Welcome {name}! Waiting for host to start...")

# If already joined
if "player_name" in st.session_state:
    player = st.session_state["player_name"]
    state = load_state()
    
    if not state["started"]:
        st.info("⏳ Waiting for host to start the game...")
        st.stop()
    
    # Current question
    q_index = state["current_q"]
    
    if q_index < len(questions):
        question = questions[q_index]
        st.subheader(f"❓ {question['q']}")
        
        # Answer input
        if "answered" not in st.session_state:
            st.session_state["answered"] = False
        
        if not st.session_state["answered"]:
            choice = st.radio("Choose your answer:", question["options"])
            if st.button("Submit Answer"):
                st.session_state["answered"] = True
                if choice == question["answer"]:
                    state["players"][player] += 5
                    st.success("✅ Correct! +5 points")
                else:
                    st.error(f"❌ Wrong! Correct answer: {question['answer']}")
                save_state(state)
                time.sleep(3)  # feedback delay
                state["current_q"] += 1
                save_state(state)
                st.session_state["answered"] = False
                st.experimental_rerun()
    else:
        st.success("🎉 Game Over! Check leaderboard on host screen.")
