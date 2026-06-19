from chatbot.presentation.streamlit.components.quick_actions import QuickActionsComponent


class SuggestionsComponent:
    """Backward-compatible alias that delegates to QuickActionsComponent."""

    def __init__(self) -> None:
        self._quick_actions = QuickActionsComponent()

    def render_for_message(self, message, index: int, total_messages: int) -> None:
        self._quick_actions.render_for_message(message, index, total_messages)
