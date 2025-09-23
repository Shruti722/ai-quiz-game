import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
import google.generativeai as genai

STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Initialize state.json if not exists
# -------------------------------
default_state = {
    "game_started": False,
    "current_question": 0,
    "players": {},
    "scores": [],
    "questions": [],
    "game_over": False
}

if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, "w") as f:
        json.dump(default_state, f)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# AI question generation
# -------------------------------
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y api")  # replace with your API key

def get_ai_questions():
    prompt = """
    Create 5 multiple-choice quiz questions about Data Literacy and AI Agents.
    Provide as JSON with keys: question, options, answer.
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
# Determine mode from query params
# -------------------------------
role = st.sidebar.radio("Select mode:", ["Host", "Player"])
query_params = st.query_params
if query_params.get("role", [""])[0].lower() == "player":
    role = "Player"
elif query_params.get("role", [""])[0].lower() == "host":
    role = "Host"

state = load_state()

# -------------------------------
# Host Screen
# -------------------------------
if role == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code below to join:")

    # QR Code
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"Or [click here to join as Player]({GAME_URL})")

    st.write(f"Players joined: {len(state.get('players', {}))}")

    if not state.get("game_started", False):
        if st.button("🚀 Start Game"):
            state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started! Players can now see the first question.")

    if st.button("🔄 Restart Game"):
        state = default_state.copy()
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    # Show progress / leaderboard
    if state.get("game_started", False):
        if state.get("game_over", False):
            st.success("🎉 Game Over! Final Leaderboard:")
            scores = state.get("scores", [])
            if scores:
                df = pd.DataFrame(scores).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state.get('current_question', 0)+1} / {len(state.get('questions', []))}")
            scores = state.get("scores", [])
            if scores:
                df = pd.DataFrame(scores).sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# Player Screen
# -------------------------------
if role == "Player":
    st.title("🎮 Quiz Game Player")
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    if not st.session_state.player_name:
        st.stop()

    name = st.session_state.player_name
    if name not in state.get("players", {}):
        state["players"][name] = 0
        save_state(state)

    st.write(f"Welcome, **{name}**!")

    if not state.get("game_started", False):
        st.info("⏳ Waiting for host to start the game...")
        st.stop()

    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        scores = state.get("scores", [])
        if scores:
            df = pd.DataFrame(scores).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # Initialize session state
    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Current question
    q_index = state.get("current_question", 0)
    questions = state.get("questions", [])
    if q_index >= len(questions):
        st.success("🎉 Game Over! Thank you for playing.")
        st.stop()

    q = questions[q_index]
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index+1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q.get("options", []),
        key=f"{name}_{q_index}"
    )
    st.write(f"⏳ Time left: {remaining} sec")

    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q.get("answer")
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

    if st.session_state.answered:
        if st.session_state.selected_answer == q.get("answer"):
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q.get('answer')}")

    # Move to next question after timer ends
    if elapsed >= QUESTION_TIME:
        if q_index < len(questions) - 1:
            state["current_question"] = q_index + 1
        else:
            state["game_over"] = True
        save_state(state)
        # reset session
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
        st.experimental_rerun()
