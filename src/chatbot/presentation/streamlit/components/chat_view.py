import streamlit as st

from chatbot.presentation.streamlit.components.suggestions import SuggestionsComponent
from chatbot.shared.link_formatter import LinkFormatter


class ChatViewComponent:
    def __init__(self) -> None:
        self._suggestions = SuggestionsComponent()

    def render(self) -> None:
        st.title("MedAtlas Chatbot")
        messages = st.session_state.messages

        for idx, message in enumerate(messages):
            with st.chat_message(message["role"]):
                st.markdown(
                    LinkFormatter.make_clickable(message["content"], message.get("sources", {}))
                )
                self._render_sources(message.get("sources", {}))
                self._suggestions.render_for_message(message, idx, len(messages))

    def render_user_message(self, content: str) -> None:
        st.chat_message("user").markdown(content)

    def render_assistant_message(self, content: str, sources: dict | None = None) -> None:
        with st.chat_message("assistant"):
            st.markdown(LinkFormatter.make_clickable(content, sources or {}))
            if sources:
                with st.expander("View Sources"):
                    for sid, link in sources.items():
                        st.write(f"[{sid}] {link}")

    @staticmethod
    def _render_sources(sources: dict) -> None:
        if not sources:
            return
        with st.expander("Sources", expanded=False):
            for sid, link in sources.items():
                st.markdown(f"- [{sid}] {link}")
