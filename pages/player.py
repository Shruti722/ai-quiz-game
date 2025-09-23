import streamlit as st
import time
import json

STATE_FILE = "state.json"
QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# -------------------------------
# Helpers
# -------------------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        state.setdefault("started", False)
        state.setdefault("current_q", 0)
        state.setdefault("players", {})
        state.setdefault("questions", [])
        state.setdefault("question_start", None)
        return state
    except:
        return {"started": False, "current_q": 0, "players": {}, "questions": [], "question_start": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Player UI
# -------------------------------
st.title("🎮 AI-Powered Quiz Game - Player")
state = load_state()

# Player name input
if "player_name" not in st.session_state:
    st.session_state.player_name = ""

if not st.session_state.player_name:
    name = st.text_input("Enter your name:")
    if st.button("Join Game") and name:
        st.session_state.player_name = name
        if name not in state["players"]:
            state["players"][name] = 0
        save_state(state)
        st.success(f"Welcome {name}! Waiting for host to start...")
    st.stop()

player = st.session_state.player_name

if not state["started"]:
    st.info("⏳ Waiting for host to start the game...")
    st.stop()

q_index = state["current_q"]
questions = state["questions"]
q = questions[q_index]

if "answered" not in st.session_state:
    st.session_state.answered = False
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None

# Timer
elapsed = int(time.time() - state["question_start"])
remaining = max(0, QUESTION_TIME - elapsed)

st.subheader(f"❓ Question {q_index + 1}: {q['question']}")
st.session_state.selected_answer = st.radio("Choose your answer:", q["options"], key=f"q{q_index}")
st.write(f"⏳ Time left: {remaining} sec")

if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
    st.session_state.answered = True
    st.session_state.feedback_time = time.time()
    if st.session_state.selected_answer == q["answer"]:
        state["players"][player] += POINTS_PER_QUESTION
    save_state(state)

# Feedback
if st.session_state.answered:
    if st.session_state.selected_answer == q["answer"]:
        st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
    else:
        st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    elapsed_feedback = time.time() - st.session_state.feedback_time
    if elapsed_feedback > FEEDBACK_TIME:
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.rerun()
    else:
        st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
        time.sleep(1)
        st.rerun()
else:
    time.sleep(1)
    st.rerun()

# Leaderboard
st.subheader("🏆 Leaderboard - Top 3")
if state["players"]:
    df = pd.DataFrame(list(state["players"].items()), columns=["Name","Score"]).sort_values(by="Score", ascending=False).head(3)
    st.table(df)
