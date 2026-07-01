from fastapi import APIRouter

from chatbot.application.session_service import SessionService
from chatbot.infrastructure.search.factory import MANUAL_SCRAPING, SERPER, TAVILY
from chatbot.infrastructure.settings import Settings
from chatbot.presentation.api.dependencies import get_container
from chatbot.presentation.api.model_registry import ModelRegistry
from chatbot.presentation.api.schemas import ConfigResponse, ModelOptionSchema

router = APIRouter(prefix="/config", tags=["config"])


class ConfigController:
    @staticmethod
    def build_response(settings: Settings) -> ConfigResponse:
        return ConfigResponse(
            models=[ModelOptionSchema(**item) for item in ModelRegistry.as_dicts()],
            search_methods=[SERPER, TAVILY, MANUAL_SCRAPING],
            default_model_id=ModelRegistry.default_id(),
            default_search_method=settings.default_search_method,
        )


@router.get("", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    settings = get_container().settings
    return ConfigController.build_response(settings)
