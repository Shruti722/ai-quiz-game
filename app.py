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
# Configuration
# -------------------------------
STATE_FILE = "state.json"
GAME_URL = "https://your-streamlit-app-url/?role=Player"  # Replace with your app's public URL
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Configure Gemini API (replace with your API key)
# -------------------------------
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")

# -------------------------------
# Initialize state.json if not exists
# -------------------------------
if not os.path.exists(STATE_FILE):
    state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "players": {}, "questions": []}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# State functions
# -------------------------------
def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Fallback static questions
# -------------------------------
STATIC_QUESTIONS = [
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
# Auto-refresh for real-time updates
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# Generate AI Questions
# -------------------------------
def get_ai_questions():
    prompt = """
    Create 5 multiple-choice quiz questions about Data Literacy and AI Agents.
    Provide them as a JSON list with keys: question, options, answer.
    Example:
    [
      {"question": "What is structured data?", 
       "options": ["Images", "Tables with rows/columns", "Videos", "Audio"], 
       "answer": "Tables with rows/columns"}
    ]
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-turbo")  # faster
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        if len(questions) < 5:
            return STATIC_QUESTIONS
        return questions
    except Exception:
        return STATIC_QUESTIONS

# -------------------------------
# Select Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# HOST SCREEN
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")

    state = load_state()

    # Show QR code and clickable link
    st.subheader("📱 Players Join")
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.markdown(f"[Or click here to join as Player]({GAME_URL})")

    # Show number of players joined
    st.write(f"Players joined: {len(state.get('players', {}))}")

    # Start Game
    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started!")

    # Restart Game
    if st.button("🔄 Restart Game"):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "players": {}, "questions": []}
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    # Game progress / leaderboard
    state = load_state()
    if state["game_started"]:
        if state.get("game_over", False):
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_question'] + 1}/{len(state.get('questions', STATIC_QUESTIONS))}")
            if state.get('scores'):
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# PLAYER SCREEN
# -------------------------------
else:
    st.title("🎮 Quiz Game Player")

    # Player name input
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")
    if not st.session_state.player_name:
        st.stop()
    name = st.session_state.player_name
    st.write(f"Welcome, **{name}**!")

    # Load state and register player
    state = load_state()
    if name not in state.get("players", {}):
        state.setdefault("players", {})[name] = 0
        save_state(state)

    # Waiting for host
    if not state.get("game_started", False):
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    # Game over
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
    q_index = state.get("current_question", 0)
    questions = state.get("questions", STATIC_QUESTIONS)
    if q_index >= len(questions):
        st.success("🎉 Game Over!")
        st.stop()
    q = questions[q_index]

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"{name}_{q_index}"
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        state = load_state()
        correct = st.session_state.selected_answer == q["answer"]
        found = False
        for s in state.get("scores", []):
            if s["name"] == name:
                if correct:
                    s["score"] += POINTS_PER_QUESTION
                found = True
        if not found:
            state.setdefault("scores", []).append({
                "name": name,
                "score": POINTS_PER_QUESTION if correct else 0
            })
        save_state(state)

    # Show feedback
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    # Move to next question after timer
    if elapsed >= QUESTION_TIME:
        state = load_state()
        if q_index < len(questions) - 1:
            state["current_question"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        # Reset session for next question
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False

# -------------------------------
# Admin reset
# -------------------------------
st.sidebar.subheader("⚙️ Admin Controls")
if st.sidebar.button("🔄 Reset Game"):
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    st.sidebar.success("Game reset!")
