import os
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class AIProviderConfig(BaseModel):
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096


class AIConfig(BaseModel):
    primary: Literal["openai", "anthropic", "gemini", "groq", "ollama"] = "openai"
    fallback: Optional[Literal["openai", "anthropic", "gemini", "groq", "ollama"]] = (
        None
    )

    openai: Optional[AIProviderConfig] = AIProviderConfig(model="gpt-4-turbo-preview")
    anthropic: Optional[AIProviderConfig] = AIProviderConfig(
        model="claude-3-opus-20240229"
    )
    gemini: Optional[AIProviderConfig] = AIProviderConfig(model="gemini-1.5-pro-latest")
    groq: Optional[AIProviderConfig] = AIProviderConfig(model="llama-3.1-8b-instant")
    ollama: Optional[AIProviderConfig] = AIProviderConfig(model="llama3.1:8b")


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    TAVILY_API_KEY: Optional[str] = None
    NEWSAPI_KEY: Optional[str] = None  # For news aggregation
    SERPAPI_API_KEY: Optional[str] = None

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # AI Configuration
    ai: AIConfig = AIConfig()

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "output"

    # Research Configuration
    MAX_SEARCH_RESULTS: int = 5
    CONCURRENT_SEARCHES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )


def get_settings() -> Settings:
    return Settings()
