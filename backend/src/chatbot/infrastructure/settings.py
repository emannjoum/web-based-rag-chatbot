import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai_lib
from tavily import TavilyClient


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    openai_api_key: str
    gemini_api_key: str
    tavily_api_key: str
    serper_api_key: str
    api_host: str
    api_port: int
    api_reload: bool
    cors_origins: list[str]
    default_search_method: str
    frontend_dist_path: Path
    redis_url: str
    redis_cache_enabled: bool
    redis_cache_ttl_seconds: int
    mysql_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    streamlit_user_id: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        cors_raw = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000",
        )
        project_root = Path(__file__).resolve().parents[4]
        dist_default = project_root / "frontend" / "dist"

        return cls(
            mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            serper_api_key=os.getenv("SERPER_API_KEY", ""),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            api_reload=os.getenv("API_RELOAD", "false").lower() == "true",
            cors_origins=[origin.strip() for origin in cors_raw.split(",") if origin.strip()],
            default_search_method=os.getenv("DEFAULT_SEARCH_METHOD", "Serper"),
            frontend_dist_path=Path(os.getenv("FRONTEND_DIST_PATH", str(dist_default))),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            redis_cache_enabled=os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true",
            redis_cache_ttl_seconds=int(os.getenv("REDIS_CACHE_TTL_SECONDS", "300")),
            mysql_url=os.getenv(
                "MYSQL_URL",
                "mysql+pymysql://medatlas:medatlas@localhost:3306/medatlas",
            ),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "10080")),
            streamlit_user_id=int(os.getenv("STREAMLIT_USER_ID", "1")),
        )

    @cached_property
    def openai_client(self) -> OpenAI:
        return OpenAI(api_key=self.openai_api_key)

    @cached_property
    def tavily_client(self) -> TavilyClient:
        return TavilyClient(api_key=self.tavily_api_key)

    def configure_gemini(self) -> None:
        genai_lib.configure(api_key=self.gemini_api_key)
