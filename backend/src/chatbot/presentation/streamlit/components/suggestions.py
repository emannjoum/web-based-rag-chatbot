from typing import Any

import streamlit as st


class SuggestionsComponent:
    def render_for_message(self, message: dict[str, Any], index: int, total_messages: int) -> None:
        if message["role"] != "assistant" or index != total_messages - 1:
            return
        suggestions = message.get("suggestions")
        if not suggestions:
            return

        cols = st.columns(len(suggestions))
        for suggestion_index, suggestion in enumerate(suggestions):
            unique_key = f"sugg_btn_{index}_{hash(suggestion + str(suggestion_index))}"
            if cols[suggestion_index].button(suggestion, key=unique_key, use_container_width=True):
                st.session_state.pending_action = suggestion
                st.rerun()
