import streamlit as st

from chatbot.presentation.streamlit.bilingual import BilingualTextRenderer
from chatbot.presentation.streamlit.components.empty_state import EmptyStateComponent
from chatbot.presentation.streamlit.components.quick_actions import QuickActionsComponent


class ChatViewComponent:
    """Center-column chat interface: empty state, message threads, and quick actions."""

    def __init__(self) -> None:
        self._empty_state = EmptyStateComponent()
        self._quick_actions = QuickActionsComponent()

    def render(self, selected_model: str) -> None:
        self._render_top_nav(selected_model)
        messages = st.session_state.messages

        if not messages:
            self._empty_state.render()
            return

        st.markdown('<div class="center-column">', unsafe_allow_html=True)
        for idx, message in enumerate(messages):
            self._render_message(message, idx, len(messages))
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_top_nav(self, selected_model: str) -> None:
        st.markdown(
            f"""
            <div class="top-nav-bar">
                <span class="top-nav-title">Active Session</span>
                <span class="model-pill-active">{selected_model}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_message(self, message: dict, index: int, total: int) -> None:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        sources = message.get("sources") or {}
        avatar = "user" if role == "user" else "assistant"

        with st.chat_message(avatar):
            BilingualTextRenderer.render_chat_content(content, sources, role)
            if role == "assistant":
                self._quick_actions.render_for_message(message, index, total)

    def render_user_message(self, content: str) -> None:
        with st.chat_message("user"):
            BilingualTextRenderer.render_chat_content(content, {}, "user")

    def render_assistant_message(self, content: str, sources: dict | None = None) -> None:
        with st.chat_message("assistant"):
            BilingualTextRenderer.render_chat_content(content, sources or {}, "assistant")
