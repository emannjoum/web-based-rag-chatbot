from chatbot.domain.exceptions import AuthError
from chatbot.domain.models import User
from chatbot.infrastructure.auth.jwt import create_access_token
from chatbot.infrastructure.persistence.mysql.user_repository import MySQLUserRepository
from chatbot.infrastructure.settings import Settings


class AuthService:
    def __init__(self, user_repository: MySQLUserRepository, settings: Settings) -> None:
        self._users = user_repository
        self._settings = settings

    def register(self, email: str, password: str, display_name: str) -> tuple[User, str]:
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters long.")
        user = self._users.create_user(email, password, display_name)
        token = self._issue_token(user.id)
        return user, token

    def login(self, email: str, password: str) -> tuple[User, str]:
        user = self._users.authenticate(email, password)
        token = self._issue_token(user.id)
        return user, token

    def get_current_user(self, user_id: int) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise AuthError("User account not found.")
        return user

    def _issue_token(self, user_id: int) -> str:
        return create_access_token(
            user_id=user_id,
            secret_key=self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
            expire_minutes=self._settings.jwt_expire_minutes,
        )
