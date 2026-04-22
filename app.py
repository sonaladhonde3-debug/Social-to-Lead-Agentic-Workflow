import streamlit as st
from agent.graph import build_graph
from agent.state import AgentState

st.title("AutoStream AI Assistant")

# Initialize agent
if "agent" not in st.session_state:
    st.session_state.agent = build_graph()
    st.session_state.state = {
        "messages": [],
        "intent": None,
        "lead_name": None,
        "lead_email": None,
        "lead_platform": None,
        "lead_captured": False,
        "awaiting": None,
        "rag_context": None,
        "in_lead_flow": False
    }

# Display chat history
for msg in st.session_state.state["messages"]:
    with st.chat_message(msg["role"]):
        # Use st.markdown to avoid st.write interpreting $...$ as LaTeX math
        st.markdown(msg["content"])

# Input box
user_input = st.chat_input("Type your message...")

if user_input:
    state = st.session_state.state
    agent = st.session_state.agent

    # Add user message to history
    state["messages"].append({"role": "user", "content": user_input})

    # Run the agent
    result = agent.invoke(state)
    state.update(result)

    st.session_state.state = state

    # Rerun so the full chat history (user + assistant) renders from the loop above
    st.rerun()