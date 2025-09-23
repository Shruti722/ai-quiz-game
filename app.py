import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO
import json
import os
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai
import re
import difflib

# -------------------------------
# CONFIG
# -------------------------------
# Put your Gemini API key here (insecure to hardcode on public repos)
genai.configure(api_key="AIzaSyAUd8_UuRowt-QmJBESIBTEXC8dnSDWk_Y")

STATE_FILE = "state.json"
GAME_URL = "https://ai-quiz-game-vuwsfb3hebgvdstjtewksd.streamlit.app"  # replace with your deployed URL

QUESTION_TIME = 15
POINTS_PER_QUESTION = 5

# -------------------------------
# Fallback (static) questions
# -------------------------------
FALLBACK_QUESTIONS = [
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
# Helpers: state load/save
# -------------------------------
def init_state_if_missing():
    if not os.path.exists(STATE_FILE):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "questions": []}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# -------------------------------
# String normalization & sanitization
# -------------------------------
def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    # collapse whitespace and lowercase
    return re.sub(r'\s+', ' ', s).strip().lower()

def sanitize_questions(raw_questions):
    """
    Validate and sanitize the AI output.
    Return sanitized list or None if invalid.
    """
    if not isinstance(raw_questions, list):
        return None
    sanitized = []
    for q in raw_questions:
        if not isinstance(q, dict):
            return None
        question_text = q.get("question", "")
        options = q.get("options", [])
        answer_raw = q.get("answer", "")

        # ensure question text and options exist
        if not question_text or not isinstance(options, list):
            return None

        # make sure there are at least 4 options (we require exactly 4)
        # truncate or pad if necessary (prefer truncation)
        opts_clean = [str(o).strip() for o in options if str(o).strip() != ""]
        if len(opts_clean) < 4:
            return None  # invalid; reject entire AI output quickly
        opts_clean = opts_clean[:4]

        # Try to determine the canonical answer string from answer_raw
        norm_opts = [normalize_text(o) for o in opts_clean]
        norm_answer = normalize_text(answer_raw)

        chosen_answer = None
        # direct normalized match
        if norm_answer in norm_opts:
            chosen_answer = opts_clean[norm_opts.index(norm_answer)]
        else:
            # if answer is like "B" or "b" or "B)" or "Option B"
            m = re.search(r'\b([A-Da-d])\b', answer_raw)
            if m:
                idx = ord(m.group(1).upper()) - ord('A')
                if 0 <= idx < len(opts_clean):
                    chosen_answer = opts_clean[idx]
            if chosen_answer is None:
                # digit 1-4
                m2 = re.search(r'\b([1-4])\b', answer_raw)
                if m2:
                    idx = int(m2.group(1)) - 1
                    if 0 <= idx < len(opts_clean):
                        chosen_answer = opts_clean[idx]

        if chosen_answer is None:
            # try fuzzy matching
            close = difflib.get_close_matches(answer_raw, opts_clean, n=1, cutoff=0.6)
            if close:
                chosen_answer = close[0]

        if chosen_answer is None:
            # last resort: if one option contains the answer substring
            for o in opts_clean:
                if normalize_text(answer_raw) in normalize_text(o):
                    chosen_answer = o
                    break

        if chosen_answer is None:
            return None  # treat AI output as invalid

        sanitized.append({
            "question": str(question_text).strip(),
            "options": opts_clean,
            "answer": chosen_answer
        })
    return sanitized

