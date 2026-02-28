import streamlit as st
from agent.deep_agent import Agents
from utils.util import fetch_supported_models


st.set_page_config(page_title="Chat", page_icon="💬")
st.title("💬 Chat")

if "supported_models" not in st.session_state:
    st.session_state.supported_models = fetch_supported_models()

_default_model = "gpt-oss:120b"
if _default_model not in st.session_state.supported_models:
    st.session_state.supported_models.insert(0, _default_model)

if "model_choice" not in st.session_state:
    st.session_state.model_choice = _default_model

with st.sidebar:
    st.session_state.model_choice = st.selectbox(
        "Model",
        st.session_state.supported_models,
        index=st.session_state.supported_models.index(_default_model),
    )
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    model_name = st.session_state.model_choice
    agent_instance = Agents(model_name=model_name)
    agent = agent_instance.get_agent()

    with st.chat_message("assistant"):
      response_placeholder = st.empty()
      thinking_container = st.container()
      ai_response = ""

    with st.spinner("Thinking..."):
        for namespace, chunk in agent.stream(
            {"messages": [{"role": "user", "content": prompt}]},
            stream_mode="updates",
            subgraphs=True,
        ):
            with thinking_container:
              if not namespace:
                  agent_label = "Main agent"
              else:
                  agent_label = f"Sub-agent {namespace[0]}"

              for node_name, data in chunk.items():
                  if node_name == "model":
                      if not isinstance(data, dict):
                          continue

                      messages = data.get("messages", [])
                      if not messages:
                          continue
                      msg = messages[-1]
                      if hasattr(msg, "tool_calls") and msg.tool_calls:
                          for tc in msg.tool_calls:
                              tool_name = tc.get("name", "unknown")
                              with st.expander(
                                  f"🔧 Tool call · {tool_name}  ({agent_label})",
                                  expanded=False
                              ):
                                  st.json(tc.get("args", {}))

                      if not namespace and msg.content:
                          ai_response = msg.content
                          response_placeholder.write(ai_response)
                  elif node_name == "tools":
                      if not isinstance(data, dict):
                          continue
                      messages = data.get("messages", [])
                      if not isinstance(messages, list):
                          continue

                      for msg in messages:
                          if getattr(msg, "type", None) == "tool":
                              with st.expander(
                                  f"✅ Tool result · `{msg.name}`  ({agent_label})",
                                  expanded=False
                              ):
                                  content_str = str(msg.content)
                                  st.write(content_str[:1800] + ("..." if len(content_str) > 1800 else ""))
                  else:
                      with st.expander(
                          f"⚙️ {agent_label} · {node_name}",
                          expanded=False
                      ):
                          if not isinstance(data, dict):
                              st.write(data)
                              continue

                          messages = data.get("messages")
                          if isinstance(messages, list):
                              for msg in messages:
                                  if hasattr(msg, "type") and hasattr(msg, "content"):
                                      content_preview = str(msg.content)[:700]
                                      st.write(f"**{msg.type.upper()}**: {content_preview}{'...' if len(str(msg.content)) > 700 else ''}")
                                  else:
                                      st.write(msg)
                          else:
                              st.write("State update:", messages)
    if ai_response:
        response_placeholder.write(ai_response)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})