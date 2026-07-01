import streamlit as st

from chatbot.application.dependencies import DependencyContainer
from chatbot.infrastructure.persistence.mongo_repository import MongoChatRepository


class SessionManager:
    @classmethod
    @st.cache_resource
    def get_repository(cls) -> MongoChatRepository:
        return DependencyContainer.default().repository
