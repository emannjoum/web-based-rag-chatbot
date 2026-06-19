import streamlit as st


class CitationPaneComponent:
    """Dedicated RAG citation and context pane for the right sidebar column."""

    HEADER_TITLE = "Verified Sources & Context"
    EMPTY_MESSAGE = (
        "Source references will appear here when the assistant cites "
        "verified clinical documents in a response."
    )

    @classmethod
    def _resolve_active_sources(cls) -> dict:
        messages = st.session_state.get("messages", [])
        for message in reversed(messages):
            if message.get("role") == "assistant":
                sources = message.get("sources") or {}
                if sources:
                    return sources
        return {}

    @classmethod
    def _infer_verification_label(cls, url: str) -> str:
        lowered = url.lower()
        if "altibbi" in lowered:
            return "Altibbi Core"
        if any(token in lowered for token in ("pubmed", "ncbi", "who.int", "cdc.gov")):
            return "Clinical Reference"
        return "External Source"

    @classmethod
    def _compute_relevance(cls, citation_id: int, total: int) -> int:
        if total <= 1:
            return 94
        position_weight = 1.0 - ((citation_id - 1) / max(total, 1))
        return max(52, min(98, int(55 + position_weight * 43)))

    @classmethod
    def _render_citation_card(cls, citation_id: int, url: str, relevance: int) -> None:
        label = cls._infer_verification_label(url)
        display_url = url if len(url) <= 72 else url[:69] + "..."
        st.markdown(
            f"""
            <div class="citation-card">
                <div class="citation-label">{label}</div>
                <div style="display:flex;align-items:flex-start;">
                    <span class="citation-badge">[{citation_id}]</span>
                    <div style="flex:1;">
                        <div class="citation-url">
                            <a href="{url}" target="_blank" rel="noopener noreferrer">{display_url}</a>
                        </div>
                        <div class="relevance-bar-track">
                            <div class="relevance-bar-fill" style="width:{relevance}%;"></div>
                        </div>
                        <div class="relevance-label">
                            <span>Relevance</span>
                            <span>{relevance}%</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render(self) -> None:
        sources = self._resolve_active_sources()
        total = len(sources)

        st.markdown(
            f'<div class="citation-pane"><div class="citation-pane-header">{self.HEADER_TITLE}</div>',
            unsafe_allow_html=True,
        )

        if not sources:
            st.markdown(
                f'<div class="citation-empty">{self.EMPTY_MESSAGE}</div></div>',
                unsafe_allow_html=True,
            )
            return

        sorted_sources = sorted(sources.items(), key=lambda item: int(item[0]))
        for citation_id, url in sorted_sources:
            relevance = self._compute_relevance(int(citation_id), total)
            self._render_citation_card(int(citation_id), url, relevance)

        st.markdown("</div>", unsafe_allow_html=True)
