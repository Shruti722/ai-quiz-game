# -------------------------------
# Player Screen
# -------------------------------
if mode == "Player":
    st.title("🎮 Quiz Game Player")

    # Enter name
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if not st.session_state.player_name:
        st.session_state.player_name = st.text_input("Enter your first name:")
        st.stop()
    st.write(f"Welcome, **{st.session_state.player_name}**!")

    # Reload state every refresh
    state = load_state()

    # Register player safely
    if st.session_state.player_name not in state["players"]:
        state["players"][st.session_state.player_name] = 0
        save_state(state)

    # Show number of players on host (optional)
    # This is only visible on host, but can log to state
    state = load_state()

    if not state["game_started"]:
        st.warning("⏳ Waiting for host to start the game...")
        st.stop()

    if state["game_over"]:
        st.success("🎉 Game Over! Thank you for playing.")
        if state["scores"]:
            df = pd.DataFrame(state["scores"]).sort_values(by="score", ascending=False)
            df.insert(0, "Rank", range(1, len(df)+1))
            st.subheader("🏆 Final Leaderboard")
            st.table(df[["Rank","name","score"]])
        st.stop()

    # Reset answered state if host moved to next question
    if "last_question_index" not in st.session_state:
        st.session_state.last_question_index = state["current_question"]

    if st.session_state.last_question_index != state["current_question"]:
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.last_question_index = state["current_question"]

    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "selected_answer" not in st.session_state:
        st.session_state.selected_answer = None

    # Get current question
    q_index = state["current_question"]
    q = state["questions"][q_index]

    st.markdown(f"**Question {q_index+1}: {q['question']}**")

    # Countdown timer synced with host
    remaining = max(0, QUESTION_TIME - int(time.time() - state.get("host_question_start", time.time())))
    st.write(f"⏳ Time left for this question: {remaining} sec")

    # Options
    st.session_state.selected_answer = st.radio("Choose your answer:", q["options"], key=f"q{q_index}")

    # Submit answer button
    if st.button("Submit") and not st.session_state.answered:
        st.session_state.answered = True
        correct = st.session_state.selected_answer == q["answer"]

        # Update score safely without overwriting game state
        updated = False
        for s in state["scores"]:
            if s["name"] == st.session_state.player_name:
                if correct:
                    s["score"] += POINTS_PER_QUESTION
                updated = True
                break
        if not updated:
            state["scores"].append({
                "name": st.session_state.player_name,
                "score": POINTS_PER_QUESTION if correct else 0
            })
        save_state(state)

    # Show result only after Submit
    if st.session_state.answered:
        if st.session_state.selected_answer == q["answer"]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect ❌.")
