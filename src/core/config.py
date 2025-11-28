import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, SecretStr


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


class RuntimeConfig(BaseModel):
    """Runtime configuration for application behavior."""
    headless: bool = False  # Run without UI, for CLI/API/CI use
    log_to_file: bool = False  # Redirect logs to file instead of stdout
    log_file_path: Optional[str] = None  # Path for log file
    disable_interactive: bool = False  # Disable interactive prompts
    quiet: bool = False  # Suppress non-essential output
    verbose: bool = False  # Enable verbose output


class Settings(BaseSettings):
    # API Authentication - Required for protected endpoints
    API_KEY: Optional[SecretStr] = None

    # AI Provider Keys - Using SecretStr to prevent accidental exposure in logs/repr
    OPENAI_API_KEY: Optional[SecretStr] = None
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    GEMINI_API_KEY: Optional[SecretStr] = None
    GROQ_API_KEY: Optional[SecretStr] = None

    TAVILY_API_KEY: Optional[SecretStr] = None
    NEWSAPI_KEY: Optional[SecretStr] = None  # For news aggregation
    SERPAPI_API_KEY: Optional[SecretStr] = None

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[SecretStr] = None
    LANGFUSE_SECRET_KEY: Optional[SecretStr] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # AI Configuration
    ai: AIConfig = AIConfig()

    # Runtime Configuration
    runtime: RuntimeConfig = RuntimeConfig()

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

    def _has_secret(self, secret: Optional[SecretStr]) -> bool:
        """Check if a SecretStr has a value."""
        return secret is not None and len(secret.get_secret_value()) > 0

    def validate_config(self) -> list[str]:
        """
        Validate configuration and return list of warnings.
        Does not raise exceptions to allow graceful degradation.
        """
        warnings = []

        # Check primary AI provider has API key
        provider_key_map = {
            "openai": self._has_secret(self.OPENAI_API_KEY),
            "anthropic": self._has_secret(self.ANTHROPIC_API_KEY),
            "gemini": self._has_secret(self.GEMINI_API_KEY),
            "groq": self._has_secret(self.GROQ_API_KEY),
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
        if not self._has_secret(self.TAVILY_API_KEY):
            warnings.append("TAVILY_API_KEY not set - search functionality will be limited")

        return warnings

    def has_any_ai_provider(self) -> bool:
        """Check if at least one AI provider is configured."""
        return any([
            self._has_secret(self.OPENAI_API_KEY),
            self._has_secret(self.ANTHROPIC_API_KEY),
            self._has_secret(self.GEMINI_API_KEY),
            self._has_secret(self.GROQ_API_KEY),
            self.ai.primary == "ollama",  # Ollama works without API key
        ])

    @property
    def is_headless(self) -> bool:
        """Check if running in headless mode."""
        # Can be set via config or environment variable
        return self.runtime.headless or os.getenv("HEADLESS", "").lower() in ("1", "true", "yes")

    @property
    def is_interactive(self) -> bool:
        """Check if interactive mode is enabled."""
        return not self.runtime.disable_interactive and not self.is_headless

    @property
    def is_quiet(self) -> bool:
        """Check if quiet mode is enabled."""
        return self.runtime.quiet or os.getenv("QUIET", "").lower() in ("1", "true", "yes")

    @property
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.runtime.verbose or os.getenv("VERBOSE", "").lower() in ("1", "true", "yes")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance. Call clear_settings() to reset."""
    return Settings()


def clear_settings():
    """Clear the cached settings (useful for testing)."""
    get_settings.cache_clear()
