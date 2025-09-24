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
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player"
QUESTION_TIME = 20
POINTS_PER_QUESTION = 5

# -------------------------------
# Gemini Setup (optional)
# -------------------------------
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")  # Replace with your API key
MODEL_NAME = "gemini-1.5-turbo"

# -------------------------------
# Fallback Questions
# -------------------------------
FALLBACK_QUESTIONS = [
    {"question": "What does the standard deviation measure?", "options": ["The central value of data","The spread of data around the mean","The most common value","The difference between max and min"], "answer": "The spread of data around the mean"},
    {"question": "Which company built AlphaGo, the AI agent that beat a Go world champion?", "options": ["OpenAI","DeepMind","IBM","Microsoft"], "answer": "DeepMind"},
    {"question": "Which measure of central tendency is most affected by extreme values?", "options": ["Mean","Median","Mode","Range"], "answer": "Mean"},
    {"question": "Which of these best describes 'data literacy'?", "options": ["Ability to read and work with data","Ability to code","Ability to memorize statistics","Ability to create charts only"], "answer": "Ability to read and work with data"},
    {"question": "What is a 'multi-agent system'?", "options": ["AI working in isolation","Multiple AI agents interacting","Humans and AI working together","One AI agent with multiple tasks"], "answer": "Multiple AI agents interacting"},
    {"question": "Which famous AI agent defeated Garry Kasparov in chess?", "options": ["AlphaGo","Siri","Deep Blue","Watson"], "answer": "Deep Blue"},
    {"question": "What is the primary purpose of data visualization?", "options": ["To make data look pretty","To identify patterns and insights","To store data","To clean data"], "answer": "To identify patterns and insights"},
    {"question": "Which AI agent famously won Jeopardy! against human champions?", "options": ["Siri","Watson","Alexa","BERT"], "answer": "Watson"},
    {"question": "Which of these is an example of a reactive AI agent?", "options": ["Chess AI","Personal Assistant","Self-driving car","Spam filter"], "answer": "Spam filter"},
    {"question": "What does a histogram show?", "options": ["Trends over time","Distribution of data","Relationship between variables","Averages only"], "answer": "Distribution of data"},
    {"question": "If the mean = median = mode in a dataset, what is its distribution?", "options": ["Skewed left","Skewed right","Normal distribution","Uniform distribution"], "answer": "Normal distribution"},
    {"question": "What is the 'environment' in AI agents?", "options": ["The physical world only","The context in which an agent operates","The internet","The dataset only"], "answer": "The context in which an agent operates"},
    {"question": "Which type of chart is best for showing parts of a whole?", "options": ["Bar chart","Pie chart","Histogram","Scatter plot"], "answer": "Pie chart"},
    {"question": "What is an AI agent?", "options": ["A piece of software that perceives and acts in an environment","A robot only","Any computer program","A human working with AI"], "answer": "A piece of software that perceives and acts in an environment"},
    {"question": "What does a pie chart represent best?", "options": ["Parts of a whole","Trends over time","Correlation between variables","Frequency distribution"], "answer": "Parts of a whole"}
]

# -------------------------------
# State management (robust)
# -------------------------------
def save_state(state):
    """
    Write to a temp file then atomically replace the state file to avoid partial/corrupt JSON.
    """
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    # atomic replace
    os.replace(tmp, STATE_FILE)

def load_state():
    """
    Load state, recover from invalid/corrupt file by resetting.
    Ensure all expected keys exist.
    """
    defaults = {
        "game_started": False,
        "current_question": 0,
        "scores": [],
        "game_over": False,
        "players": {},
        "questions": [],
        "host_question_start": time.time()
    }

    if not os.path.exists(STATE_FILE):
        # initialize fresh
        state = defaults.copy()
        # populate fallback questions by default
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)
        return state

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # corrupted file -> reset
        state = defaults.copy()
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)
        return state

    # ensure keys exist
    for k, v in defaults.items():
        if k not in state:
            state[k] = v

    # if questions missing or empty, fill fallback
    if not state.get("questions"):
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)

    # defensive: ensure current_question is within valid range
    if not isinstance(state.get("current_question", 0), int):
        state["current_question"] = 0
    if state["current_question"] < 0:
        state["current_question"] = 0
    if state["current_question"] >= len(state["questions"]):
        # mark game over (finished) to prevent IndexError and show final leaderboard
        state["game_over"] = True
        save_state(state)

    return state

def init_state():
    s = load_state()
    save_state(s)

# -------------------------------
# Question generation (optional)
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
        # minimal validation
        if isinstance(questions, list) and len(questions) >= 1:
            return questions
    except Exception:
        pass
    return FALLBACK_QUESTIONS.copy()

# -------------------------------
# Auto-refresh so pages update
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")
init_state()

# -------------------------------
# Mode selection
# -------------------------------
params = st.query_params
role = params.get("role", ["Host"])[0]
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"], index=0 if role.lower() == "host" else 1)

