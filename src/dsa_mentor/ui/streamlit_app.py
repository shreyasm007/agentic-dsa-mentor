import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from dsa_mentor.bootstrap import build_orchestrator
from dsa_mentor.domain.models import CodingProblem, MentorMode
from dsa_mentor.infrastructure.config import get_settings


@st.cache_resource
def _graph():
    return build_orchestrator()


def run() -> None:
    settings = get_settings()
    st.set_page_config(page_title="Agentic DSA Mentor", page_icon="🥋", layout="wide")
    st.title("Agentic DSA Mentor")
    st.caption("Paste a LeetCode URL, say “LeetCode 3”, or paste the complete problem.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "problem" not in st.session_state:
        st.session_state.problem = None

    with st.sidebar:
        mode = st.selectbox("Mentor mode", [item.value for item in MentorMode])
        default_index = (
            settings.groq_models.index(settings.default_groq_model)
            if settings.default_groq_model in settings.groq_models
            else 0
        )
        model_id = st.selectbox("Groq model", settings.groq_models, index=default_index)
        if st.session_state.problem:
            problem = CodingProblem.model_validate(st.session_state.problem)
            st.subheader("Resolved problem")
            st.write(f"**{problem.frontend_id or ''} {problem.title}**")
            st.write(problem.difficulty or "Difficulty unknown")
            st.write(", ".join(problem.topics))
            if problem.url:
                st.link_button("Open on LeetCode", problem.url)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Try: Give me a hint for LeetCode 3"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        graph_messages = [
            HumanMessage(content=item["content"])
            if item["role"] == "user"
            else AIMessage(content=item["content"])
            for item in st.session_state.messages
        ]
        with st.chat_message("assistant"):
            with st.spinner("Resolving problem and consulting a specialist..."):
                result = _graph().invoke(
                    {
                        "messages": graph_messages,
                        "selected_mode": mode,
                        "model_id": model_id,
                        "problem": st.session_state.problem,
                    }
                )
                response = result["response"]
                st.markdown(response)
                st.caption(
                    f"Agent: {result['route'].value.replace('_', ' ').title()} · Model: {model_id}"
                )

        st.session_state.problem = result.get("problem")
        st.session_state.messages.append({"role": "assistant", "content": response})
