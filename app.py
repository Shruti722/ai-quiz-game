import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
from datetime import datetime
import google.generativeai as genai
import traceback

# —————————––

# Config

# —————————––

STATE_FILE = “state.json”
GAME_URL = “https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app/?role=Player”
QUESTION_TIME = 20
POINTS_PER_QUESTION = 5
AUTO_REFRESH_INTERVAL = 1000  # milliseconds

# —————————––

# Page Config

# —————————––

st.set_page_config(
page_title=“AI Quiz Game”,
page_icon=“🎮”,
layout=“wide”
)

# —————————––

# Gemini Setup

# —————————––

GEMINI_API_KEY = st.secrets.get(“GEMINI_API_KEY”, “AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y”)
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = “gemini-1.5-flash”  # Using flash for faster response

# —————————––

# Fallback Questions

# —————————––

FALLBACK_QUESTIONS = [
{“question”: “What does the standard deviation measure?”, “options”: [“The central value of data”,“The spread of data around the mean”,“The most common value”,“The difference between max and min”], “answer”: “The spread of data around the mean”},
{“question”: “Which company built AlphaGo, the AI agent that beat a Go world champion?”, “options”: [“OpenAI”,“DeepMind”,“IBM”,“Microsoft”], “answer”: “DeepMind”},
{“question”: “Which measure of central tendency is most affected by extreme values?”, “options”: [“Mean”,“Median”,“Mode”,“Range”], “answer”: “Mean”},
{“question”: “Which of these best describes ‘data literacy’?”, “options”: [“Ability to read and work with data”,“Ability to code”,“Ability to memorize statistics”,“Ability to create charts only”], “answer”: “Ability to read and work with data”},
{“question”: “What is a ‘multi-agent system’?”, “options”: [“AI working in isolation”,“Multiple AI agents interacting”,“Humans and AI working together”,“One AI agent with multiple tasks”], “answer”: “Multiple AI agents interacting”},
{“question”: “Which famous AI agent defeated Garry Kasparov in chess?”, “options”: [“AlphaGo”,“Siri”,“Deep Blue”,“Watson”], “answer”: “Deep Blue”},
{“question”: “What is the primary purpose of data visualization?”, “options”: [“To make data look pretty”,“To identify patterns and insights”,“To store data”,“To clean data”], “answer”: “To identify patterns and insights”},
{“question”: “Which AI agent famously won Jeopardy! against human champions?”, “options”: [“Siri”,“Watson”,“Alexa”,“BERT”], “answer”: “Watson”},
{“question”: “Which of these is an example of a reactive AI agent?”, “options”: [“Chess AI”,“Personal Assistant”,“Self-driving car”,“Spam filter”], “answer”: “Spam filter”},
{“question”: “What does a histogram show?”, “options”: [“Trends over time”,“Distribution of data”,“Relationship between variables”,“Averages only”], “answer”: “Distribution of data”},
]

# —————————––

# State Management with File Locking

# —————————––

def get_default_state():
“”“Returns the default state structure”””
return {
“game_started”: False,
“current_question”: 0,
“scores”: [],
“game_over”: False,
“players”: {},
“questions”: [],
“host_question_start”: time.time(),
“last_updated”: time.time(),
“game_id”: datetime.now().strftime(”%Y%m%d_%H%M%S”)
}

def save_state(state):
“”“Save state with error handling”””
try:
state[“last_updated”] = time.time()
temp_file = STATE_FILE + “.tmp”
with open(temp_file, “w”) as f:
json.dump(state, f, indent=2)
# Atomic rename to avoid corruption
os.replace(temp_file, STATE_FILE)
return True
except Exception as e:
st.error(f”Error saving state: {e}”)
return False

def load_state():
“”“Load state with comprehensive error handling”””
if not os.path.exists(STATE_FILE):
state = get_default_state()
save_state(state)
return state

```
try:
    with open(STATE_FILE, "r") as f:
        content = f.read()
        if not content:
            raise ValueError("Empty state file")
        state = json.loads(content)

    # Validate and repair state structure
    default_state = get_default_state()
    for key, value in default_state.items():
        if key not in state:
            state[key] = value

    return state
except Exception as e:
    st.warning(f"State file corrupted, resetting: {e}")
    state = get_default_state()
    save_state(state)
    return state
```

def reset_game():
“”“Complete game reset”””
state = get_default_state()
state[“questions”] = get_ai_questions()
save_state(state)
return state

# —————————––

# Question Generator

# —————————––

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_ai_questions():
“”“Generate questions using Gemini AI with fallback”””
prompt = “””
Create exactly 10 multiple-choice quiz questions about Data Literacy and AI Agents.
Mix basic and intermediate difficulty levels.

