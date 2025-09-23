import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
import google.generativeai as genai
from streamlit_autorefresh import st_autorefresh

STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Configure Gemini API
# -------------------------------
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y api")  # replace with your API key

# -------------------------------
# Initialize state.json if not exists
# -------------------------------
if not os.path.exists(STATE_FILE):
    state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Fallback static questions (7)
# -------------------------------
fallback_questions = [
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
    {"question": "Fun fact: The first AI agent was created in which decade?",
     "options": ["1950s", "1970s", "1990s", "2000s"],
     "answer": "1950s"},
    {"question": "Fun fact: Which AI agent is known for beating human champions in Go?",
     "options": ["DeepBlue", "AlphaGo", "Watson", "GPT-3"],
     "answer": "AlphaGo"},
]

# -------------------------------
# Generate AI questions
# -------------------------------
def get_ai_questions():
    prompt = """
    Create 7 multiple-choice quiz questions about Data Literacy and AI Agents.
    Provide them as a JSON list with keys: question, options, answer.
    Example:
    [
      {"question": "What is structured data?", 
       "options": ["Images", "Tables with rows/columns", "Videos", "Audio"], 
       "answer": "Tables with rows/columns"}
    ]
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-turbo")  # faster variant
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        return questions
    except Exception:
        return fallback_questions  # fallback to static questions immediately

# -------------------------------
# Auto-refresh every 1 sec
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# Host Screen
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code below to join:")

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"Or click [here]({GAME_URL}) to join as Player.")

    state = load_state()
    if "scores" not in state:
        state["scores"] = []

    st.write(f"Players joined: {len(state['scores'])}")

    if not state["game_started"]:
        if st.button("Start Game"):
            state["questions"] = get_ai_questions()  # use all generated/fallback questions
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started!")

    if st.button("Restart Game"):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False}
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    # Show leaderboard or progress
    state = load_state()
    if state["game_started"]:
        if state["game_over"]:
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
# Player Screen
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
    if not state.get("scores"):
        state["scores"] = []

    # Register player if not already
    name = st.session_state.player_name
    if not any(p["name"] == name for p in state["scores"]):
        state["scores"].append({"name": name, "score": 0})
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
        key=f"q{q_index}",
        index=0
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        state = load_state()
        correct = st.session_state.selected_answer == q["answer"]
        for s in state["scores"]:
            if s["name"] == name:
                if correct:
                    s["score"] += POINTS_PER_QUESTION
        save_state(state)

    # Show feedback immediately
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    # Move to next question after timer ends
    if elapsed >= QUESTION_TIME:
        state = load_state()
        if q_index < len(state["questions"]) - 1:
            state["current_question"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        # Reset session for next question
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
