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
# Player UI
# -------------------------------
st.title("🎮 Player Screen")

# Load state
state = load_state()

# Player name input
if "player_name" not in st.session_state:
    name = st.text_input("Enter your name:")
    if st.button("Join Game") and name:
        state["players"][name] = 0
        save_state(state)
        st.session_state["player_name"] = name
        st.success(f"Welcome {name}! Waiting for game to start...")

# If already joined
if "player_name" in st.session_state:
    player = st.session_state["player_name"]

    if not state["started"]:
        st.info("⏳ Waiting for host to start the game...")
    else:
        # Placeholder questions for now
        questions = [
            {"q": "What is 2 + 2?", "options": ["3", "4", "5"], "answer": "4"},
            {"q": "What is the capital of France?", "options": ["Paris", "Rome", "Berlin"], "answer": "Paris"}
        ]

        q_index = state["current_q"]
        if q_index < len(questions):
            question = questions[q_index]

            st.subheader(f"❓ {question['q']}")

            # Answer input
            choice = st.radio("Choose your answer:", question["options"], key=f"q{q_index}")
            if st.button("Submit Answer"):
                if choice == question["answer"]:
                    st.success("✅ Correct! +5 points")
                    state["players"][player] += 5
                else:
                    st.error("❌ Wrong answer")

                # Move to next question after short pause
                save_state(state)
                time.sleep(3)
                state["current_q"] += 1
                save_state(state)
                st.rerun()
        else:
            st.success("🎉 Game Over! Check the leaderboard on host screen.")