```
Return ONLY a valid JSON array with this exact structure:
[
  {
    "question": "Question text here?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "answer": "The correct option exactly as written in options"
  }
]

Ensure each question has exactly 4 options and the answer matches one option exactly.
"""

try:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    # Clean the response text
    text = response.text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    questions = json.loads(text.strip())

    # Validate questions structure
    if not isinstance(questions, list) or len(questions) < 5:
        raise ValueError("Invalid questions format")

    for q in questions:
        if not all(k in q for k in ["question", "options", "answer"]):
            raise ValueError("Missing required fields")
        if len(q["options"]) != 4:
            raise ValueError("Must have exactly 4 options")
        if q["answer"] not in q["options"]:
            raise ValueError("Answer must be in options")

    return questions[:10]  # Limit to 10 questions

except Exception as e:
    st.warning(f"Using fallback questions due to: {e}")
    return FALLBACK_QUESTIONS
```

# —————————––

# Auto-refresh Component

# —————————––

def auto_refresh():
“”“Custom auto-refresh implementation”””
if “last_refresh” not in st.session_state:
st.session_state.last_refresh = time.time()

```
current_time = time.time()
if current_time - st.session_state.last_refresh > 1:  # Refresh every second
    st.session_state.last_refresh = current_time
    st.rerun()
```

# Add JavaScript for auto-refresh (backup method)

auto_refresh_script = “””

<script>
setTimeout(function(){
    window.location.reload();
}, 1000);
</script>

“””

# —————————––

# Initialize Session State

# —————————––

if “initialized” not in st.session_state:
st.session_state.initialized = True
st.session_state.player_name = “”
st.session_state.answered = False
st.session_state.selected_answer = None
st.session_state.last_question_index = -1
st.session_state.player_score = 0

# Load current state

state = load_state()

# Generate questions if needed

if not state[“questions”]:
with st.spinner(“Generating quiz questions…”):
state[“questions”] = get_ai_questions()
save_state(state)

# —————————––

# Mode Selection

# —————————––

params = st.query_params
role = params.get(“role”, “Host”)

with st.sidebar:
st.title(“🎮 Quiz Game Settings”)
mode = st.selectbox(
“Select mode:”,
[“Host”, “Player”],
index=0 if role == “Host” else 1,
key=“mode_selector”
)

```
st.divider()
st.caption(f"Game ID: {state.get('game_id', 'Unknown')}")
st.caption(f"Questions: {len(state['questions'])}")
st.caption(f"Time per question: {QUESTION_TIME}s")
```

# —————————––

# Host Screen

# —————————––

if mode == “Host”:
st.title(“🎮 AI Quiz Game - Host Console”)

```
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("📱 Join Game")
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)
    st.markdown(f"[Join as Player]({GAME_URL})")

with col2:
    st.subheader("📊 Game Status")

    # Game controls
    if not state["game_started"]:
        st.info(f"👥 Players joined: {len(state['players'])}")

        if len(state['players']) > 0:
            st.write("Ready players:", ", ".join(state['players'].keys()))

        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            state["host_question_start"] = time.time()
            state["scores"] = []  # Reset scores
            save_state(state)
            st.success("Game started!")
            st.rerun()

    elif not state["game_over"]:
        # Game in progress
        q_num = state["current_question"] + 1
        total_q = len(state["questions"])

        progress = q_num / total_q
        st.progress(progress, text=f"Question {q_num} of {total_q}")

        # Timer
        elapsed = int(time.time() - state["host_question_start"])
        remaining = max(0, QUESTION_TIME - elapsed)

        st.metric("Time Remaining", f"{remaining}s")

        # Current question display
        if state["current_question"] < len(state["questions"]):
            q = state["questions"][state["current_question"]]
            st.info(f"**Current Question:** {q['question']}")

        # Auto-advance logic
        if elapsed >= QUESTION_TIME:
            if state["current_question"] < len(state["questions"]) - 1:
                state["current_question"] += 1
                state["host_question_start"] = time.time()
                save_state(state)
                st.rerun()
            else:
                state["game_over"] = True
                save_state(state)
                st.rerun()

        # Manual controls
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⏭️ Next Question"):
                if state["current_question"] < len(state["questions"]) - 1:
                    state["current_question"] += 1
                    state["host_question_start"] = time.time()
                else:
                    state["game_over"] = True
                save_state(state)
                st.rerun()

        with col_b:
            if st.button("🏁 End Game"):
                state["game_over"] = True
                save_state(state)
                st.rerun()

    else:
        # Game over
        st.success("🎉 Game Complete!")

    # Reset button
    if st.button("🔄 Reset Game", type="secondary", use_container_width=True):
        state = reset_game()
        st.success("Game reset! New questions generated.")
        st.rerun()

with col3:
    st.subheader("🏆 Leaderboard")
    if state["scores"]:
        df = pd.DataFrame(state["scores"])
        df = df.sort_values(by="score", ascending=False).head(10)
        df.insert(0, "🏅", ["🥇", "🥈", "🥉"] + [""] * (len(df) - 3) if len(df) >= 3 else ["🥇", "🥈", "🥉"][:len(df)])
        st.dataframe(
            df[["🏅", "name", "score"]],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No scores yet")

# Auto-refresh
st.markdown(auto_refresh_script, unsafe_allow_html=True)
```

