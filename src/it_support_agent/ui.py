"""Streamlit chat UI for the agent.

Run with:  uv run streamlit run src/it_support_agent/ui.py
"""

import os

import streamlit as st
from openai import OpenAIError

from it_support_agent.cli import build_agent
from it_support_agent.core.config import Settings
from it_support_agent.core.exceptions import AgentError
from it_support_agent.core.logging import setup_logging

SAMPLE_QUESTIONS = [
    "payment-server-01 is slow, please handle it",
    "auth-service-03 keeps crashing",
    "search-index-09 has a problem, please handle it",
    "Is db-node-02 ok?",
    "Check frontend-node-04 and db-node-02",
]

st.set_page_config(page_title="IT Support Agent", page_icon=":wrench:")
st.title("IT Support Agent")
st.caption("Describe a server problem. Server data is mocked: nothing real is restarted or ticketed.")

with st.sidebar:
    st.header("API key")
    env_has_key = bool(os.getenv("OPENROUTER_API_KEY"))
    typed_key = st.text_input(
        "OpenRouter API key",
        type="password",
        placeholder="sk-or-...",
        help="Get one at https://openrouter.ai/keys. Used only for this browser session, never saved.",
    ).strip()
    if typed_key:
        st.caption("Using the key you entered.")
    elif env_has_key:
        st.caption("Using the key from `.env`. Enter one above to use a different key.")
    else:
        st.caption("No key in `.env`, so enter one above to start.")

# Streamlit re-runs this whole script on every click, so the agent (and its
# conversation history) lives in session_state to survive between runs.
# It is rebuilt, with a fresh conversation, whenever the key changes.
if st.session_state.get("agent_key") != typed_key or "agent" not in st.session_state:
    try:
        settings = Settings.from_env(api_key=typed_key or None)
    except RuntimeError:
        st.info("Enter your OpenRouter API key in the sidebar to start chatting.")
        st.stop()
    setup_logging(settings.log_level)
    st.session_state.agent = build_agent(settings)
    st.session_state.agent_key = typed_key
    st.session_state.chat = []  # (role, text) pairs shown on screen

agent = st.session_state.agent
chat: list[tuple[str, str]] = st.session_state.chat

with st.sidebar:
    st.divider()
    st.header("Sample questions")
    for question in SAMPLE_QUESTIONS:
        if st.button(question, width="stretch"):
            st.session_state.pending = question
    st.divider()
    if st.button("Clear conversation", width="stretch"):
        agent.reset()
        chat.clear()
        st.rerun()

prompt = st.chat_input("e.g. payment-server-01 is slow") or st.session_state.pop("pending", None)

if not chat and not prompt:
    st.subheader("Try one of these")
    for i, question in enumerate(SAMPLE_QUESTIONS):
        if st.button(question, key=f"start-{i}", width="stretch"):
            st.session_state.pending = question
            st.rerun()

for role, text in chat:
    st.chat_message(role).markdown(text)

if prompt:
    chat.append(("user", prompt))
    st.chat_message("user").markdown(prompt)
    with st.chat_message("assistant"), st.spinner("Checking the servers..."):
        try:
            answer = agent.run(prompt)
        except (AgentError, OpenAIError) as exc:
            answer = f"**Error:** {exc}"
        st.markdown(answer)
    chat.append(("assistant", answer))
