import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO

# -------------------------------
# Streamlit Cloud URL
# -------------------------------
game_url = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=player"

# Generate QR code for players
qr = qrcode.QRCode(version=1, box_size=8, border=2)
qr.add_data(game_url)
qr.make(fit=True)
img = qr.make_image(fill='black', back_color='white')
buf = BytesIO()
img.save(buf)

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
# Role detection (host or player)
# -------------------------------
query_params = st.query_params
role = query_params.get("role", "host")  # default = host


# -------------------------------
# Host Screen
# -------------------------------
if role == "host":
    st.title("🎮 AI-Powered Quiz Game - Host Screen")

    st.image(buf, width=200)
    st.write("📱 Ask players to scan this QR code to join!")
    st.write(f"Or share this link: {game_url}")

    if st.button("Start Game"):
        st.session_state.game_started = True
        st.success("✅ Game started! Players should now see questions.")

# -------------------------------
# Player Screen
# -------------------------------
elif role == "player":
    st.title("🎮 AI-Powered Quiz Game")

    if 'player_name' not in st.session_state:
        st.session_state.player_name = ''
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'q_index' not in st.session_state:
        st.session_state.q_index = 0
    if 'shuffled_questions' not in st.session_state:
        st.session_state.shuffled_questions = random.sample(questions, len(questions))
    if 'answer_selected' not in st.session_state:
        st.session_state.answer_selected = False
    if 'scores' not in st.session_state:
        st.session_state.scores = []

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    if st.session_state.player_name:
        st.write(f"Welcome, **{st.session_state.player_name}**! Let's start the quiz.")

        if st.session_state.q_index < len(st.session_state.shuffled_questions):
            q = st.session_state.shuffled_questions[st.session_state.q_index]
            st.write(f"**Question {st.session_state.q_index + 1}: {q['question']}**")

            answer = st.radio("Choose your answer:", q['options'], key=st.session_state.q_index)
            
            if st.button("Submit Answer"):
                if answer == q['answer']:
                    st.success("Correct! ✅ (+5 points)")
                    st.session_state.score += 5
                else:
                    st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

                time.sleep(3)  # wait before next question
                st.session_state.q_index += 1
                st.experimental_rerun()
        else:
            st.subheader(f"🎉 Quiz Finished! Your score: {st.session_state.score}/{len(questions)*5}")
            st.session_state.scores.append({"name": st.session_state.player_name, "score": st.session_state.score})
            st.subheader("🏆 Leaderboard - Top 3")
            df = pd.DataFrame(st.session_state.scores).sort_values(by='score', ascending=False).head(3)
            st.table(df)
