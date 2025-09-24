import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai

# -------------------------------
# Config
# -------------------------------
STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"  # Update to your deployed URL
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Gemini Setup
# -------------------------------
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")  # Replace with your API key
MODEL_NAME = "gemini-1.5-turbo"

# -------------------------------
# Fallback Questions (15 total)
# -------------------------------
FALLBACK_QUESTIONS = [
    {"question": "What does the standard deviation measure?",
     "options": ["The central value of data", "The spread of data around the mean", "The most common value", "The difference between max and min"],
     "answer": "The spread of data around the mean"},
    {"question": "Which company built AlphaGo, the AI agent that beat a Go world champion?",
     "options": ["OpenAI", "DeepMind", "IBM", "Microsoft"],
     "answer": "DeepMind"},
    {"question": "Which measure of central tendency is most affected by extreme values?",
     "options": ["Mean", "Median", "Mode", "Range"],
     "answer": "Mean"},
    {"question": "Which of these best describes 'data literacy'?",
     "options": ["Ability to read and work with data", "Ability to code", "Ability to memorize statistics", "Ability to create charts only"],
     "answer": "Ability to read and work with data"},
    {"question": "What is a 'multi-agent system'?",
     "options": ["AI working in isolation", "Multiple AI agents interacting", "Humans and AI working together", "One AI agent with multiple tasks"],
     "answer": "Multiple AI agents interacting"},
    {"question": "Which famous AI agent defeated Garry Kasparov in chess?",
     "options": ["AlphaGo", "Siri", "Deep Blue", "Watson"],
     "answer": "Deep Blue"},
    {"question": "What is the primary purpose of data visualization?",
     "options": ["To make data look pretty", "To identify patterns and insights", "To store data", "To clean data"],
     "answer": "To identify patterns and insights"},
    {"question": "Which AI agent famously won Jeopardy! against human champions?",
     "options": ["Siri", "Watson", "Alexa", "BERT"],
     "answer": "Watson"},
    {"question": "Which of these is an example of a reactive AI agent?",
     "options": ["Chess AI", "Personal Assistant", "Self-driving car", "Spam filter"],
     "answer": "Spam filter"},
    {"question": "What does a histogram show?",
     "options": ["Trends over time", "Distribution of data", "Relationship between variables", "Averages only"],
     "answer": "Distribution of data"},
    {"question": "If the mean = median = mode in a dataset, what is its distribution?",
     "options": ["Skewed left", "Skewed right", "Normal distribution", "Uniform distribution"],
     "answer": "Normal distribution"},
    {"question": "What is the 'environment' in AI agents?",
     "options": ["The physical world only", "The context in which an agent operates", "The internet", "The dataset only"],
     "answer": "The context in which an agent operates"},
    {"question": "Which type of chart is best for showing parts of a whole?",
     "options": ["Bar chart", "Pie chart", "Histogram", "Scatter plot"],
     "answer": "Pie chart"},
    {"question": "What is an AI agent?",
     "options": ["A piece of software that perceives and acts in an environment", "A robot only", "Any computer program", "A human working with AI"],
     "answer": "A piece of software that perceives and acts in an environment"},
    {"question": "What does a pie chart represent best?",
     "options": ["Parts of a whole", "Trends over time", "Correlation between variables", "Frequency distribution"],
     "answer": "Parts of a whole"},
]

# -------------------------------
# State Management
# -------------------------------
def init_state():
    if not os.path.exists(STATE_FILE):
        state = {
            "game_started": False,
            "current_question": 0,
            "scores": [],
            "game_over": False,
            "players": {},
            "questions": []
        }
        save_state(state)
    else:
        # Ensure all keys exist
        state = load_state()
        if "players" not in state:
            state["players"] = {}
        if "questions" not in state:
            state["questions"] = []
        save_state(state)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Question Generator
# -------------------------------
def get_ai_questions():
    prompt = """
    Create 15 multiple-choice quiz questions about Data Literacy and AI Agents.
    Provide them as a JSON list with keys: question, options, answer.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        return questions
    except Exception:
        return FALLBACK_QUESTIONS

# -------------------------------
# Auto-refresh every 1 sec
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")
init_state()
state = load_state()

# Pre-generate AI questions at app start if empty
if not state["questions"]:
    state["questions"] = get_ai_questions()
    save_state(state)

# -------------------------------
# Mode Selection
# -------------------------------
params = st.query_params
role = params.get("role", ["Host"])[0]
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"], index=0 if role.lower() == "host" else 1)

# -------------------------------
# Host Screen
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code or click the link below to join:")

    # QR code
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.markdown(f"[👉 Click here to join as Player]({GAME_URL})")

    state = load_state()
    st.write(f"Players joined: {len(state['players'])}")

    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started!")

    if st.button("🔄 Restart Game"):
        state = {"game_started": False, "current_question": 0,
                 "scores": [], "game_over": False, "players": {}, "questions": state["questions"]}
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    if state["game_started"]:
        if state["game_over"]:
            st.success("🎉 Game Over! Final Leaderboard:")
            if state["scores"]:
                df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            st.write(f"Game in progress... Question {state['current_question'] + 1}/{len(state['questions'])}")
            if state["scores"]:
                df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False).head(3)
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

    # Register player
    if st.session_state.player_name not in state["players"]:
        state["players"][st.session_state.player_name] = 0
        save_state(state)

    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    if state["game_over"]:
        st.success("🎉 Game Over! Thank you for playing.")
        if state["scores"]:
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # Question session state
    if "start_time" not in st.session_state or st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    questions = state["questions"]
    q_index = state["current_question"]
    q = questions[q_index]

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"q{q_index}"
    )
    st.write(f"⏳ Time left: {remaining} sec")

    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]
        found = False
        for s in state["scores"]:
            if s["name"] == st.session_state.player_name:
                if correct:
                    s["score"] += POINTS_PER_QUESTION
                found = True
        if not found:
            state["scores"].append({
                "name": st.session_state.player_name,
                "score": POINTS_PER_QUESTION if correct else 0
            })
        save_state(state)

    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    # Move to next question after timer ends
    if elapsed >= QUESTION_TIME:
        state = load_state()
        if state["current_question"] < len(questions) - 1:
            state["current_question"] += 1
        else:
            state["game_over"] = True
        save_state(state)
    
        # Reset session variables for next question
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