# —————————––

# Player Screen

# —————————––

elif mode == “Player”:
st.title(“🎮 AI Quiz Game - Player”)

```
# Player name entry
if not st.session_state.player_name:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Welcome! 👋")
        name_input = st.text_input(
            "Enter your name to join:",
            placeholder="Your name",
            max_chars=20
        )
        if st.button("Join Game", type="primary", use_container_width=True) and name_input:
            st.session_state.player_name = name_input
            # Register player
            state["players"][name_input] = {
                "joined": time.time(),
                "score": 0
            }
            save_state(state)
            st.rerun()
    st.stop()

# Game interface
player_name = st.session_state.player_name
st.sidebar.success(f"Playing as: **{player_name}**")

# Check game status
if not state["game_started"]:
    st.info("⏳ Waiting for host to start the game...")
    st.write(f"Players in lobby: {len(state['players'])}")

    # Show waiting animation
    with st.spinner("Refreshing..."):
        time.sleep(1)
    st.rerun()

elif state["game_over"]:
    st.balloons()
    st.success("🎉 Game Over!")

    # Show final leaderboard
    if state["scores"]:
        df = pd.DataFrame(state["scores"])
        df = df.sort_values(by="score", ascending=False)
        df.insert(0, "Rank", range(1, len(df) + 1))

        # Highlight player's score
        player_rank = df[df["name"] == player_name]["Rank"].values
        if player_rank:
            st.metric("Your Rank", f"#{player_rank[0]}")

        st.subheader("📊 Final Leaderboard")
        st.dataframe(
            df[["Rank", "name", "score"]],
            hide_index=True,
            use_container_width=True
        )

else:
    # Game in progress
    q_index = state["current_question"]

    # Reset answer state when question changes
    if st.session_state.last_question_index != q_index:
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.last_question_index = q_index

    if q_index < len(state["questions"]):
        q = state["questions"][q_index]

        # Question header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"Question {q_index + 1} of {len(state['questions'])}")
        with col2:
            # Timer
            elapsed = int(time.time() - state["host_question_start"])
            remaining = max(0, QUESTION_TIME - elapsed)
            if remaining > 10:
                st.success(f"⏱️ {remaining}s")
            elif remaining > 5:
                st.warning(f"⏱️ {remaining}s")
            else:
                st.error(f"⏱️ {remaining}s")

        # Question
        st.markdown(f"### {q['question']}")

        # Answer options
        if not st.session_state.answered:
            selected = st.radio(
                "Select your answer:",
                q["options"],
                key=f"q_{q_index}_{player_name}",
                label_visibility="collapsed"
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ Submit Answer", type="primary", use_container_width=True):
                    if selected and remaining > 0:
                        st.session_state.answered = True
                        st.session_state.selected_answer = selected

                        # Check if correct
                        is_correct = (selected == q["answer"])

                        # Update score
                        player_found = False
                        for score_entry in state["scores"]:
                            if score_entry["name"] == player_name:
                                if is_correct:
                                    score_entry["score"] += POINTS_PER_QUESTION
                                player_found = True
                                break

                        if not player_found:
                            state["scores"].append({
                                "name": player_name,
                                "score": POINTS_PER_QUESTION if is_correct else 0
                            })

                        save_state(state)
                        st.rerun()
                    elif remaining <= 0:
                        st.error("⏰ Time's up!")

        else:
            # Show result
            if st.session_state.selected_answer == q["answer"]:
                st.success(f"✅ Correct! You earned {POINTS_PER_QUESTION} points!")
            else:
                st.error(f"❌ Incorrect. The correct answer was: **{q['answer']}**")

            st.info("Waiting for next question...")

    # Auto-refresh
    with st.spinner(""):
        time.sleep(1)
    st.rerun()
```

# Footer

st.divider()
st.caption(“🎮 AI Quiz Game - Built with Streamlit”)
