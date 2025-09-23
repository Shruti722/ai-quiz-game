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
# CONFIGURATION
# -------------------------------
STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"  # your deployed app URL
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# Configure Gemini API (replace with your API key directly)
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y api")  # replace with your actual key

# -------------------------------
# STATE MANAGEMENT
# -------------------------------
if not os.path.exists(STATE_FILE):
    state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "players": [], "questions": []}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# QUESTION GENERATION
# -------------------------------
def get_ai_questions():
    """Generate 5 questions using Gemini API, fallback to defaults if fails quickly"""
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
        model = genai.GenerativeModel("gemini-1.5-turbo")  # faster than flash
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        if len(questions) == 5:
            return questions
    except Exception:
        pass

    # fallback
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
# AUTO REFRESH
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# APP MODE SELECTION
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# HOST SCREEN
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    state = load_state()

    # QR code for players
    st.subheader("📱 Share with Players")
    st.markdown(f"[Or click here to join as Player]({GAME_URL})")
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)

    st.write(f"Players joined: {len(state.get('players', []))}")

    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started! Players can now see the first question.")

    if st.button("🔄 Restart Game"):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "players": [], "questions": []}
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    # Leaderboard / Progress
    if state["game_started"]:
        if state.get("game_over", False):
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_question'] + 1}/{len(state['questions'])}")
            if state['scores']:
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

    st.write(f"Welcome, **{st.session_state.player_name}**!")

    state = load_state()

    # Add player if not already in state
    if st.session_state.player_name not in state.get("players", []):
        state.setdefault("players", []).append(st.session_state.player_name)
        save_state(state)

    if not state.get("game_started", False):
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state['scores']:
            df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
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
    q_index = state["current_question"]
    q = state["questions"][q_index]

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"q{q_index}",
        index=0
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]

        # Update scores
        state = load_state()
        found = False
        for s in state.get("scores", []):
            if s["name"] == st.session_state.player_name:
                if correct:
                    s["score"] += POINTS_PER_QUESTION
                found = True
        if not found:
            state.setdefault("scores", []).append({
                "name": st.session_state.player_name,
                "score": POINTS_PER_QUESTION if correct else 0
            })
        save_state(state)

    # Show feedback
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    # Move to next question
    if elapsed >= QUESTION_TIME:
        state = load_state()
        if q_index < len(state["questions"]) - 1:
            state["current_question"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
