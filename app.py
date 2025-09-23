import streamlit as st
import random
import pandas as pd
import time
import qrcode
from io import BytesIO
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Supabase credentials
# -------------------------------
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# Quiz config
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

QUESTION_TIME = 15
FEEDBACK_TIME = 3
POINTS_PER_QUESTION = 5

# Auto-refresh for timers
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App Mode
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# Host screen
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")

    # QR code
    GAME_URL = "YOUR_DEPLOYED_STREAMLIT_URL"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.write("📱 Players scan the QR code to join!")

    # Fetch game info
    game = supabase.table("game_info").select("*").eq("id", 1).single().execute().data

    # Start game button
    if not game["game_started"]:
        if st.button("Start Game"):
            supabase.table("game_info").update({"game_started": True, "current_question": 0}).eq("id", 1).execute()
            st.success("Game started!")

    else:
        st.write(f"Game in progress... Current Question: {game['current_question'] + 1}/{len(questions)}")

        # Leaderboard
        scores = supabase.table("game_scores").select("*").order("score", desc=True).limit(3).execute().data
        if scores:
            df = pd.DataFrame(scores)
            df.insert(0, "Rank", range(1, len(df) + 1))
            st.subheader("🏆 Leaderboard - Top 3")
            st.table(df[["Rank", "player_name", "score"]])

    # Restart Game button
    if st.button("Restart Game"):
        # Reset game info
        supabase.table("game_info").update({"game_started": False, "current_question": 0}).eq("id", 1).execute()
        # Clear all player scores
        supabase.table("game_scores").delete().neq("id", 0).execute()  # Delete all rows
        st.success("Game has been reset! Players can rejoin.")

# -------------------------------
# Player screen
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    else:
        st.write(f"Welcome, **{st.session_state.player_name}**!")

        # Register player in Supabase if new
        players = supabase.table("game_scores").select("*").eq("player_name", st.session_state.player_name).execute().data
        if not players:
            supabase.table("game_scores").insert({"player_name": st.session_state.player_name, "score": 0}).execute()

        # Fetch game info
        game = supabase.table("game_info").select("*").eq("id", 1).single().execute().data

        if not game["game_started"]:
            st.warning("Waiting for host to start the game...")
            st.stop()

        q_index = game["current_question"]
        if q_index >= len(questions):
            st.success("Game finished!")
            scores = supabase.table("game_scores").select("*").order("score", desc=True).limit(3).execute().data
            if scores:
                df = pd.DataFrame(scores)
                df.insert(0, "Rank", range(1, len(df) + 1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "player_name", "score"]])
            st.stop()

        # Question display
        q = questions[q_index]
        if "selected_answer" not in st.session_state:
            st.session_state.selected_answer = None
        if "answered" not in st.session_state:
            st.session_state.answered = False
        if "start_time" not in st.session_state:
            st.session_state.start_time = time.time()
        if "feedback_time" not in st.session_state:
            st.session_state.feedback_time = None

        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, QUESTION_TIME - elapsed)

        st.write(f"**Question {q_index + 1}: {q['question']}**")
        st.session_state.selected_answer = st.radio(
            "Choose your answer:",
            q["options"],
            index=0,
            key=f"q{q_index}"
        )

        st.write(f"⏳ Time left: {remaining} sec")

        if (st.button("Submit") or remaining == 0) and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.feedback_time = time.time()

            correct = st.session_state.selected_answer == q["answer"]
            # Update score
            player = supabase.table("game_scores").select("*").eq("player_name", st.session_state.player_name).single().execute().data
            new_score = player["score"] + (POINTS_PER_QUESTION if correct else 0)
            supabase.table("game_scores").update({"score": new_score}).eq("player_name", st.session_state.player_name).execute()

        # Feedback
        if st.session_state.answered:
            if st.session_state.selected_answer == q["answer"]:
                st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
            else:
                st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

            elapsed_feedback = time.time() - st.session_state.feedback_time
            if elapsed_feedback > FEEDBACK_TIME:
                st.write("Waiting for host to advance the question...")
            else:
                st.write(f"➡️ Next question in {FEEDBACK_TIME - int(elapsed_feedback)} sec...")
