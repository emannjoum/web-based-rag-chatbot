import datetime
from typing import Any

import streamlit as st

from chatbot.domain.ports.repository_port import ChatRepositoryPort
from chatbot.presentation.streamlit.bilingual import BilingualTextRenderer


class SidebarComponent:
    """Left navigation column: new chat, timeline-grouped history, and system footer."""

    MODEL_OPTIONS = ["GPT-4o mini", "Gemini 2.5 Flash Lite"]
    SEARCH_OPTIONS = ["Serper", "Tavily", "Manual Scraping"]

    def __init__(self, repository: ChatRepositoryPort) -> None:
        self._repository = repository

    def render(self) -> tuple[str, str]:
        with st.sidebar:
            st.markdown(
                """
                <div class="sidebar-brand">Clinical Terminal</div>
                <div class="sidebar-title">Altibbi Medical AI</div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
            if st.button("+ New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_chat_id = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            self._render_history()

            st.markdown(
                '<div class="timeline-header" style="margin-top:1.5rem;">Configuration</div>',
                unsafe_allow_html=True,
            )
            selected_model = st.radio("Inference Model", self.MODEL_OPTIONS)
            search_method = st.selectbox("Retrieval Pipeline", self.SEARCH_OPTIONS)

            self._render_footer(selected_model, search_method)

        return selected_model, search_method

    def _render_history(self) -> None:
        chats = self._repository.get_all_history(limit=15) or []
        grouped = self._group_by_timeline(chats)

        for group_label, group_chats in grouped.items():
            if not group_chats:
                continue
            st.markdown(f'<div class="timeline-header">{group_label}</div>', unsafe_allow_html=True)
            for chat in group_chats:
                self._render_history_item(chat)

    def _render_history_item(self, chat: dict[str, Any]) -> None:
        raw_label = chat.get("chat_title") or chat.get("last_preview", "Empty Chat")
        chat_label = BilingualTextRenderer.truncate_preview(str(raw_label), 32)
        chat_id = str(chat["_id"])

        col1, col2 = st.columns([0.82, 0.12])
        with col1:
            if st.button(chat_label, key=f"load_{chat_id}", use_container_width=True):
                st.session_state.messages = self._repository.get_chat_by_id(chat_id) or []
                st.session_state.current_chat_id = chat_id
                st.rerun()

        with col2.popover("..."):
            if st.button("Delete", key=f"del_{chat_id}", type="primary"):
                self._repository.delete_chat(chat_id)
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.messages = []
                    st.session_state.current_chat_id = None
                st.rerun()

    def _group_by_timeline(self, chats: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        now = datetime.datetime.now(datetime.timezone.utc)
        groups: dict[str, list[dict[str, Any]]] = {
            "YESTERDAY": [],
            "LAST WEEK": [],
            "LAST MONTH": [],
            "OLDER": [],
        }

        for chat in chats:
            last_active = chat.get("last_active")
            if not isinstance(last_active, datetime.datetime):
                groups["OLDER"].append(chat)
                continue

            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=datetime.timezone.utc)

            delta = now - last_active
            if delta.days < 1:
                groups["YESTERDAY"].append(chat)
            elif delta.days < 7:
                groups["LAST WEEK"].append(chat)
            elif delta.days < 30:
                groups["LAST MONTH"].append(chat)
            else:
                groups["OLDER"].append(chat)

        return groups

    def _render_footer(self, selected_model: str, search_method: str) -> None:
        st.markdown(
            f"""
            <div class="sidebar-footer">
                <div style="display:flex;align-items:center;margin-bottom:0.4rem;">
                    <span class="status-dot"></span>
                    <span class="status-text">System Online</span>
                </div>
                <div class="status-text" style="margin-bottom:0.2rem;">
                    Model: {selected_model}
                </div>
                <div class="status-text">Pipeline: {search_method}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
