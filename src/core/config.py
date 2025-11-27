import os
from functools import lru_cache
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

    openai: Optional[AIProviderConfig] = AIProviderConfig(model="gpt-4o")
    anthropic: Optional[AIProviderConfig] = AIProviderConfig(
        model="claude-sonnet-4-20250514"
    )
    gemini: Optional[AIProviderConfig] = AIProviderConfig(model="gemini-2.0-flash")
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

    def get_output_dir(self) -> Path:
        """Get output directory, configurable via OUTPUT_DIR env var."""
        output_path = os.getenv("OUTPUT_DIR")
        if output_path:
            return Path(output_path)
        return self.BASE_DIR / "output"

    # Research Configuration
    MAX_SEARCH_RESULTS: int = 5
    CONCURRENT_SEARCHES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    def validate_config(self) -> list[str]:
        """
        Validate configuration and return list of warnings.
        Does not raise exceptions to allow graceful degradation.
        """
        warnings = []

        # Check primary AI provider has API key
        provider_key_map = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
            "groq": self.GROQ_API_KEY,
            "ollama": True,  # Ollama doesn't need API key
        }

        primary = self.ai.primary
        if primary != "ollama" and not provider_key_map.get(primary):
            warnings.append(f"Primary AI provider '{primary}' has no API key configured")

        # Check fallback if configured
        fallback = self.ai.fallback
        if fallback and fallback != "ollama" and not provider_key_map.get(fallback):
            warnings.append(f"Fallback AI provider '{fallback}' has no API key configured")

        # Check search API key
        if not self.TAVILY_API_KEY:
            warnings.append("TAVILY_API_KEY not set - search functionality will be limited")

        return warnings

    def has_any_ai_provider(self) -> bool:
        """Check if at least one AI provider is configured."""
        return any([
            self.OPENAI_API_KEY,
            self.ANTHROPIC_API_KEY,
            self.GEMINI_API_KEY,
            self.GROQ_API_KEY,
            self.ai.primary == "ollama",  # Ollama works without API key
        ])


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance. Call clear_settings() to reset."""
    return Settings()


def clear_settings():
    """Clear the cached settings (useful for testing)."""
    get_settings.cache_clear()
