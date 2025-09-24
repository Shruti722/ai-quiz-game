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
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")  # Replace with your API key if desired
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
# Robust state helpers
# -------------------------------
def save_state(state):
    """Atomically write JSON to avoid partial/corrupt files."""
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)

def load_state():
    """
    Load state, recover from invalid/corrupt file by resetting to safe defaults,
    and ensure all expected keys exist.
    """
    defaults = {
        "game_started": False,
        "current_question": 0,
        "scores": [],
        "game_over": False,
        "players": {},
        "questions": FALLBACK_QUESTIONS.copy(),
        "host_question_start": time.time()
    }

    if not os.path.exists(STATE_FILE):
        save_state(defaults)
        return defaults.copy()

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Recover by resetting
        save_state(defaults)
        return defaults.copy()

    # Ensure keys
    for k, v in defaults.items():
        if k not in state or state[k] is None:
            state[k] = v if k != "questions" else FALLBACK_QUESTIONS.copy()

    # Defensive: if questions empty, fill fallback
    if not isinstance(state.get("questions"), list) or len(state["questions"]) == 0:
        state["questions"] = FALLBACK_QUESTIONS.copy()

    # Defensive: current_question bounds
    if not isinstance(state.get("current_question"), int):
        state["current_question"] = 0
    if state["current_question"] < 0:
        state["current_question"] = 0
    if state["current_question"] >= len(state["questions"]):
        # mark game over when index is out of range
        state["game_over"] = True

    # Save if we changed anything important
    save_state(state)
    return state

def init_state():
    s = load_state()
    save_state(s)

# Optional: AI question generation (unused unless you call)
def get_ai_questions():
    prompt = """
    Create 15 multiple-choice quiz questions about Data Literacy and AI Agents.
    Provide them as a JSON list with keys: question, options, answer.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        if isinstance(questions, list) and len(questions) >= 1:
            return questions
    except Exception:
        pass
    return FALLBACK_QUESTIONS.copy()

# -------------------------------
# Auto-refresh (keeps UI in sync)
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

    # load the latest state
    state = load_state()
    st.write(f"Players joined: {len(state.get('players', {}))}")

    # allow host to generate AI questions (optional)
    if not state.get("questions"):
        if st.button("Generate questions with Gemini"):
            qs = get_ai_questions()
            state = load_state()
            state["questions"] = qs
            save_state(state)
            st.success("Generated questions.")

    if not state.get("game_started"):
        if st.button("🚀 Start Game"):
            # reload and set start
            state = load_state()
            if not state.get("questions"):
                state["questions"] = FALLBACK_QUESTIONS.copy()
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            state["host_question_start"] = time.time()
            save_state(state)
            st.success("Game started!")

    if st.button("🔄 Restart Game"):
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

    # advance question if time elapsed (host only)
    state = load_state()
    if state.get("game_started") and not state.get("game_over"):
        elapsed = int(time.time() - state.get("host_question_start", time.time()))
        if elapsed >= QUESTION_TIME:
            if state["current_question"] < len(state["questions"]) - 1:
                state["current_question"] += 1
                state["host_question_start"] = time.time()
            else:
                # end game cleanly (do NOT flip game_started to False)
                state["game_over"] = True
            save_state(state)

    state = load_state()
    if state.get("game_started") and not state.get("game_over"):
        st.write(f"Game in progress... Question {state['current_question']+1}/{len(state['questions'])}")
        if state.get("scores"):
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False).head(5)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Leaderboard - Top 5")
            st.table(df[["Rank","name","score"]])

    if state.get("game_over"):
        st.success("🎉 Game Over! Final Leaderboard:")
        if state.get("scores"):
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.table(df[["Rank","name","score"]])

# -------------------------------
# PLAYER
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    # get player's name (persisted per browser session)
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")
        # wait for user to enter name
        st.stop()

    player = st.session_state.player_name
    st.write(f"Welcome, **{player}**!")

    # register player safely (load fresh, update, save)
    state = load_state()
    if player not in state.get("players", {}):
        state = load_state()  # reload before mutating
        if player not in state.get("players", {}):
            state["players"][player] = 0
            save_state(state)
            state = load_state()

    # show final leaderboard first if game_over
    state = load_state()
    if state.get("game_over"):
        st.success("🎉 Game Over! Final Leaderboard:")
        if state.get("scores"):
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank","name","score"]])
        st.stop()

    # if game not started yet -> waiting
    if not state.get("game_started"):
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    # defensive: ensure questions exist
    if not state.get("questions"):
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)

    # if current_question out of bounds -> end game
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

    # reset per-session answered state on question change
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

    # safe read of current question
    q_index = state["current_question"]
    questions = state["questions"]
    if q_index < 0 or q_index >= len(questions):
        # If out of bounds, mark game_over and show leaderboard
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

    # show question + timer
    st.markdown(f"**Question {q_index+1}: {q.get('question', '---')}**")
    remaining = max(0, QUESTION_TIME - int(time.time() - state.get("host_question_start", time.time())))
    st.write(f"⏳ Time left for this question: {remaining} sec")

    # radio options
    options = q.get("options", [])
    st.session_state.selected_answer = st.radio("Choose your answer:", options, key=f"q{q_index}")

    # Submit -> update scoreboard on a fresh read/write so we do not clobber host fields
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q.get("answer")

        # load fresh state, update scores list only, preserve everything else
        s2 = load_state()
        if "scores" not in s2 or not isinstance(s2["scores"], list):
            s2["scores"] = []

        # update existing entry or append
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
        # reload state for UI consistency
        state = load_state()

    # show feedback only after submit
    if st.session_state.answered:
        if st.session_state.selected_answer == q.get("answer"):
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q.get('answer', 'Unknown')}")

    # show live top-5 leaderboard while playing
    if state.get("scores"):
        df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False).head(5)
        df.insert(0, "Rank", range(1, len(df)+1))
        st.subheader("🏆 Current Leaderboard - Top 5")
        st.table(df[["Rank","name","score"]])
