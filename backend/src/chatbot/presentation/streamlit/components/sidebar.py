from typing import Any

import streamlit as st

from chatbot.domain.ports.repository_port import ChatRepositoryPort


class SidebarComponent:
    MODEL_OPTIONS = ["GPT-4o mini", "Gemini 2.5 Flash Lite"]
    SEARCH_OPTIONS = ["Serper", "Tavily", "Manual Scraping"]

    def __init__(self, repository: ChatRepositoryPort, user_id: int) -> None:
        self._repository = repository
        self._user_id = user_id

    def render(self) -> tuple[str, str]:
        with st.sidebar:
            st.title("Settings")
            selected_model = st.radio("Used Model:", self.MODEL_OPTIONS)
            search_method = st.selectbox("Context Retrieval Method:", self.SEARCH_OPTIONS)

            if st.button("New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_chat_id = None
                st.rerun()

            st.divider()
            self._render_history()

        return selected_model, search_method

    def _render_history(self) -> None:
        st.subheader("Recent History")
        for chat in self._repository.get_all_history(self._user_id, limit=15) or []:
            chat_label = chat.get("chat_title") or chat.get("last_preview", "Empty Chat")[:25] + "..."
            col1, col2 = st.columns([0.8, 0.15])

            if col1.button(chat_label, key=f"load_{chat['_id']}", use_container_width=True):
                st.session_state.messages = self._repository.get_chat_by_id(str(chat["_id"]), self._user_id) or []
                st.session_state.current_chat_id = str(chat["_id"])
                st.rerun()

            with col2.popover("⋮"):
                if st.button("Delete", key=f"del_{chat['_id']}", type="primary"):
                    self._repository.delete_chat(str(chat["_id"]), self._user_id)
                    if st.session_state.current_chat_id == str(chat["_id"]):
                        st.session_state.messages = []
                        st.session_state.current_chat_id = None
                    st.rerun()
