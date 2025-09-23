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
            return json.load(f)
    except:
        return {"started": False, "current_q": 0, "players": {}, "questions": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Player UI
# -------------------------------
st.title("🎮 Player Screen")

# Load shared state
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
        st.success(f"Welcome {name}! Waiting for host to start the game...")
    st.stop()

player = st.session_state.player_name

if not state["started"]:
    st.info("⏳ Waiting for host to start the game...")
    st.stop()

# Initialize player session state
if "q_index" not in st.session_state:
    st.session_state.q_index = state["current_q"]
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "answered" not in st.session_state:
    st.session_state.answered = False
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None

questions = state["questions"]

# -------------------------------
# Quiz Loop
# -------------------------------
if st.session_state.q_index < len(questions):
    q = questions[st.session_state.q_index]

    # Start question timer
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.subheader(f"❓ Question {st.session_state.q_index + 1}: {q['question']}")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"q{st.session_state.q_index}"
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer or timeout
    if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
        st.session_state.answered = True
        st.session_state.feedback_time = time.time()
        if st.session_state.selected_answer == q["answer"]:
            state["players"][player] += POINTS_PER_QUESTION
        save_state(state)

    # Show feedback
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

        elapsed_feedback = time.time() - st.session_state.feedback_time
        if elapsed_feedback > FEEDBACK_TIME:
            st.session_state.q_index += 1
            st.session_state.start_time = None
            st.session_state.answered = False
            st.session_state.selected_answer = None
            state["current_q"] = st.session_state.q_index
            save_state(state)
            st.rerun()
        else:
            st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
            time.sleep(1)
            st.rerun()
    else:
        time.sleep(1)
        st.rerun()

# -------------------------------
# Quiz finished
# -------------------------------
else:
    st.success("🎉 Quiz Finished!")
    st.subheader(f"Your score: {state['players'][player]}")
    st.subheader("🏆 Leaderboard - Top 3")
    df = pd.DataFrame(list(state["players"].items()), columns=["Name","Score"]).sort_values(by="Score", ascending=False).head(3)
    st.table(df)
