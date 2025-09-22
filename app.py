# app.py
import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO

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
# Leaderboard
# -------------------------------
if 'scores' not in st.session_state:
    st.session_state.scores = []

# -------------------------------
# QR Code for game access
# -------------------------------
st.title("AI-Powered Quiz Game 🎮")

# Generate QR code
qr = qrcode.QRCode(version=1, box_size=8, border=2)
game_url = "http://localhost:8501"  # Change if deploying
qr.add_data(game_url)
qr.make(fit=True)
img = qr.make_image(fill='black', back_color='white')
buf = BytesIO()
img.save(buf)
st.image(buf, width=200)
st.write("Scan the QR code to join the game!")

# -------------------------------
# Player enters name
# -------------------------------
player_name = st.text_input("Enter your first name:")

if player_name:
    st.session_state.current_player = player_name
    st.write(f"Welcome, **{player_name}**! Let's start the quiz.")
    
    # Shuffle questions
    shuffled_questions = random.sample(questions, len(questions))
    score = 0
    
    for i, q in enumerate(shuffled_questions):
        st.write(f"**Question {i+1}: {q['question']}**")
        options = q['options']
        random.shuffle(options)
        
        # Timer
        time_placeholder = st.empty()
        for t in range(20, 0, -1):
            time_placeholder.text(f"Time left: {t} sec")
            time.sleep(1)
        time_placeholder.empty()
        
        # Display options
        answer = st.radio("Choose your answer:", options, key=i)
        
        # Check answer
        if st.button("Submit", key=f"btn{i}"):
            if answer == q['answer']:
                st.success("Correct! ✅")
                score += 1
            else:
                st.error(f"Incorrect ❌. Correct answer: {q['answer']}")
            st.markdown("---")
            time.sleep(1)
    
    # Store score
    st.session_state.scores.append({"name": player_name, "score": score})
    
    # Show leaderboard
    st.subheader("🏆 Leaderboard - Top 3")
    df = pd.DataFrame(st.session_state.scores).sort_values(by='score', ascending=False).head(3)
    st.table(df)