# -------------------------------
# HOST
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code or click the link below to join:")

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.markdown(f"[👉 Click here to join as Player]({GAME_URL})")

    # always reload current state at the top of host block
    state = load_state()
    st.write(f"Players joined: {len(state['players'])}")

    # generate questions if none exist (host action)
    if not state.get("questions"):
        state["questions"] = get_ai_questions()
        save_state(state)

    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            # reload before mutating to take latest
            state = load_state()
            if not state.get("questions"):
                state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            state["host_question_start"] = time.time()
            save_state(state)
            st.success("Game started!")

    if st.button("🔄 Restart Game"):
        # reload then reset but keep existing questions if present
        state = load_state()
        state = {
            "game_started": False,
            "current_question": 0,
            "scores": [],
            "game_over": False,
            "players": {},
            "questions": state.get("questions", FALLBACK_QUESTIONS.copy()),
            "host_question_start": time.time()
        }
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    # Advance questions when appropriate
    state = load_state()  # reload latest
    if state["game_started"] and not state["game_over"]:
        elapsed = int(time.time() - state.get("host_question_start", time.time()))
        if elapsed >= QUESTION_TIME:
            # advance safely
            if state["current_question"] < len(state["questions"]) - 1:
                state["current_question"] += 1
                state["host_question_start"] = time.time()
            else:
                state["game_over"] = True
            save_state(state)

        st.write(f"Game in progress... Question {state['current_question']+1}/{len(state['questions'])}")
        if state["scores"]:
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False).head(5)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Leaderboard - Top 5")
            st.table(df[["Rank","name","score"]])

    if state.get("game_over"):
        st.success("🎉 Game Over! Final Leaderboard:")
        if state["scores"]:
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.table(df[["Rank","name","score"]])

# -------------------------------
# PLAYER
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    # --- get player name (persisted per-session) ---
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")
        st.stop()
    player = st.session_state.player_name
    st.write(f"Welcome, **{player}**!")

    # load latest state and register player safely
    state = load_state()
    if player not in state["players"]:
        # reload before modifying to reduce race windows
        state = load_state()
        if player not in state["players"]:
            state["players"][player] = 0
            save_state(state)
            # reload after save so we operate on fresh state
            state = load_state()

    # Immediately reflect game_over (highest priority)
    if state.get("game_over"):
        st.success("🎉 Game Over! Final Leaderboard:")
        if state.get("scores"):
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank","name","score"]])
        st.stop()

    # If host hasn't started the game yet
    if not state.get("game_started"):
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    # ensure questions exist; defensive
    if not state.get("questions"):
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)

    # ensure current_question is valid; if not, mark game_over and show leaderboard
    if state["current_question"] >= len(state["questions"]):
        state["game_over"] = True
        save_state(state)
        st.success("🎉 Game Over! Final Leaderboard:")
        if state.get("scores"):
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank","name","score"]])
        st.stop()

    # Reset per-session answered state on question change
    if "last_question_index" not in st.session_state:
        st.session_state.last_question_index = state["current_question"]
    if st.session_state.last_question_index != state["current_question"]:
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.last_question_index = state["current_question"]

    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Safe access to the current question
    q_index = state["current_question"]
    questions = state["questions"]
    # double-check bounds
    if q_index < 0 or q_index >= len(questions):
        # out of bounds -> end game
        state["game_over"] = True
        save_state(state)
        st.success("🎉 Game Over! Final Leaderboard:")
        if state.get("scores"):
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank","name","score"]])
        st.stop()

    q = questions[q_index]

    # Display question and timer (synced to host)
    st.markdown(f"**Question {q_index+1}: {q.get('question', '---')}**")
    remaining = max(0, QUESTION_TIME - int(time.time() - state.get("host_question_start", time.time())))
    st.write(f"⏳ Time left for this question: {remaining} sec")

    # Options (radio)
    st.session_state.selected_answer = st.radio("Choose your answer:", q.get("options", []), key=f"q{q_index}")

    # Submit: update score on a freshly loaded state to avoid clobbering
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q.get("answer")

        # Reload state, update player score inside this fresh state, then save
        s2 = load_state()
        # ensure s2 has a scores list
        if "scores" not in s2 or not isinstance(s2["scores"], list):
            s2["scores"] = []

        found = False
        for entry in s2["scores"]:
            if entry.get("name") == player:
                if correct:
                    entry["score"] = entry.get("score", 0) + POINTS_PER_QUESTION
                found = True
                break
        if not found:
            s2["scores"].append({"name": player, "score": POINTS_PER_QUESTION if correct else 0})

        save_state(s2)
        # reload state to reflect saved data for this session's logic
        state = load_state()

    # Show result only after Submit
    if st.session_state.answered:
        if st.session_state.selected_answer == q.get("answer"):
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q.get('answer', 'Unknown')}")

    # Optionally show a small leaderboard during play
    if state.get("scores"):
        df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False).head(5)
        df.insert(0, "Rank", range(1, len(df)+1))
        st.subheader("🏆 Current Leaderboard - Top 5")
        st.table(df[["Rank","name","score"]])
