import streamlit as st

from chatbot.presentation.streamlit.bilingual import BilingualTextRenderer


class EmptyStateComponent:
    """Renders the center-column empty state with watermark and inquiry grid."""

    WATERMARK_TEXT = "ALTIBBI"
    SUBTITLE = "Clinical intelligence terminal — select an inquiry or begin a new session."

    INQUIRIES = [
        "What are the primary symptoms and diagnostic criteria for Type 2 diabetes?",
        "Explain first-line hypertension treatment protocols and monitoring guidelines.",
        "What drug interactions should be checked before prescribing warfarin?",
        "ما هي أعراض نقص فيتامين د وكيف يتم تشخيصه؟",
        "Summarize contraindications for ACE inhibitors in renal impairment.",
        "How should acute migraine episodes be managed in outpatient settings?",
    ]

    def render(self) -> None:
        st.markdown(
            f"""
            <div class="center-column">
                <div class="empty-state-watermark">{self.WATERMARK_TEXT}</div>
                <div class="empty-state-subtitle">{self.SUBTITLE}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-family:IBM Plex Mono,monospace;font-size:0.68rem;'
            'letter-spacing:0.14em;text-transform:uppercase;color:#475569;'
            'margin-bottom:0.75rem;">Suggested Medical Inquiries</p>'
            '<div class="inquiry-grid">',
            unsafe_allow_html=True,
        )

        for row_start in range(0, len(self.INQUIRIES), 3):
            row_items = self.INQUIRIES[row_start : row_start + 3]
            cols = st.columns(3, gap="small")
            for col_index, inquiry in enumerate(row_items):
                with cols[col_index]:
                    self._render_inquiry_card(inquiry, row_start + col_index)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_inquiry_card(self, inquiry: str, index: int) -> None:
        preview = BilingualTextRenderer.truncate_preview(inquiry, 55)
        if st.button(preview, key=f"inquiry_{index}", use_container_width=True):
            st.session_state.pending_action = inquiry
            st.rerun()
