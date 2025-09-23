import streamlit as st
import json, time

STATE_FILE = "state.json"
QUESTIONS_FILE = "questions.json"

def load_state():
    try: return json.load(open(STATE_FILE))
    except: return {"started": False, "current_q": 0, "players": {}}

def save_state(state):
    json.dump(state, open(STATE_FILE,"w"))

QUESTIONS = json.load(open(QUESTIONS_FILE))

st.title("🎮 Player Screen")

if "name" not in st.session_state:
    st.session_state.name = st.text_input("Enter your name:")
    if st.session_state.name:
        state = load_state()
        state["players"][st.session_state.name] = 0
        save_state(state)
        st.success("Joined! Wait for host...")
    st.stop()

state = load_state()
if not state["started"]:
    st.info("⏳ Waiting for host...")
    st.stop()

q_idx = state["current_q"]
if q_idx >= len(QUESTIONS):
    st.success("🎉 Game finished!")
    st.stop()

q = QUESTIONS[q_idx]
st.subheader(f"Q{q_idx+1}: {q['question']}")
choice = st.radio("Choose:", q["options"], index=None)

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

elapsed = int(time.time()-st.session_state.start_time)
remaining = max(0, 15-elapsed)
st.write(f"⏳ Time left: {remaining} sec")

if remaining==0:
    if choice==q["answer"]:
        st.success("✅ Correct! +5 points")
        state["players"][st.session_state.name]+=5
    else:
        st.error(f"❌ Wrong! Correct: {q['answer']}")
    save_state(state)
    for i in range(3,0,-1):
        st.write(f"Next Q in {i}...")
        time.sleep(1)
    st.session_state.start_time=time.time()
    st.rerun()
