import logging
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[3]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import streamlit as st

from chatbot.application.chat_service import ChatService
from chatbot.application.dependencies import DependencyContainer
from chatbot.domain.exceptions import SearchError
from chatbot.presentation.streamlit.components.chat_view import ChatViewComponent
from chatbot.presentation.streamlit.components.citation_pane import CitationPaneComponent
from chatbot.presentation.streamlit.components.sidebar import SidebarComponent
from chatbot.presentation.streamlit.session import SessionManager
from chatbot.presentation.streamlit.theme import ClinicalTerminalTheme


class StreamlitChatApp:
    """Three-column clinical terminal orchestrator for the Altibbi RAG chatbot."""

    def __init__(self, container: DependencyContainer | None = None) -> None:
        self._container = container or DependencyContainer.default()
        self._chat_service = ChatService(self._container)
        self._repository = SessionManager.get_repository()
        self._sidebar = SidebarComponent(self._repository)
        self._chat_view = ChatViewComponent()
        self._citation_pane = CitationPaneComponent()
        self._logger = logging.getLogger(__name__)

    def run(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="\n%(asctime)s | [%(levelname)s] | %(message)s",
            datefmt="%H:%M:%S",
        )

        st.set_page_config(
            page_title="Altibbi Clinical Terminal",
            page_icon=None,
            layout="wide",
            initial_sidebar_state="expanded",
        )
        ClinicalTerminalTheme.inject()
        self._initialize_session_state()

        selected_model, search_method = self._sidebar.render()

        center_col, citation_col = st.columns([2.75, 1], gap="small")

        with center_col:
            self._chat_view.render(selected_model)

        with citation_col:
            self._citation_pane.render()

        self._handle_user_input(selected_model, search_method)

    def _initialize_session_state(self) -> None:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "current_chat_id" not in st.session_state:
            st.session_state.current_chat_id = None

    def _handle_user_input(self, selected_model: str, search_method: str) -> None:
        if st.session_state.get("pending_action"):
            self._handle_suggestion(selected_model, search_method)
            return

        user_input = st.chat_input(
            "Enter clinical inquiry...",
            accept_file=True,
            file_type=["png", "jpg", "jpeg"],
        )
        if not user_input:
            return

        if user_input.files:
            self._handle_image_upload(user_input, selected_model, search_method)
        elif user_input.text:
            self._chat_view.render_user_message(user_input.text)
            st.session_state.messages.append({"role": "user", "content": user_input.text})
            self._execute_text_pipeline(user_input.text, selected_model, search_method)

    def _handle_suggestion(self, selected_model: str, search_method: str) -> None:
        simulated_query = st.session_state.pending_action
        st.session_state.pending_action = None
        self._chat_view.render_user_message(simulated_query)
        st.session_state.messages.append({"role": "user", "content": simulated_query})
        self._execute_text_pipeline(simulated_query, selected_model, search_method)

    def _execute_text_pipeline(
        self,
        query: str,
        selected_model: str,
        search_method: str,
        *,
        is_drug_profile: bool = False,
    ) -> None:
        spinner_label = (
            "Retrieving clinical context..."
            if not is_drug_profile
            else "Analyzing pharmaceutical profile..."
        )
        with st.spinner(spinner_label):
            try:
                pipeline_result = self._chat_service.handle_text_query(
                    query,
                    st.session_state.messages,
                    st.session_state.current_chat_id,
                    selected_model,
                    search_method,
                    is_drug_profile=is_drug_profile,
                )
            except SearchError as exc:
                self._logger.error("Search failed: %s", exc)
                st.error(str(exc))
                return

        st.session_state.current_chat_id = pipeline_result.session_id

        if pipeline_result.status == "fallback":
            st.session_state.messages.append(
                {"role": "assistant", "content": pipeline_result.response, "sources": {}}
            )
            self._chat_view.render_assistant_message(pipeline_result.response)
            st.rerun()
            return

        assistant_message = {
            "role": "assistant",
            "content": pipeline_result.response,
            "sources": pipeline_result.sources,
        }
        if pipeline_result.suggestions:
            assistant_message["suggestions"] = pipeline_result.suggestions

        st.session_state.messages.append(assistant_message)
        self._chat_view.render_assistant_message(
            pipeline_result.response,
            pipeline_result.sources,
        )
        st.rerun()

    def _handle_image_upload(self, user_input, selected_model: str, search_method: str) -> None:
        img_file = user_input.files[0]
        img_bytes = img_file.getvalue()

        with st.spinner("Classifying medical image..."):
            image_result = self._chat_service.handle_image_upload(
                img_bytes,
                img_file.name,
                user_input.text,
                selected_model,
            )

        self._logger.info("Vision Layer Detected Type: %s", image_result.status)
        st.session_state.messages.append({"role": "user", "content": image_result.user_message})
        self._chat_view.render_user_message(image_result.user_message)

        if image_result.status == "unsupported":
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": image_result.assistant_response,
                    "sources": {},
                }
            )
            self._chat_view.render_assistant_message(image_result.assistant_response)
            st.session_state.current_chat_id = self._chat_service.persist_simple_exchange(
                st.session_state.current_chat_id,
                image_result.user_message,
                image_result.assistant_response or "",
                {"model": selected_model, "content_type": "unsupported"},
            )
            st.rerun()
            return

        if image_result.status == "report":
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": image_result.assistant_response,
                    "sources": {},
                }
            )
            self._chat_view.render_assistant_message(image_result.assistant_response)
            st.session_state.current_chat_id = self._chat_service.persist_simple_exchange(
                st.session_state.current_chat_id,
                image_result.user_message,
                image_result.assistant_response or "",
                {"model": selected_model, "content_type": "report"},
            )
            st.rerun()
            return

        if image_result.status == "drug" and image_result.drug_query:
            self._logger.info("Extracted Drug Name: '%s'", image_result.drug_query)
            self._execute_text_pipeline(
                image_result.drug_query,
                selected_model,
                search_method,
                is_drug_profile=True,
            )


class StreamlitApp(StreamlitChatApp):
    """Backward-compatible alias for StreamlitChatApp."""


if __name__ == "__main__":
    StreamlitChatApp().run()
