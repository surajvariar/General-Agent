import streamlit as st
from agent.deep_agent import Agents
from utils.util import fetch_supported_models, store_conversation_history,generate_session_id,load_all_sessions,delete_session

@st.cache_resource(show_spinner="Initializing agent…")
def get_agent(model_name: str):
    agent_instance = Agents(model_name=model_name)
    return agent_instance.get_agent()

st.set_page_config(page_title="Chat", page_icon="💬")
st.title("💬 Chat")

if "supported_models" not in st.session_state:
    st.session_state.supported_models = fetch_supported_models()
if "session_id" not in st.session_state:
    st.session_state.session_id=generate_session_id()
if "sessions" not in st.session_state:
    st.session_state.sessions=load_all_sessions()

if "messages" not in st.session_state:
    st.session_state.messages = []


if "model_choice" not in st.session_state:
    st.session_state.model_choice =""

with st.sidebar:
    st.session_state.model_choice = st.selectbox(
        "Model",
        st.session_state.supported_models,
    )
    if st.button("➕ New Chat"):
        st.session_state.session_id = generate_session_id()
        st.session_state.messages = []
        store_conversation_history(st.session_state.session_id,[])
        load_all_sessions.clear()
        st.rerun()

    st.divider()
    st.subheader("🕑 Chat History")
    load_all_sessions.clear()
    sessions = load_all_sessions()
    st.session_state.sessions = sessions
    if not sessions:
        st.caption("No past conversations yet.")
    else:
        for session_id in sessions.keys():
            col1,col2=st.columns([5,1])
            with col1:
                history = sessions[session_id]
                if not history or not isinstance(history, dict):
                    continue
                label=history.get("title","Untitled")
                button_type = "primary" if session_id == st.session_state.session_id else "secondary"
                if st.button(label, key=f"load_{session_id}", type=button_type, use_container_width=True):
                    st.session_state.session_id = session_id
                    st.session_state.messages = history.get("messages")
                    st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{session_id}"):
                    delete_session(session_id)
                    # If deleting the active session, start fresh
                    if session_id == st.session_state.session_id:
                        st.session_state.session_id = generate_session_id()
                        st.session_state.messages = []
                        # load_all_sessions.clear()
                    st.rerun() 

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    agent = get_agent(st.session_state.model_choice)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        ai_response = ""

    with st.status("Thinking...",expanded=False) as status:
        for namespace, chunk in agent.stream(
            {"messages": [{"role": "user", "content": prompt}]},
            { "configurable": { "thread_id": st.session_state.session_id } },
            stream_mode="updates",
            subgraphs=True,
        ):

            if not namespace:
                agent_label = "Main agent"
                current_phase = "Main reasoning"
            else:
                agent_label = f"Sub-agent {namespace[0]}"
                current_phase = f"{agent_label} working"
            
            if "model" in chunk:
                status.update(label=f"{current_phase} → Calling model...",state="running")
            elif "tools" in chunk:
                status.update(label=f"{current_phase} → Executing tools...",state="running")
            elif namespace:
                status.update(label=f"Sub-agent {namespace[0]} in progress...",state="running")

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
                                expanded=False,
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
                                expanded=False,
                            ):
                                content_str = str(msg.content)
                                st.write(
                                    content_str[:1800]
                                    + ("..." if len(content_str) > 1800 else "")
                                )
                else:
                    with st.expander(f"⚙️ {agent_label} · {node_name}", expanded=False):
                        if not isinstance(data, dict):
                            st.write(data)
                            continue

                        messages = data.get("messages")
                        if isinstance(messages, list):
                            for msg in messages:
                                if hasattr(msg, "type") and hasattr(msg, "content"):
                                    content_preview = str(msg.content)[:700]
                                    st.write(
                                        f"**{msg.type.upper()}**: {content_preview}{'...' if len(str(msg.content)) > 700 else ''}"
                                    )
                                else:
                                    st.write(msg)
                        else:
                            st.write("State update:", messages)
        status.update(label="Thinking Complete",state="complete")
    if ai_response:
        response_placeholder.write(ai_response)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    store_conversation_history(st.session_state.session_id,st.session_state.messages)
    load_all_sessions.clear()
    st.session_state.sessions=load_all_sessions()