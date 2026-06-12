import base64
import html
import re
import uuid
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from dsa_mentor.bootstrap import build_orchestrator
from dsa_mentor.domain.models import CodingProblem, MentorMode
from dsa_mentor.infrastructure import db
from dsa_mentor.infrastructure.config import get_settings
from dsa_mentor.application.orchestrator import SPECIALIST_MODES


@st.cache_resource
def _graph():
    return build_orchestrator()


def display_message_content(content: str):
    # Search for mermaid code blocks: ```mermaid ... ```
    pattern = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
    parts = pattern.split(content)

    for i, part in enumerate(parts):
        if not part.strip():
            continue
        if i % 2 == 1:
            # Mermaid code block found, render inside an interactive HTML component
            escaped_code = html.escape(part.strip())
            html_content = f"""
            <div style="background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin: 15px 0; display: flex; flex-direction: column; align-items: center;">
                <div class="mermaid" style="width: 100%; display: flex; justify-content: center; overflow: auto;">
                {escaped_code}
                </div>
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
            </script>
            """
            st.components.v1.html(html_content, height=450, scrolling=True)
        else:
            st.markdown(part)


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Modern ChatGPT-like Dark Theme & Layout */
        .stApp {
            background-color: #1e1f25;
            color: #ececf1;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        
        /* Sidebar layout */
        [data-testid="stSidebar"] {
            background-color: #0d0e12 !important;
            border-right: 1px solid #2d2e38;
        }
        
        /* Compact styled paperclip file uploader */
        [data-testid="stFileUploader"] {
            padding: 0 !important;
            margin: 0 !important;
            width: auto !important;
        }
        [data-testid="stFileUploader"] section {
            padding: 0px !important;
            min-height: 44px !important;
            height: 44px !important;
            width: 44px !important;
            border: 1px solid #3e3f4b !important;
            border-radius: 22px !important;
            background-color: #2e2f38 !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease-in-out;
        }
        [data-testid="stFileUploader"] section:hover {
            border-color: #5865F2 !important;
            background-color: #383944 !important;
        }
        [data-testid="stFileUploader"] section > div {
            display: none !important;
        }
        [data-testid="stFileUploader"] section::after {
            content: "📎" !important;
            font-size: 20px !important;
            color: #c5c5d2 !important;
        }

        /* Expander / Logs persistence card */
        .stExpander {
            background-color: #17181f !important;
            border: 1px solid #2d2e38 !important;
            border-radius: 8px !important;
            margin: 8px 0;
        }
        
        /* Premium title styling */
        .premium-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #5865F2, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            text-align: center;
        }

        /* Buttons style */
        .stButton>button {
            border-radius: 6px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        /* Alignment fixes */
        .chat-input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(180deg, rgba(30,31,37,0) 0%, rgba(30,31,37,1) 30%);
            padding: 20px 0;
            z-index: 100;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def run() -> None:
    # Initialize DB tables
    db.init_db()

    # Load general settings
    settings = get_settings()

    st.set_page_config(page_title="Agentic DSA Mentor", page_icon="🥋", layout="wide")
    inject_custom_css()

    # Manage session state variables
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "problem" not in st.session_state:
        st.session_state.problem = None
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # 1. Authentication Layer (If not logged in)
    if not st.session_state.current_user:
        st.markdown("<h1 class='premium-title'>🥋 Agentic DSA Mentor</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align: center; color: #8a8d98; font-size: 1.1rem;'>Your personalized, interactive AI-powered Data Structures & Algorithms learning assistant</p>",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 1.8, 1])
        with col2:
            tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])

            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username").strip()
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("Sign In", use_container_width=True)
                    if submit:
                        if db.verify_user(username, password):
                            st.session_state.current_user = username.lower()
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                            st.session_state.problem = None
                            st.success("Successfully logged in!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

            with tab2:
                with st.form("signup_form"):
                    new_username = st.text_input("New Username").strip()
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    submit = st.form_submit_button("Create Account", use_container_width=True)
                    if submit:
                        if not new_username or not new_password:
                            st.error("Username and password cannot be empty.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            if db.create_user(new_username, new_password):
                                st.success("Account created successfully! Please Sign In.")
                            else:
                                st.error("Username already exists.")
        return

    # 2. Main Interface (Logged-In User)
    username_display = st.session_state.current_user.capitalize()

    # Sidebar: Session management, Configuration, Resolved Problem
    with st.sidebar:
        st.markdown(f"### Welcome, **{username_display}**! 👋")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state.current_chat_id = None
            st.session_state.messages = []
            st.session_state.problem = None
            st.rerun()

        st.markdown("---")

        # Previous Chat List
        st.markdown("#### Previous Chats")
        chats = db.load_chats(st.session_state.current_user)
        if not chats:
            st.caption("No previous chats. Start one below!")
        else:
            for ch in chats:
                col_btn, col_del = st.columns([0.82, 0.18])
                is_active = st.session_state.current_chat_id == ch["id"]
                btn_label = f"💬 {ch['title'][:18]}..." if len(ch["title"]) > 18 else f"💬 {ch['title']}"
                if is_active:
                    btn_label = f"⭐ {ch['title'][:18]}..." if len(ch["title"]) > 18 else f"⭐ {ch['title']}"

                if col_btn.button(
                    btn_label,
                    key=f"load_{ch['id']}",
                    use_container_width=True,
                    type="secondary" if not is_active else "primary",
                ):
                    st.session_state.current_chat_id = ch["id"]
                    st.session_state.messages = ch["messages"]
                    st.session_state.problem = ch["problem"]
                    st.rerun()

                if col_del.button("🗑️", key=f"del_{ch['id']}", use_container_width=True):
                    db.delete_chat(ch["id"], st.session_state.current_user)
                    if st.session_state.current_chat_id == ch["id"]:
                        st.session_state.current_chat_id = None
                        st.session_state.messages = []
                        st.session_state.problem = None
                    st.rerun()

        st.markdown("---")

        # Configuration options
        st.markdown("#### Mentor & LLM Settings")
        mode = st.selectbox("Mentor mode", [item.value for item in MentorMode])
        default_index = (
            settings.groq_models.index(settings.default_groq_model)
            if settings.default_groq_model in settings.groq_models
            else 0
        )
        model_id = st.selectbox("Groq model", settings.groq_models, index=default_index)

        # Problem Info Card
        if st.session_state.problem:
            problem = CodingProblem.model_validate(st.session_state.problem)
            st.markdown("---")
            st.subheader("Resolved Problem")
            st.write(f"**{problem.frontend_id or ''} {problem.title}**")
            st.write(problem.difficulty or "Difficulty unknown")
            st.write(", ".join(problem.topics))
            if problem.url:
                st.link_button("Open on LeetCode", problem.url)

        # Logout at the bottom
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.current_chat_id = None
            st.session_state.messages = []
            st.session_state.problem = None
            st.rerun()

    # Main Chat Area (ChatGPT Centered Style)
    st.markdown("<h1 class='premium-title'>🥋 Agentic DSA Mentor</h1>", unsafe_allow_html=True)

    # Render current conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image_base64" in message and message["image_base64"]:
                img_data = base64.b64decode(message["image_base64"])
                st.image(img_data, width=350, caption="Uploaded Image Context")
            
            # Display text & diagrams/images
            display_message_content(message["content"])

            # Persistent dropdown/expander for past thinking process logs
            if message["role"] == "assistant":
                if "logs" in message and message["logs"]:
                    with st.expander("💭 Agent Execution Trace / Thinking Process", expanded=False):
                        st.markdown("\n".join(message["logs"]))
                
                # Active agent details
                agent_name = message.get("agent", "tutor")
                st.markdown(
                    f"<div style='margin-top: 5px; font-size: 0.85rem; color: #5865F2; font-weight: 600;'>"
                    f"🤖 Specialist: {agent_name.replace('_', ' ').title()}</div>",
                    unsafe_allow_html=True
                )

    # Image upload preview block if file selected
    image_preview_placeholder = st.empty()

    # User Input Panel at the bottom (Upload button on LHS of chat input)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col_file, col_input = st.columns([0.06, 0.94], gap="small")
    with col_file:
        uploaded_file = st.file_uploader(
            "Upload",
            type=["png", "jpg", "jpeg"],
            key=f"uploader_{st.session_state.uploader_key}",
            label_visibility="collapsed",
        )
    with col_input:
        prompt = st.chat_input("Ask a question, paste LeetCode URL, or get a hint...")

    if uploaded_file:
        with image_preview_placeholder:
            st.image(uploaded_file, caption="Selected Image Context (will be sent on Submit)", width=200)

    # Action on Send
    if prompt:
        image_base64 = None
        image_mime = None

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(file_bytes).decode("utf-8")
            image_mime = uploaded_file.type

        # Add user message to session state
        user_msg = {"role": "user", "content": prompt}
        if image_base64:
            user_msg["image_base64"] = image_base64
            user_msg["image_mime"] = image_mime

        st.session_state.messages.append(user_msg)
        st.rerun()

    # Generate Response if last message is from user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # Format list of messages for LangGraph input
        graph_messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                if msg.get("image_base64"):
                    content = [
                        {"type": "text", "text": msg["content"]},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{msg['image_mime']};base64,{msg['image_base64']}"
                            },
                        },
                    ]
                    graph_messages.append(HumanMessage(content=content))
                else:
                    graph_messages.append(HumanMessage(content=msg["content"]))
            else:
                graph_messages.append(AIMessage(content=msg["content"]))

        with st.chat_message("assistant"):
            # Execution Trace Log Container
            thinking_expander = st.expander("💭 Agent Execution Trace / Thinking Process", expanded=True)
            with thinking_expander:
                log_placeholder = st.empty()
                logs = ["⚡ Compiling orchestrator graph..."]
                log_placeholder.markdown("\n".join(logs))

            response_placeholder = st.empty()

            try:
                response_content = ""
                route_value = "auto"

                # Stream the execution of nodes in LangGraph
                for event in _graph().stream(
                    {
                        "messages": graph_messages,
                        "selected_mode": mode,
                        "model_id": model_id,
                        "problem": st.session_state.problem,
                    },
                    stream_mode="updates",
                ):
                    for node_name, output in event.items():
                        if node_name == "resolve_problem":
                            prob = output.get("problem") if output else None
                            if prob:
                                st.session_state.problem = prob
                                logs.append(f"🔍 **Problem Resolver**: Resolved problem *{prob.get('title')}*.")
                            else:
                                logs.append("🔍 **Problem Resolver**: No coding problem matching LeetCode references.")
                        elif node_name == "route":
                            route_val = output.get("route") if output else None
                            if route_val:
                                route_value = route_val
                                logs.append(
                                    f"🔀 **Orchestrator Router**: Determined Mentor Mode as *{getattr(route_val, 'value', route_val).replace('_', ' ').title()}*."
                                )
                        elif node_name == "retrieve":
                            ctx = output.get("context", "") if output else ""
                            if ctx:
                                logs.append("📚 **Knowledge Retrieval**: Pulled relevant patterns from Qdrant vector DB.")
                            else:
                                logs.append("📚 **Knowledge Retrieval**: No additional patterns retrieved.")
                        elif node_name in [m.value for m in SPECIALIST_MODES]:
                            logs.append(
                                f"🤖 **Specialist Agent ({node_name.replace('_', ' ').title()})**: Running LLM inference with system prompt..."
                            )
                            response_content = output.get("response", "") if output else ""

                        log_placeholder.markdown("\n".join(logs))

                # Display the response using parsed custom component
                with response_placeholder:
                    display_message_content(response_content)
                    agent_name_str = getattr(route_value, "value", route_value)
                    st.markdown(
                        f"<div style='margin-top: 5px; font-size: 0.85rem; color: #5865F2; font-weight: 600;'>"
                        f"🤖 Specialist: {agent_name_str.replace('_', ' ').title()}</div>",
                        unsafe_allow_html=True
                    )

                # Save assistant response along with thinking logs and answering agent badge
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content,
                    "logs": list(logs),
                    "agent": agent_name_str
                })

                # Persist the conversation to the DB
                if not st.session_state.current_chat_id:
                    st.session_state.current_chat_id = str(uuid.uuid4())
                    first_user_msg = next(
                        (m["content"] for m in st.session_state.messages if m["role"] == "user"), "New Chat"
                    )
                    title = first_user_msg[:25] + "..." if len(first_user_msg) > 25 else first_user_msg
                else:
                    user_chats = db.load_chats(st.session_state.current_user)
                    active_chat = next((c for c in user_chats if c["id"] == st.session_state.current_chat_id), None)
                    title = active_chat["title"] if active_chat else "New Chat"

                db.save_chat(
                    chat_id=st.session_state.current_chat_id,
                    username=st.session_state.current_user,
                    title=title,
                    messages=st.session_state.messages,
                    problem=st.session_state.problem,
                    selected_mode=mode,
                    model_id=model_id,
                )

                # Reset file uploader input
                st.session_state.uploader_key += 1
                st.rerun()

            except Exception as e:
                st.error(f"Failed to process message: {e}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": "Sorry, I had an issue handling that request."}
                )
