
import streamlit as st
from agent.deep_agent import Agents


st.set_page_config(page_title="Chat", page_icon="💬")
st.title("💬 Chat")

# Sidebar
with st.sidebar:
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# Init history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input
if prompt := st.chat_input("Say something..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get agent response
    agent_instance = Agents(model_name="gpt-oss:20b")
    agent_instance.config_agent()
    agent = agent_instance.get_agent()
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        with st.spinner(text="Thinking..."):
          full_response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
          ai_response=full_response.get("messages",{})[-1].content
        response_placeholder.write(ai_response)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})
  