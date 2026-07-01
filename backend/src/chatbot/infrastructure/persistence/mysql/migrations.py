"""Run Alembic migrations programmatically."""

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def _find_alembic_ini() -> Path | None:
    configured = os.getenv("ALEMBIC_CONFIG", "").strip()
    if configured:
        path = Path(configured)
        if path.exists():
            return path

    for base in (Path.cwd(), *Path.cwd().parents):
        candidate = base / "alembic.ini"
        if candidate.exists():
            return candidate

    for base in (Path(__file__).resolve().parents[5], *Path(__file__).resolve().parents):
        candidate = base / "alembic.ini"
        if candidate.exists():
            return candidate

    return None


def run_migrations(database_url: str) -> None:
    alembic_ini = _find_alembic_ini()
    if alembic_ini is None:
        raise FileNotFoundError("alembic.ini not found; database migrations were not applied.")

    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", database_url)
    logger.info("Running Alembic migrations using %s", alembic_ini)
    command.upgrade(config, "head")
