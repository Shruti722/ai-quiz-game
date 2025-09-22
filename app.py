import streamlit as st
import random
import pandas as pd
import time

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
# Session state setup
# -------------------------------
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

# -------------------------------
# Game UI
# -------------------------------
st.title("AI-Powered Quiz Game 🎮")

# Enter player name
if not st.session_state.player_name:
    st.session_state.player_name = st.text_input("Enter your first name:")

if st.session_state.player_name:
    st.write(f"Welcome, **{st.session_state.player_name}**! Let's start the quiz.")

    # Show current question
    if st.session_state.q_index < len(st.session_state.shuffled_questions):
        q = st.session_state.shuffled_questions[st.session_state.q_index]
        st.write(f"**Question {st.session_state.q_index + 1}: {q['question']}**")
        
        # Display options
        answer = st.radio("Choose your answer:", q['options'], key=st.session_state.q_index)
        
        # Timer placeholder
        timer_placeholder = st.empty()
        
        if not st.session_state.answer_selected:
            for t in range(15, 0, -1):
                timer_placeholder.text(f"Time left: {t} sec")
                time.sleep(1)
                st.experimental_rerun()  # rerun to update the timer
            st.session_state.answer_selected = True
        
        # Check answer and move to next question
        if st.session_state.answer_selected:
            if answer == q['answer']:
                st.success("Correct! ✅")
                st.session_state.score += 1
            else:
                st.error(f"Incorrect ❌. Correct answer: {q['answer']}")
            st.session_state.q_index += 1
            st.session_state.answer_selected = False
            st.experimental_rerun()
            
    else:
        st.subheader(f"Quiz Finished! Your score: {st.session_state.score}/{len(questions)}")
        # Store score in leaderboard
        st.session_state.scores.append({"name": st.session_state.player_name, "score": st.session_state.score})
        st.subheader("🏆 Leaderboard - Top 3")
        df = pd.DataFrame(st.session_state.scores).sort_values(by='score', ascending=False).head(3)
        st.table(df)
