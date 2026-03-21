import asyncio
import streamlit as st
from agent.deep_agent import Agents
import time
from datetime import timedelta
from models.settings import settings
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from utils.util import (
    fetch_supported_models,
    store_conversation_history,
    generate_session_id,
    load_all_sessions,
    load_all_sessions_uncached,
    delete_session,
)


def get_or_create_event_loop():
    """Get existing loop or create one — needed outside Streamlit's async context."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# Cache the agent initialization
@st.cache_resource(show_spinner="Initializing agent…")
def get_agent(model_name: str):
    loop = get_or_create_event_loop()
    agent_instance = loop.run_until_complete(Agents.create(model_name=model_name))
    return agent_instance.get_agent()


def enable_tracing():
    print("Called")
    langfuse_handler = None
    if settings.LANGFUSE_TRACING_ENABLED:
        langfuse = get_client()
        if langfuse.auth_check():
            print("Langfuse client is authenticated and ready!")
        else:
            print("Authentication failed. Please check your credentials and host.")
        langfuse_handler = CallbackHandler()
    return langfuse_handler


def initialize_session_state():
    """Initialize all session state variables"""
    if "supported_models" not in st.session_state:
        st.session_state.supported_models = fetch_supported_models()
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model_choice" not in st.session_state:
        st.session_state.model_choice = ""
    # Always load fresh session data to avoid caching issues
    st.session_state.sessions = load_all_sessions_uncached()


def handle_new_chat():
    """Handle creating a new chat session"""
    st.session_state.session_id = generate_session_id()
    st.session_state.messages = []
    store_conversation_history(st.session_state.session_id, [])
    # Refresh session data immediately after creating new chat
    load_all_sessions.clear()
    st.session_state.sessions = load_all_sessions_uncached()
    st.rerun()


def render_single_session(session_id, history):
    """Render a single chat session in the sidebar"""
    col1, col2 = st.columns([5, 1])
    with col1:
        label = history.get("title", "Untitled")
        button_type = (
            "primary" if session_id == st.session_state.session_id else "secondary"
        )
        if st.button(
            label, key=f"load_{session_id}", type=button_type, use_container_width=True
        ):
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
            # Refresh session data immediately after deletion
            load_all_sessions.clear()
            st.session_state.sessions = load_all_sessions_uncached()
            st.rerun()


def render_chat_history(sessions):
    """Render the chat history section"""
    if not sessions:
        st.caption("No past conversations yet.")
    else:
        for session_id in sessions.keys():
            history = sessions[session_id]
            if not history or not isinstance(history, dict):
                continue
            render_single_session(session_id, history)


def render_sidebar():
    """Render the sidebar with model selection and chat history"""
    with st.sidebar:
        st.header("💬 Chat")

        st.session_state.model_choice = st.selectbox(
            "Model",
            st.session_state.supported_models,
        )

        if st.button("➕ New Chat"):
            handle_new_chat()

        st.divider()
        st.subheader("🕑 Chat History")

        # Always use fresh session data to avoid caching issues
        # st.session_state.sessions = load_all_sessions_uncached()

        render_chat_history(st.session_state.sessions)


def display_chat_messages():
    """Display all chat messages in the UI"""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])


def process_tool_calls(msg, agent_label):
    """Process and display tool calls"""
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            tool_name = tc.get("name", "unknown")
            with st.expander(
                f"🔧 Tool call · {tool_name}  ({agent_label})",
                expanded=False,
            ):
                st.json(tc.get("args", {}))


def process_tool_results(messages, agent_label):
    """Process and display tool results"""
    for msg in messages:
        if getattr(msg, "type", None) == "tool":
            with st.expander(
                f"✅ Tool result · `{msg.name}`  ({agent_label})",
                expanded=False,
            ):
                content_str = str(msg.content)
                st.write(
                    content_str[:1800] + ("..." if len(content_str) > 1800 else "")
                )


def process_other_nodes(data, agent_label, node_name):
    """Process and display other node information"""
    with st.expander(f"⚙️ {agent_label} · {node_name}", expanded=False):
        if not isinstance(data, dict):
            st.write(data)
            return

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


async def handle_agent_streaming(agent, prompt, response_placeholder,langfuse_handler):
    """Handle the agent streaming response and update UI accordingly"""
    ai_response = ""
    total_input_tokens = 0
    total_output_tokens = 0

    with st.status("Thinking...", expanded=False) as status:
        # Stream the agent's response
        async for namespace, chunk in agent.astream(
            {"messages": [{"role": "user", "content": prompt}]},
            {
                "configurable": {
                    "thread_id": st.session_state.session_id,
                    "callbacks": [langfuse_handler],
                },
            },
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
                status.update(
                    label=f"{current_phase} → Calling model...", state="running"
                )
            elif "tools" in chunk:
                status.update(
                    label=f"{current_phase} → Executing tools...", state="running"
                )
            elif namespace:
                status.update(
                    label=f"Sub-agent {namespace[0]} in progress...", state="running"
                )

            for node_name, data in chunk.items():
                if node_name == "model":
                    if not isinstance(data, dict):
                        continue

                    messages = data.get("messages", [])
                    if not messages:
                        continue
                    msg = messages[-1]
                    process_tool_calls(msg, agent_label)

                    usage = getattr(msg, "usage_metadata", None)
                    if usage:
                        total_input_tokens += usage.get("input_tokens", 0)
                        total_output_tokens += usage.get("output_tokens", 0)

                    if not namespace and msg.content:
                        ai_response = msg.content
                        response_placeholder.write(ai_response)
                elif node_name == "tools":
                    if not isinstance(data, dict):
                        continue
                    messages = data.get("messages", [])
                    if not isinstance(messages, list):
                        continue

                    process_tool_results(messages, agent_label)
                else:
                    process_other_nodes(data, agent_label, node_name)
        status.update(label="Thinking Complete", state="complete")

    return ai_response, total_input_tokens, total_output_tokens


def main() -> None:
    st.set_page_config(page_title="Chat", page_icon="💬")
    st.title("💬 Chat")
    initialize_session_state()
    render_sidebar()
    langfuse_handler=enable_tracing()
    # Display chat messages
    display_chat_messages()

    # Handle user input
    if prompt := st.chat_input("Say something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        agent = get_agent(st.session_state.model_choice)
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            start_time = time.perf_counter()
            # Handle agent streaming response
            loop = get_or_create_event_loop()
            ai_response, total_input, total_output = loop.run_until_complete(
                handle_agent_streaming(agent, prompt, response_placeholder,langfuse_handler)
            )

            if ai_response:
                elapsed = time.perf_counter() - start_time
                elapsed_str = (
                    f"{timedelta(seconds=int(elapsed))}"
                    if elapsed >= 60
                    else f"{elapsed:.1f}s"
                )
                total_tokens = total_input + total_output

                stats_html = f"""
                <div style="
                    display: flex;
                    gap: 10px;
                    margin-top: 12px;
                    flex-wrap: wrap;
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 8px;
                        padding: 5px 12px;
                        font-size: 12px;
                        color: #a0a0b0;
                        font-family: monospace;
                    ">
                        ⏱️ <span style="color:#e0e0f0; font-weight:600;">{elapsed_str}</span>
                    </div>
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 8px;
                        padding: 5px 12px;
                        font-size: 12px;
                        color: #a0a0b0;
                        font-family: monospace;
                    ">
                        🔢 <span style="color:#e0e0f0; font-weight:600;">{total_tokens:,}</span> total
                    </div>
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        background: rgba(99,202,183,0.08);
                        border: 1px solid rgba(99,202,183,0.2);
                        border-radius: 8px;
                        padding: 5px 12px;
                        font-size: 12px;
                        color: #a0a0b0;
                        font-family: monospace;
                    ">
                        ↑ <span style="color:#63cab7; font-weight:600;">{total_input:,}</span> in
                    </div>
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        background: rgba(180,130,255,0.08);
                        border: 1px solid rgba(180,130,255,0.2);
                        border-radius: 8px;
                        padding: 5px 12px;
                        font-size: 12px;
                        color: #a0a0b0;
                        font-family: monospace;
                    ">
                        ↓ <span style="color:#b482ff; font-weight:600;">{total_output:,}</span> out
                    </div>
                </div>
                """

                response_placeholder.write(ai_response)
                st.markdown(stats_html, unsafe_allow_html=True)

            st.session_state.messages.append(
                {"role": "assistant", "content": ai_response}
            )
            store_conversation_history(
                st.session_state.session_id, st.session_state.messages
            )
            # Refresh session data immediately after storing
            load_all_sessions.clear()
            st.session_state.sessions = load_all_sessions_uncached()
        # st.rerun()


if __name__ == "__main__":
    main()