# -------------------------------
# AI question generator (Gemini)
# -------------------------------
def generate_ai_questions():
    prompt = """
    Generate 5 multiple-choice quiz questions about Data Literacy and AI Agents.
    Return ONLY valid JSON (no explanations, no markdown).
    Output format exactly as:
    [
      {"question": "...", "options": ["A","B","C","D"], "answer": "B"},
      ...
    ]
    Make sure "answer" value exactly matches one of the options (not a letter).
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # request application/json to reduce markdown / extra text
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        raw_text = response.text
        # Try to parse JSON directly
        try:
            raw = json.loads(raw_text)
        except Exception:
            # strip common code fences and try again
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                parts = cleaned.split("```")
                # try inner parts for json
                for part in parts:
                    try:
                        candidate = part.strip()
                        j = json.loads(candidate)
                        raw = j
                        break
                    except Exception:
                        raw = None
                if raw is None:
                    raise ValueError("Could not parse Gemini JSON output.")
            else:
                raise

        sanitized = sanitize_questions(raw)
        if sanitized is None:
            raise ValueError("Sanitization failed for AI output.")
        return sanitized

    except Exception as e:
        # immediate fallback to static questions
        return FALLBACK_QUESTIONS

# -------------------------------
# Init state if missing
# -------------------------------
init_state_if_missing()

# -------------------------------
# Auto-refresh every 1 sec (keeps players in sync while waiting)
# -------------------------------
st_autorefresh(interval=1000, limit=None, key="quiz_autorefresh")

# -------------------------------
# App Mode (UI layout same as your layout)
# -------------------------------
mode = st.sidebar.selectbox("Select mode:", ["Host", "Player"])

# -------------------------------
# Host screen
# -------------------------------
if mode == "Host":
    st.title("🎮 Quiz Game Host")
    st.write("📱 Players scan the QR code below to join:")

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(GAME_URL)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    st.image(buf, width=200)

    state = load_state()
    st.write(f"Players joined: {len(state['scores'])}")

    if not state["game_started"]:
        if st.button("Start Game with AI Agent Questions"):
            # show spinner while generating
            with st.spinner("Generating questions with AI..."):
                questions = generate_ai_questions()
            # questions already sanitized inside generate_ai_questions (or fallback)
            state["questions"] = questions
            state["game_started"] = True
            state["current_question"] = 0
            state["game_over"] = False
            save_state(state)
            st.success("Game started with AI-generated questions!")

    if st.button("Restart Game"):
        state = {"game_started": False, "current_question": 0, "scores": [], "game_over": False, "questions": []}
        save_state(state)
        st.success("Game has been reset! Players can rejoin.")

    # Show leaderboard or progress
    state = load_state()
    if state["game_started"]:
        if state["game_over"]:
            st.success("🎉 Game Over! Final Leaderboard:")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.table(df[["Rank", "name", "score"]])
        else:
            total_q = len(state.get("questions", []))
            st.write(f"Game in progress... Question {state['current_question'] + 1}/{total_q}")
            if state['scores']:
                df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False).head(3)
                df.insert(0, "Rank", range(1, len(df)+1))
                st.subheader("🏆 Leaderboard - Top 3")
                st.table(df[["Rank", "name", "score"]])

# -------------------------------
# Player screen
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    # session state initialization
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")

    if not st.session_state.player_name:
        st.stop()

    # register player (if first time)
    state = load_state()
    if not any(p.get("name") == st.session_state.player_name for p in state["scores"]):
        state["scores"].append({"name": st.session_state.player_name, "score": 0})
        save_state(state)
        state = load_state()

    st.write(f"Welcome, **{st.session_state.player_name}**!")

    state = load_state()
    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    if state.get("game_over", False):
        st.success("🎉 Game Over! Thank you for playing.")
        if state['scores']:
            df = pd.DataFrame(state['scores']).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank", "name", "score"]])
        st.stop()

    # get questions
    questions = state.get("questions", [])
    if not questions:
        st.error("⚠️ No questions available yet. Please wait for the host to start the game.")
        st.stop()

    # initialize timer for the question
    if st.session_state.start_time is None or st.session_state.answered:
        st.session_state.start_time = time.time()
        st.session_state.answered = False
        st.session_state.selected_answer = None

    q_index = state["current_question"]
    if q_index >= len(questions):
        st.warning("⚠️ Out of questions. Waiting for host to end the game...")
        st.stop()

    q = questions[q_index]

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, QUESTION_TIME - elapsed)

    st.write(f"**Question {q_index + 1}: {q['question']}**")
    st.session_state.selected_answer = st.radio(
        "Choose your answer:",
        q["options"],
        key=f"q{q_index}",
        index=0
    )
    st.write(f"⏳ Time left: {remaining} sec")

    # Submit button
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        # robust correctness check: normalize both sides
        sel = normalize_text(st.session_state.selected_answer)
        ans = normalize_text(q["answer"])
        is_correct = (sel == ans)
        # if not direct match, also try to map answer letter to option (A/B/C/D)
        if not is_correct:
            # try letter in answer
            m = re.search(r'\b([A-Da-d])\b', q.get("answer", ""))
            if m:
                idx = ord(m.group(1).upper()) - ord('A')
                if 0 <= idx < len(q["options"]):
                    is_correct = normalize_text(q["options"][idx]) == sel
        # If still not match, fallback to fuzzy equality
        if not is_correct:
            close = difflib.get_close_matches(q["answer"], q["options"], n=1, cutoff=0.6)
            if close:
                is_correct = normalize_text(close[0]) == sel

        # update scores in state (list of dicts)
        state = load_state()
        for s in state["scores"]:
            if s["name"] == st.session_state.player_name:
                if is_correct:
                    s["score"] += POINTS_PER_QUESTION
                break
        save_state(state)

        # immediate feedback
        if is_correct:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌. Correct answer: {q['answer']}")

    # keep feedback visible until timer ends
    if st.session_state.answered:
        # already shown above
        pass

    # Move to next question after QUESTION_TIME
    if elapsed >= QUESTION_TIME:
        state = load_state()
        if q_index < len(state["questions"]) - 1:
            state["current_question"] += 1
        else:
            state["game_over"] = True
        save_state(state)
        # reset session for next question
        st.session_state.start_time = time.time()
        st.session_state.selected_answer = None
        st.session_state.answered = False
