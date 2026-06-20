from dataclasses import dataclass

from chatbot.infrastructure.llm.factory import GEMINI_FLASH_LITE, GPT4O_MINI


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    provider_value: str


class ModelRegistry:
    """Maps UI-facing model identifiers to backend LLM provider values."""

    OPTIONS: tuple[ModelOption, ...] = (
        ModelOption("kimi-k2.5", "Kimi K2.5", GEMINI_FLASH_LITE),
        ModelOption("clinical-insight-3", "Clinical-Insight 3.0", GPT4O_MINI),
        ModelOption("medilogic-4", "Medi-Logic 4", GPT4O_MINI),
        ModelOption("medical-pricer", "Medical Pricer", GEMINI_FLASH_LITE),
    )

    @classmethod
    def resolve_provider_value(cls, model_id: str) -> str:
        for option in cls.OPTIONS:
            if option.id == model_id:
                return option.provider_value
        return cls.OPTIONS[0].provider_value

    @classmethod
    def default_id(cls) -> str:
        return cls.OPTIONS[0].id

    @classmethod
    def as_dicts(cls) -> list[dict[str, str]]:
        return [
            {"id": option.id, "label": option.label, "provider_value": option.provider_value}
            for option in cls.OPTIONS
        ]
