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

# -------------------------------
# Configure Gemini API
# -------------------------------
# Replace "YOUR_API_KEY" with your Gemini API key
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")

# -------------------------------
# Load / Save state
# -------------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"players": {}, "current_q": 0, "game_started": False, "questions": [], "game_over": False}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def reset_game():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

# -------------------------------
# Static fallback questions
# -------------------------------
def get_fallback_questions():
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
# Generate AI questions
# -------------------------------
def get_ai_questions(timeout=3):
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
        # Use timeout parameter to reduce wait time
        response = model.generate_content(prompt, timeout=timeout)
        questions = json.loads(response.text)
        # Ensure exactly 5 questions
        if len(questions) != 5:
            return get_fallback_questions()
        return questions
    except Exception:
        return get_fallback_questions()

# -------------------------------
# Auto-refresh every 1 sec
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App Mode detection (Host / Player)
# -------------------------------
query_params = st.query_params
mode_param = query_params.get("role", [""])[0]

if mode_param == "Host":
    mode = "Host"
elif mode_param == "Player":
    mode = "Player"
else:
    mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# HOST SCREEN
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code or click the link below to join:")

    # QR Code + link
    player_url = f"{GAME_URL}?role=Player"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(player_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"[Click here to join as Player]({player_url})")

    state = load_state()
    st.write(f"Players joined: {len(state['players'])}")

    # Start game
    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["questions"] = get_ai_questions(timeout=3)  # AI-generated questions with short timeout
            state["game_started"] = True
            state["current_q"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started! Players can now see the first question.")

    # Restart game
    if st.button("🔄 Restart Game"):
        reset_game()
        st.success("Game has been reset! Players can rejoin.")

    # Show progress / leaderboard
    state = load_state()
    if state["game_started"]:
        if state["game_over"]:
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['players']:
                df = pd.DataFrame(
                    [{"name": k, "score": v} for k, v in state['players'].items()]
                ).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df)
        else:
            st.write(f"Game in progress... Question {state['current_q'] + 1}/5")
            if state['players']:
                df = pd.DataFrame(
                    [{"name": k, "score": v} for k, v in state['players'].items()]
                ).sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df)

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
    st.write(f"Welcome, **{name}**!")

    state = load_state()
    if name not in state["players"]:
        state["players"][name] = 0
        save_state(state)
        state = load_state()

    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state['players']:
            df = pd.DataFrame(
                [{"name": k, "score": v} for k, v in state['players'].items()]
            ).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df)
        st.stop()

    # Initialize session state for question
    if "start_time" not in st.session_state or st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Current question
    q_index = state["current_q"]
    questions = state.get("questions", get_fallback_questions())
    q = questions[q_index]

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
    if st.button("Submit", key=f"submit_{name}_{q_index}") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]
        if correct:
            st.success(f"✅ Correct! (+{POINTS_PER_QUESTION} points)")
            state["players"][name] += POINTS_PER_QUESTION
        else:
            st.error(f"❌ Incorrect! Correct answer: {q['answer']}")
        save_state(state)

    # Move to next question after timer ends
    if elapsed >= QUESTION_TIME:
        state = load_state()
        if q_index < len(questions) - 1:
            state["current_q"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        # Reset session for next question
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
