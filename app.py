import streamlit as st
import json
import os
import time
import random
import google.generativeai as genai

STATE_FILE = "state.json"

# Configure Gemini API
genai.configure(api_key=os.environ.get("AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y"))

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"players": {}, "current_q": 0, "game_started": False, "questions": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def reset_game():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

def get_ai_questions():
    """Generate 5 questions using Gemini API, fallback to defaults if error"""
    prompt = """
    Create 5 multiple-choice quiz questions about Data Literacy and AI Agents.
    Provide them as a JSON list with keys: question, options, answer.
    Example:
    [
      {"question": "What is structured data?", 
       "options": ["Images", "Tables with rows/columns", "Videos", "Audio"], 
       "answer": "Tables with rows/columns"}
    ]
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        questions = json.loads(response.text)
        return questions
    except Exception as e:
        # Fallback hardcoded questions
        return [
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

# Streamlit UI
st.set_page_config(page_title="AI Quiz Game", layout="centered")

role = st.sidebar.radio("Choose role:", ["Host", "Player"])

# ----------------- HOST -----------------
if role == "Host":
    st.title("👩‍💻 Quiz Game Host")
    state = load_state()

    if not state["game_started"]:
        if st.button("🚀 Start Game"):
            state["questions"] = get_ai_questions()
            state["game_started"] = True
            state["current_q"] = 0
            save_state(state)
            st.success("Game started! Players can now see the first question.")
    else:
        st.subheader("📊 Game in Progress")
        st.write(f"Current Question: {state['current_q']+1} / {len(state['questions'])}")

        # Leaderboard
        sorted_players = sorted(state["players"].items(), key=lambda x: x[1], reverse=True)
        st.write("🏆 Leaderboard")
        for i, (player, score) in enumerate(sorted_players, start=1):
            st.write(f"{i}. {player}: {score} points")

# ----------------- PLAYER -----------------
else:
    st.title("🎮 Quiz Game Player")
    name = st.text_input("Enter your first name:")

    if name:
        state = load_state()
        if name not in state["players"]:
            state["players"][name] = 0
            save_state(state)

        if not state["game_started"]:
            st.info("⏳ Waiting for host to start the game...")
        else:
            q_index = state["current_q"]
            if q_index < len(state["questions"]):
                q = state["questions"][q_index]
                st.subheader(q["question"])
                choice = st.radio("Choose an option:", q["options"], key=f"{name}_{q_index}")

                if st.button("Submit Answer", key=f"submit_{name}_{q_index}"):
                    if choice == q["answer"]:
                        st.success("✅ Correct!")
                        state["players"][name] += 5
                    else:
                        st.error(f"❌ Incorrect! Correct answer: {q['answer']}")
                    save_state(state)

# ----------------- RESET -----------------
st.sidebar.subheader("⚙️ Admin Controls")
if st.sidebar.button("🔄 Reset Game"):
    reset_game()
    st.sidebar.success("Game reset!")
