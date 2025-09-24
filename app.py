import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
import google.generativeai as genai

# -------------------------------
# CONFIGURE GEMINI API
# -------------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # set your API key in env variable

STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"

QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Initialize state.json if not exists
# -------------------------------
if not os.path.exists(STATE_FILE):
    state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "questions": []}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Load & Save state
# -------------------------------
def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# Generate questions via Gemini
# -------------------------------
def generate_questions(n=5):
    prompt = f"""
    Generate {n} multiple-choice questions about data literacy and AI agents.
    Each question must have exactly 4 options and indicate the correct answer.
    Return only valid JSON in the following format:
    [
      {{
        "question": "...",
        "options": ["...", "...", "...", "..."],
        "answer": "..."
      }},
      ...
    ]
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    try:
        questions = json.loads(response.text)
    except Exception:
        st.error("⚠️ Failed to parse Gemini response. Check output format.")
        questions = []
    return questions

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# HOST SCREEN
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code below to join:")

    # QR code
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)

    state = load_state()
    st.write(f"Players joined: {len(state['scores'])}")

    # Start Game
    if not state["game_started"]:
        if st.button("Start Game"):
            questions = generate_questions()
            if not questions:
                st.error("❌ No questions generated. Try again.")
            else:
                state["questions"] = questions
                state["game_started"] = True
                state["current_question"] = 0
                state["game_over"] = False
                save_state(state)
                st.success("✅ Game started with AI-generated questions!")

    # Restart Game
    if st.button("Restart Game"):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "questions": []}
        save_state(state)
        st.success("🔄 Game has been reset! Players can rejoin.")

    # Game in progress / leaderboard
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

            # Timer
            if "host_start_time" not in st.session_state:
                st.session_state.host_start_time = time.time()
            elapsed = int(time.time() - st.session_state.host_start_time)
            remaining = max(0, QUESTION_TIME - elapsed)
            st.write(f"⏳ Time left for this question: {remaining} sec")

            # Advance question automatically when timer ends
            if elapsed >= QUESTION_TIME:
                if state["current_question"] < len(state["questions"]) - 1:
                    state["current_question"] += 1
                    st.session_state.host_start_time = time.time()
                else:
                    state["game_over"] = True
                save_state(state)

            # Show top 3 leaderboard
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

    # Load state
    state = load_state()
    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    # Initialize session state
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Game Over Check
    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state['scores']:
            df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # Current Question
    q_index = state["current_question"]
    questions = state["questions"]
    if q_index >= len(questions):
        st.stop()

    q = questions[q_index]

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"q{q_index}"
    )

    # Submit Answer
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]

        # Update score
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

    # Feedback
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")
