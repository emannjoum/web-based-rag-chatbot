import logging
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[3]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import uvicorn

from chatbot.infrastructure.settings import Settings
from chatbot.presentation.api.app_factory import create_app

app = create_app()


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | [%(levelname)s] | %(name)s | %(message)s",
    )
    settings = Settings.from_env()
    uvicorn.run(
        "chatbot.presentation.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        factory=False,
    )


if __name__ == "__main__":
    run()
