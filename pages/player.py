import streamlit as st
import json
import time

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

# Question bank
questions = [
    {"q": "Which of the following best describes structured data?",
     "options": ["Images", "Tables with rows and columns", "Videos", "Audio"],
     "answer": "Tables with rows and columns"},
    {"q": "What is the primary purpose of data visualization?",
     "options": ["Encrypt data", "Analyze trends and patterns", "Store data", "Delete data"],
     "answer": "Analyze trends and patterns"},
    {"q": "What is the main function of an AI agent?",
     "options": ["Sense, Decide, Act", "Store data", "Only predict numbers", "Encrypt files"],
     "answer": "Sense, Decide, Act"},
    {"q": "Which of these is an example of an AI agent?",
     "options": ["ChatGPT", "Word Document", "Excel File", "PowerPoint"],
     "answer": "ChatGPT"},
    {"q": "Which feature can AI agents have?",
     "options": ["Learning from environment", "Only remembering static data", "Watching videos", "Printing documents"],
     "answer": "Learning from environment"},
]

QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# -------------------------------
# Player screen
# -------------------------------
st.title("🎮 Player Screen")

state = load_state()

# Player name
if "player_name" not in st.session_state:
    name = st.text_input("Enter your name:")
    if st.button("Join Game") and name:
        st.session_state.player_name = name
        if name not in state["players"]:
            state["players"][name] = 0
            save_state(state)
        st.success(f"Welcome {name}! Waiting for host...")

if "player_name" in st.session_state:
    player = st.session_state.player_name

    if not state["started"]:
        st.info("⏳ Waiting for host to start the game...")
        st.stop()

    # Current question
    q_index = state["current_q"]
    if q_index < len(questions):
        q = questions[q_index]

        # Timer start
        if "start_time" not in st.session_state or st.session_state.start_time is None:
            st.session_state.start_time = time.time()
            st.session_state.answered = False

        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, QUESTION_TIME - elapsed)

        st.subheader(f"❓ Question {q_index + 1}: {q['q']}")
        st.session_state.selected_answer = st.radio("Choose your answer:", q["options"], key=f"q{q_index}")
        st.write(f"⏳ Time left: {remaining} sec")

        if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.feedback_time = time.time()
            if st.session_state.selected_answer == q["answer"]:
                state["players"][player] += POINTS_PER_QUESTION
            save_state(state)

        # Feedback display
        if st.session_state.answered:
            if st.session_state.selected_answer == q["answer"]:
                st.success(f"✅ Correct! (+{POINTS_PER_QUESTION} points)")
            else:
                st.error(f"❌ Wrong! Correct answer: {q['answer']}")

            elapsed_feedback = time.time() - st.session_state.feedback_time
            st.write(f"➡️ Next question in {max(0, FEEDBACK_TIME - int(elapsed_feedback))} sec")
            if elapsed_feedback > FEEDBACK_TIME:
                st.session_state.start_time = None
                st.session_state.answered = False
                st.session_state.selected_answer = None
                st.rerun()
            else:
                st.experimental_rerun()
        else:
            # Auto-refresh timer
            st.experimental_rerun()

    else:
        st.success("🎉 Quiz Finished! Check leaderboard on host screen.")
