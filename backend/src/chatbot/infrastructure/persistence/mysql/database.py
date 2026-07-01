from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from chatbot.infrastructure.persistence.mysql.models import Base


def create_db_engine(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_db_engine(database_url)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_database(database_url: str) -> None:
    engine = create_db_engine(database_url)
    Base.metadata.create_all(bind=engine)


def get_db_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
