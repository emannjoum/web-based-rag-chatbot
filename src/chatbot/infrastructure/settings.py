import os
from dataclasses import dataclass
from functools import cached_property

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

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            serper_api_key=os.getenv("SERPER_API_KEY", ""),
        )

    @cached_property
    def openai_client(self) -> OpenAI:
        return OpenAI(api_key=self.openai_api_key)

    @cached_property
    def tavily_client(self) -> TavilyClient:
        return TavilyClient(api_key=self.tavily_api_key)

    def configure_gemini(self) -> None:
        genai_lib.configure(api_key=self.gemini_api_key)
