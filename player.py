import streamlit as st
import json
import time

STATE_FILE = "state.json"
QUESTIONS_FILE = "questions.json"

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

st.title("🎮 AI-Powered Quiz Game")

# Player enters name
if "name" not in st.session_state:
    st.session_state.name = st.text_input("Enter your name to join:")
    if st.session_state.name:
        state = load_state()
        state["players"][st.session_state.name] = 0
        save_state(state)
        st.success("You’ve joined the game! Wait for host to start.")
    st.stop()

name = st.session_state.name

# Main quiz loop
state = load_state()

if not state["started"]:
    st.info("⏳ Waiting for host to start the game...")
    st.stop()

q_idx = state["current_q"]

if q_idx >= len(QUESTIONS):
    st.success("🎉 Game finished! Thanks for playing.")
    st.stop()

question = QUESTIONS[q_idx]
st.subheader(f"Question {q_idx+1}: {question['question']}")
choice = st.radio("Choose your answer:", question["options"], index=None)

# Timer
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

elapsed = int(time.time() - st.session_state.start_time)
remaining = max(0, 15 - elapsed)
st.write(f"⏳ Time left: {remaining} sec")

if remaining == 0:
    if choice == question["answer"]:
        st.success("✅ Correct! +5 points")
        state["players"][name] += 5
    else:
        st.error(f"❌ Wrong! Correct answer: {question['answer']}")
    save_state(state)

    # Feedback countdown
    for i in range(3, 0, -1):
        st.write(f"Next question in {i}...")
        time.sleep(1)

    # Reset timer
    st.session_state.start_time = time.time()
    st.rerun()
