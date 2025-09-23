# app.py
import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO

# -------------------------------
# Config
# -------------------------------
QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# -------------------------------
# Question bank
# -------------------------------
questions = [
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
# Streamlit Cloud URL
# -------------------------------
game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=player"

# -------------------------------
# Role detection
# -------------------------------
query_params = st.query_params
role = query_params.get("role", ["host"])[0]  # default = host

# -------------------------------
# Initialize session state safely
# -------------------------------
if "game_started" not in st.session_state:
    st.session_state.game_started = False

if role == "player":
    for key in [
        "player_name", "score", "q_index", "shuffled_questions",
        "answered", "start_time", "feedback_time", "selected_answer",
        "scores"
    ]:
        if key not in st.session_state:
            if key == "shuffled_questions":
                st.session_state[key] = random.sample(questions, len(questions))
            elif key in ["score", "q_index"]:
                st.session_state[key] = 0
            else:
                st.session_state[key] = None

# -------------------------------
# Host Screen
# -------------------------------
if role == "host":
    st.title("🎮 AI-Powered Quiz Game - Host Screen")

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(game_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write(f"📱 Ask players to scan this QR code to join or share this link: {game_url}")

    if st.button("Start Game"):
        st.session_state.game_started = True
        st.success("✅ Game started! Players should now see questions.")

# -------------------------------
# Player Screen
# -------------------------------
elif role == "player":
    st.title("🎮 AI-Powered Quiz Game")

    # Player enters name
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")
    else:
        st.write(f"Welcome, **{st.session_state.player_name}**! Let's start the quiz.")

    # Check if host started
    if not st.session_state.game_started:
        st.info("⏳ Waiting for host to start the game...")
    else:
        # Quiz questions
        if st.session_state.q_index < len(st.session_state.shuffled_questions):
            q = st.session_state.shuffled_questions[st.session_state.q_index]

            # Initialize timer
            if st.session_state.start_time is None:
                st.session_state.start_time = time.time()

            elapsed = int(time.time() - st.session_state.start_time)
            remaining = max(0, QUESTION_TIME - elapsed)

            st.write(f"**Question {st.session_state.q_index + 1}: {q['question']}**")
            st.session_state.selected_answer = st.radio(
                "Choose your answer:", q["options"], key=f"q{st.session_state.q_index}"
            )

            st.write(f"⏳ Time left: {remaining} sec")

            # Submit answer automatically if time is up
            if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
                st.session_state.answered = True
                st.session_state.feedback_time = time.time()
                if st.session_state.selected_answer == q["answer"]:
                    st.session_state.score += POINTS_PER_QUESTION

            # Show feedback
            if st.session_state.answered:
                if st.session_state.selected_answer == q["answer"]:
                    st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
                else:
                    st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

                elapsed_feedback = time.time() - st.session_state.feedback_time
                if elapsed_feedback > FEEDBACK_TIME:
                    st.session_state.q_index += 1
                    st.session_state.start_time = None
                    st.session_state.answered = False
                    st.session_state.selected_answer = None
                    st.experimental_rerun()
                else:
                    st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
                    time.sleep(1)
                    st.experimental_rerun()

        else:
            # Quiz finished
            total_points = len(st.session_state.shuffled_questions) * POINTS_PER_QUESTION
            st.subheader(f"🎉 Quiz Finished! Your score: {st.session_state.score}/{total_points}")

            if not any(s["name"] == st.session_state.player_name for s in st.session_state.scores):
                st.session_state.scores.append({"name": st.session_state.player_name, "score": st.session_state.score})

            st.subheader("🏆 Leaderboard - Top 3")
            df = pd.DataFrame(st.session_state.scores).sort_values(by="score", ascending=False).head(3)
            st.table(df)
