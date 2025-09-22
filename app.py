import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Constants
# -------------------------------
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"
POINTS_PER_QUESTION = 5
TOTAL_POINTS = 5 * POINTS_PER_QUESTION  # 5 questions
QUESTION_TIME = 15  # seconds for each question
FEEDBACK_TIME = 3   # seconds to show feedback

# -------------------------------
# Generate QR code
# -------------------------------
qr = qrcode.QRCode(version=1, box_size=8, border=2)
qr.add_data(GAME_URL)
qr.make(fit=True)
img = qr.make_image(fill='black', back_color='white')
buf = BytesIO()
img.save(buf)
st.image(buf, width=200)
st.write("Scan the QR code to join the game!")

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
# Session state initialization
# -------------------------------
if 'player_name' not in st.session_state:
    st.session_state.player_name = ''
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0
if 'shuffled_questions' not in st.session_state:
    st.session_state.shuffled_questions = random.sample(questions, len(questions))
if 'selected_answer' not in st.session_state:
    st.session_state.selected_answer = None
if 'question_start' not in st.session_state:
    st.session_state.question_start = time.time()
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'feedback_time' not in st.session_state:
    st.session_state.feedback_time = 0
if 'scores' not in st.session_state:
    st.session_state.scores = []

# -------------------------------
# Auto-refresh every second for live timer
# -------------------------------
st_autorefresh(interval=1000, key="timer_refresh")

# -------------------------------
# Game UI
# -------------------------------
st.title("AI-Powered Quiz Game 🎮")

# Enter player name
if not st.session_state.player_name:
    st.session_state.player_name = st.text_input("Enter your first name:")

if st.session_state.player_name:
    st.write(f"Welcome, **{st.session_state.player_name}**! Let's start the quiz.")

    # Check if questions remain
    if st.session_state.q_index < len(st.session_state.shuffled_questions):
        q = st.session_state.shuffled_questions[st.session_state.q_index]
        st.write(f"**Question {st.session_state.q_index + 1}: {q['question']}**")

        # Show options if not showing feedback
        if not st.session_state.answered:
            st.session_state.selected_answer = st.radio("Choose your answer:", q['options'], index=0)

        # Timer
        elapsed = int(time.time() - st.session_state.question_start)
        remaining = max(0, QUESTION_TIME - elapsed)
        if not st.session_state.answered:
            st.write(f"Time left: {remaining} sec")

        # Auto-submit if timer ends
        if remaining == 0 and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.feedback_time = time.time()

        # Submit button
        if st.button("Submit") and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.feedback_time = time.time()

        # Show feedback for FEEDBACK_TIME seconds
        if st.session_state.answered:
            if st.session_state.selected_answer == q['answer']:
                st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
                # Award points only once
                if st.session_state.feedback_time == time.time():  
                    st.session_state.score += POINTS_PER_QUESTION
            else:
                st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

            # After feedback time, move to next question
            if time.time() - st.session_state.feedback_time >= FEEDBACK_TIME:
                st.session_state.q_index += 1
                st.session_state.question_start = time.time()
                st.session_state.selected_answer = None
                st.session_state.answered = False
                st.session_state.feedback_time = 0

    else:
        # Quiz finished
        st.subheader(f"🎉 Quiz Finished! Your score: {st.session_state.score}/{TOTAL_POINTS}")

        # Save/update player score
        found = False
        for rec in st.session_state.scores:
            if rec['name'] == st.session_state.player_name:
                rec['score'] = st.session_state.score
                found = True
                break
        if not found:
            st.session_state.scores.append({"name": st.session_state.player_name, "score": st.session_state.score})

        # Leaderboard - top 3
        st.subheader("🏆 Leaderboard - Top 3")
        df = pd.DataFrame(st.session_state.scores).sort_values(by='score', ascending=False).head(3)
        st.table(df)
