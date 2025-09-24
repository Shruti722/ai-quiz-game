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
# State management
# -------------------------------
def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)

def load_state():
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
        state = defaults.copy()
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)
        return state
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except Exception:
        state = defaults.copy()
        state["questions"] = FALLBACK_QUESTIONS.copy()
        save_state(state)
        return state
    for k, v in defaults.items():
        if k not in state:
            state[k] = v
    if not state.get("questions"):
        state["questions"] = FALLBACK_QUESTIONS.copy()
    if state["current_question"] >= len(state["questions"]):
        state["game_over"] = True
    save_state(state)
    return state

def init_state():
    s = load_state()
    save_state(s)

# -------------------------------
# AI-generated questions (optional)
# -------------------------------
def get_ai_questions():
    prompt = """Create 15 multiple-choice quiz questions about Data Literacy and AI Agents. Provide them as a JSON list with keys: question, options, answer."""
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
# Auto-refresh
# -------------------------------
st_autorefresh(interval=1500, limit=None, key="quiz_autorefresh")
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

    state = load_state()

    # Only count players who have a valid name
    real_players = [name for name in state["players"] if name.strip() != ""]
    st.write(f"Players joined: {len(real_players)}")

    if not state["questions"]:
        state["questions"] = get_ai_questions()
        save_state(state)

# -------------------------------
# PLAYER
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")
        if not st.session_state.player_name:
            st.stop()
    player = st.session_state.player_name
    st.write(f"Welcome, **{player}**!")

    state = load_state()
    if player not in state["players"]:
        state["players"][player] = 0
        save_state(state)
        state = load_state()

    # --- Show final leaderboard if game ended ---
    if state["game_over"]:
        st.success("🎉 Game Over! Final Leaderboard:")
        if state["scores"]:
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank","name","score"]])
        st.stop()

    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    # --- Question handling ---
    q_index = state["current_question"]
    if q_index >= len(state["questions"]):
        state["game_over"] = True
        save_state(state)
        st.success("🎉 Game Over! Final Leaderboard:")
        if state["scores"]:
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.table(df[["Rank","name","score"]])
        st.stop()

    if "last_question_index" not in st.session_state:
        st.session_state.last_question_index = -1
    if st.session_state.last_question_index != q_index:
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.last_question_index = q_index

    q = state["questions"][q_index]
    st.markdown(f"**Question {q_index+1}: {q['question']}**")

    remaining = max(0, QUESTION_TIME - int(time.time() - state["host_question_start"]))
    st.write(f"⏳ Time left for this question: {remaining} sec")

    st.session_state.selected_answer = st.radio("Choose your answer:", q["options"], key=f"q{q_index}")

    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]
        try:
            s2 = load_state()
            found = False
            for entry in s2["scores"]:
                if entry["name"] == player:
                    if correct:
                        entry["score"] += POINTS_PER_QUESTION
                    found = True
            if not found:
                s2["scores"].append({"name": player, "score": POINTS_PER_QUESTION if correct else 0})
            save_state(s2)
        except Exception as e:
            st.error(f"Error saving score: {e}")

    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    if state["scores"]:
        df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False).head(5)
        df.insert(0, "Rank", range(1, len(df)+1))
        st.subheader("🏆 Current Leaderboard - Top 5")
        st.table(df[["Rank","name","score"]])
