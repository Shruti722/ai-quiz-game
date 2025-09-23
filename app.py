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
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# Configure Gemini API
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")  # Replace with your API key

# -------------------------------
# State functions
# -------------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"players": {}, "current_q": 0, "game_started": False, "questions": [], "game_over": False}
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    # Ensure all keys exist
    if "players" not in state:
        state["players"] = {}
    if "current_q" not in state:
        state["current_q"] = 0
    if "game_started" not in state:
        state["game_started"] = False
    if "questions" not in state:
        state["questions"] = []
    if "game_over" not in state:
        state["game_over"] = False
    return state

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def reset_game():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

# -------------------------------
# Static fallback questions
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
# Generate AI questions (pre-generated for speed)
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
        model = genai.GenerativeModel("gemini-1.5-turbo")
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        if len(questions) < 5:
            raise Exception("AI returned less than 5 questions, fallback")
        return questions
    except Exception:
        # Fallback to static questions immediately
        return STATIC_QUESTIONS

# -------------------------------
# Auto-refresh every 1 sec
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])
state = load_state()

# -------------------------------
# Host Screen
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code below to join:")

    # Player QR code & link
    player_link = f"{GAME_URL}?mode=Player"
    qr = qrcode.make(player_link)
    buf = BytesIO()
    qr.save(buf)
    st.image(buf, caption="Scan to join as Player", width=200)
    st.markdown(f"[Or click here to join as Player]({player_link})")

    st.write(f"Players joined: {len(state['players'])}")

    # Start Game
    if not state["game_started"]:
        if st.button("Start Game"):
            if not state["questions"]:
                state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_q"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started!")

    # Restart Game
    if st.button("Restart Game"):
        reset_game()
        state = load_state()
        st.success("Game has been reset! Players can rejoin.")

    # Show leaderboard or progress
    if state["game_started"]:
        if state["game_over"]:
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['players']:
                df = pd.DataFrame([{"name": n, "score": s} for n, s in state['players'].items()])
                df = df.sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_q'] + 1}/{len(state['questions'])}")
            if state['players']:
                df = pd.DataFrame([{"name": n, "score": s} for n, s in state['players'].items()])
                df = df.sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# Player Screen
# -------------------------------
else:
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    if not st.session_state.player_name:
        st.stop()

    player_name = st.session_state.player_name
    if player_name not in state["players"]:
        state["players"][player_name] = 0
        save_state(state)

    st.write(f"Welcome, **{player_name}**!")

    # Waiting for host
    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    # Game Over
    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state['players']:
            df = pd.DataFrame([{"name": n, "score": s} for n, s in state['players'].items()])
            df = df.sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # Initialize session for question
    if "start_time" not in st.session_state or st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Current question
    q_index = state["current_q"]
    q = state["questions"][q_index]
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"{player_name}_{q_index}",
        index=0
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]
        if correct:
            state["players"][player_name] += POINTS_PER_QUESTION
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")
        save_state(state)

    # Move to next question after timer
    if elapsed >= QUESTION_TIME:
        if q_index < len(state["questions"]) - 1:
            state["current_q"] += 1
        else:
            state["game_over"] = True
        save_state(state)
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
