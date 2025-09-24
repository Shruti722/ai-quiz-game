import streamlit as st
import json
import os
import random
import google.generativeai as genai
import qrcode
from io import BytesIO

# ---------------- CONFIG ----------------
STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"  # replace with your Streamlit app URL
QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# Configure Gemini API
genai.configure(api_key=os.getenv("AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y"))

# ---------------- HELPERS ----------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"players": {}, "current_q": 0, "started": False, "questions": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def generate_ai_questions():
    try:
        model = genai.GenerativeModel("gemini-1.5-turbo")
        prompt = (
            "Generate 15 multiple-choice questions with 4 options each. "
            "Topics: data literacy, AI agents, and descriptive statistics. "
            "Format strictly as JSON list: "
            '[{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A"}]'
        )
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        st.warning(f"AI question generation failed: {e}")
        return None

# ---------------- FALLBACK QUESTIONS ----------------
FALLBACK_QUESTIONS = [
    {
        "question": "What does the standard deviation measure?",
        "options": ["The central value of data", "The spread of data around the mean", "The most common value", "The difference between max and min"],
        "answer": "The spread of data around the mean"
    },
    {
        "question": "Which company built AlphaGo, the AI agent that beat a Go world champion?",
        "options": ["OpenAI", "DeepMind", "IBM", "Microsoft"],
        "answer": "DeepMind"
    },
    {
        "question": "Which measure of central tendency is most affected by extreme values?",
        "options": ["Mean", "Median", "Mode", "Range"],
        "answer": "Mean"
    },
    {
        "question": "Which of these best describes 'data literacy'?",
        "options": ["Ability to read and work with data", "Ability to code", "Ability to memorize statistics", "Ability to create charts only"],
        "answer": "Ability to read and work with data"
    },
    {
        "question": "What is a 'multi-agent system'?",
        "options": ["AI working in isolation", "Multiple AI agents interacting", "Humans and AI working together", "One AI agent with multiple tasks"],
        "answer": "Multiple AI agents interacting"
    },
    {
        "question": "Which famous AI agent defeated Garry Kasparov in chess?",
        "options": ["AlphaGo", "Siri", "Deep Blue", "Watson"],
        "answer": "Deep Blue"
    },
    {
        "question": "What is the primary purpose of data visualization?",
        "options": ["To make data look pretty", "To identify patterns and insights", "To store data", "To clean data"],
        "answer": "To identify patterns and insights"
    },
    {
        "question": "Which AI agent famously won Jeopardy! against human champions?",
        "options": ["Siri", "Watson", "Alexa", "BERT"],
        "answer": "Watson"
    },
    {
        "question": "Which of these is an example of a reactive AI agent?",
        "options": ["Chess AI", "Personal Assistant", "Self-driving car", "Spam filter"],
        "answer": "Spam filter"
    },
    {
        "question": "What does a histogram show?",
        "options": ["Trends over time", "Distribution of data", "Relationship between variables", "Averages only"],
        "answer": "Distribution of data"
    },
    {
        "question": "If the mean = median = mode in a dataset, what is its distribution?",
        "options": ["Skewed left", "Skewed right", "Normal distribution", "Uniform distribution"],
        "answer": "Normal distribution"
    },
    {
        "question": "What is the 'environment' in AI agents?",
        "options": ["The physical world only", "The context in which an agent operates", "The internet", "The dataset only"],
        "answer": "The context in which an agent operates"
    },
    {
        "question": "Which type of chart is best for showing parts of a whole?",
        "options": ["Bar chart", "Pie chart", "Histogram", "Scatter plot"],
        "answer": "Pie chart"
    },
    {
        "question": "What is an AI agent?",
        "options": ["A piece of software that perceives and acts in an environment", "A robot only", "Any computer program", "A human working with AI"],
        "answer": "A piece of software that perceives and acts in an environment"
    },
    {
        "question": "What does a pie chart represent best?",
        "options": ["Parts of a whole", "Trends over time", "Correlation between variables", "Frequency distribution"],
        "answer": "Parts of a whole"
    }
]
# ---------------- MAIN APP ----------------
st.title("🎉 AI Quiz Game")

params = st.query_params
role = params.get("role", [None])[0]

state = load_state()

if role is None:
    st.header("Select Mode")
    if st.button("Host"):
        st.switch_page("app.py?role=host")
    if st.button("Player"):
        st.switch_page("app.py?role=player")

elif role.lower() == "host":
    st.header("👩‍🏫 Host Screen")
    
    if st.button("Start Game"):
        ai_questions = generate_ai_questions()
        state["questions"] = ai_questions if ai_questions else FALLBACK_QUESTIONS
        state["current_q"] = 0
        state["started"] = True
        state["players"] = {}
        save_state(state)
        st.rerun()

    st.write(f"Players joined: {len(state.get('players', {}))}")

    # QR code + clickable link
    qr = qrcode.make(f"{GAME_URL}?role=player")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="Scan to Join")
    st.markdown(f"[Or click here to join as Player]({GAME_URL}?role=player)")

    if state["started"]:
        questions = state.get("questions", FALLBACK_QUESTIONS)
        q_index = state["current_q"]
        if q_index < len(questions):
            q = questions[q_index]
            st.subheader(f"Question {q_index + 1}: {q['question']}")
            for option in q["options"]:
                st.write(f"- {option}")
        else:
            st.success("Game Over! 🎉")
            scores = state.get("players", {})
            if scores:
                winner = max(scores, key=scores.get)
                st.write(f"🏆 Winner: {winner} with {scores[winner]} points")

elif role.lower() == "player":
    st.header("🎮 Player Screen")
    name = st.text_input("Enter your first name:")
    if name:
        if "players" not in state:
            state["players"] = {}
        if name not in state["players"]:
            state["players"][name] = 0
            save_state(state)

        if not state.get("started", False):
            st.info("Waiting for host to start the game...")
        else:
            questions = state.get("questions", FALLBACK_QUESTIONS)
            q_index = state["current_q"]
            if q_index < len(questions):
                q = questions[q_index]
                st.subheader(q["question"])
                answer = st.radio("Choose your answer:", q["options"], key=f"{name}_{q_index}")
                if st.button("Submit Answer", key=f"submit_{name}_{q_index}"):
                    if answer == q["answer"]:
                        state["players"][name] += POINTS_PER_QUESTION
                        st.success("✅ Correct!")
                    else:
                        st.error("❌ Incorrect.")
                    state["current_q"] += 1
                    save_state(state)
                    st.rerun()
            else:
                st.success("🎉 Quiz completed!")
