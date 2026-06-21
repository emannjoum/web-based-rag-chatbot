from functools import lru_cache

from chatbot.application.chat_service import ChatService
from chatbot.application.dependencies import DependencyContainer
from chatbot.application.session_service import SessionService


@lru_cache(maxsize=1)
def get_container() -> DependencyContainer:
    return DependencyContainer.default()


def get_chat_service() -> ChatService:
    return ChatService(get_container())


def get_session_service() -> SessionService:
    return SessionService(get_container().repository)
