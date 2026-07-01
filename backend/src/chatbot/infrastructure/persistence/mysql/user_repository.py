from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from chatbot.domain.exceptions import AuthError
from chatbot.domain.models import User
from chatbot.infrastructure.auth.password import hash_password, verify_password
from chatbot.infrastructure.persistence.mysql.models import UserRecord


class MySQLUserRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_user(self, email: str, password: str, display_name: str) -> User:
        normalized_email = email.strip().lower()
        record = UserRecord(
            email=normalized_email,
            display_name=display_name.strip(),
            password_hash=hash_password(password),
        )
        session = self._session_factory()
        try:
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_domain(record)
        except IntegrityError as exc:
            session.rollback()
            raise AuthError("An account with this email already exists.") from exc
        finally:
            session.close()

    def authenticate(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        session = self._session_factory()
        try:
            record = session.scalar(select(UserRecord).where(UserRecord.email == normalized_email))
            if record is None or not verify_password(password, record.password_hash):
                raise AuthError("Invalid email or password.")
            return self._to_domain(record)
        finally:
            session.close()

    def get_by_id(self, user_id: int) -> User | None:
        session = self._session_factory()
        try:
            record = session.get(UserRecord, user_id)
            if record is None:
                return None
            return self._to_domain(record)
        finally:
            session.close()

    @staticmethod
    def _to_domain(record: UserRecord) -> User:
        return User(
            id=record.id,
            email=record.email,
            display_name=record.display_name,
            created_at=record.created_at,
        )
