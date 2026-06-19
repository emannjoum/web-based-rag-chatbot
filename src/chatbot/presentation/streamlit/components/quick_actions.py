from typing import Any

import streamlit as st


class QuickActionsComponent:
    """Minimalist action pills displayed below the latest assistant response."""

    DEFAULT_ACTIONS = [
        "Simplify Clinical Terms",
        "Check Drug Interactions",
        "Show Evaluation Metrics",
    ]

    def render_for_message(self, message: dict[str, Any], index: int, total_messages: int) -> None:
        if message.get("role") != "assistant" or index != total_messages - 1:
            return

        actions = list(self.DEFAULT_ACTIONS)
        pipeline_suggestions = message.get("suggestions") or []
        for suggestion in pipeline_suggestions[:2]:
            if suggestion not in actions:
                actions.append(suggestion)

        st.markdown('<div class="quick-actions-row">', unsafe_allow_html=True)
        cols = st.columns(len(actions))
        for action_index, action in enumerate(actions):
            with cols[action_index]:
                st.markdown('<div class="action-pill">', unsafe_allow_html=True)
                unique_key = f"quick_action_{index}_{action_index}_{hash(action)}"
                if st.button(action, key=unique_key, use_container_width=True):
                    st.session_state.pending_action = action
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
