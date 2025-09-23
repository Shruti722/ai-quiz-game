import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
import google.generativeai as genai
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Configurations
# -------------------------------
STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"  # your app URL
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Gemini API
# -------------------------------
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y api")  # directly place API key here

# -------------------------------
# Load/Save state
# -------------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"game_started": False, "current_question": 0, "players": {}, "scores": [], "game_over": False, "questions": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def reset_game():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

# -------------------------------
# Generate questions via AI or fallback
# -------------------------------
def get_ai_questions():
    prompt = """
    Generate 5 multiple-choice quiz questions about Data Literacy and AI Agents.
    Return as JSON list with keys: question, options, answer.
    Example: [{"question": "What is structured data?", "options":["Images","Tables","Videos","Audio"], "answer":"Tables"}]
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-turbo")
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        if len(questions) < 5:
            raise Exception("Not enough questions returned")
        return questions
    except Exception:
        # fallback static questions
        return [
            {"question": "Which of the following best describes structured data?",
             "options": ["Images", "Tables with rows and columns", "Videos", "Audio"],
             "answer": "Tables with rows and columns"},
            {"question": "What is the primary purpose of data visualization?",
             "options": ["Encrypt data", "Analyze trends and patterns", "Store data", "Delete data"],
             "answer": "Analyze trends and patterns"},
            {"question": "What is the main function of an AI agent?",
             "options": ["Sense, Decide, Act", "Store data", "Only predict numbers", "Encrypt files"],
             "answer": "Sense, Decide, Act"},
            {"question": "Which of these is an example of an AI agent?",
             "options": ["ChatGPT", "Word Document", "Excel File", "PowerPoint"],
             "answer": "ChatGPT"},
            {"question": "Which feature can AI agents have?",
             "options": ["Learning from environment", "Only remembering static data", "Watching videos", "Printing documents"],
             "answer": "Learning from environment"},
        ]

# -------------------------------
# Auto-refresh every 1 sec
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.radio("Select mode:", ["Host", "Player"])

# -------------------------------
# HOST SCREEN
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    state = load_state()

    # QR Code + clickable link
    st.subheader("📱 Players join here")
    qr = qrcode.make(GAME_URL)
    buf = BytesIO()
    qr.save(buf)
    st.image(buf, width=200)
    st.markdown(f"[Or click here to join as Player]({GAME_URL})", unsafe_allow_html=True)

    # Show joined players
    state.setdefault("players", {})
    st.write(f"Players joined: {len(state['players'])}")

    # Start Game
    if not state.get("game_started", False):
        if st.button("🚀 Start Game"):
            state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started! Players can now see the first question.")

    # Restart Game
    if st.button("🔄 Restart Game"):
        reset_game()
        st.success("Game has been reset! Players can rejoin.")

    # Show progress/leaderboard
    if state.get("game_started", False):
        if state.get("game_over", False):
            st.success("🎉 Game Over! Final Leaderboard:")
            if state.get('scores'):
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_question']+1}/{len(state['questions'])}")
            if state.get('scores'):
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# PLAYER SCREEN
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    if not st.session_state.player_name:
        st.stop()

    name = st.session_state.player_name
    state = load_state()
    state.setdefault("players", {})
    state.setdefault("scores", [])

    # Register player
    if name not in state["players"]:
        state["players"][name] = 0
        save_state(state)

    st.write(f"Welcome, **{name}**!")

    if not state.get("game_started", False):
        st.info("⏳ Waiting for host to start the game...")
        st.stop()

    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state.get('scores'):
            df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # Initialize session state for question
    if "start_time" not in st.session_state or st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Current question
    q_index = state["current_question"]
    q = state["questions"][q_index]

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"{name}_{q_index}",
        index=0
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]
        found = False
        for s in state["scores"]:
            if s["name"] == name:
                if correct:
                    s["score"] += POINTS_PER_QUESTION
                found = True
        if not found:
            state["scores"].append({"name": name, "score": POINTS_PER_QUESTION if correct else 0})
        save_state(state)

    # Show feedback
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    # Move to next question after timer ends
    if elapsed >= QUESTION_TIME:
        if q_index < len(state["questions"]) - 1:
            state["current_question"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        # Reset session state
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False

# -------------------------------
# Admin Reset
# -------------------------------
st.sidebar.subheader("⚙️ Admin Controls")
if st.sidebar.button("🔄 Reset Game"):
    reset_game()
    st.sidebar.success("Game reset!")
