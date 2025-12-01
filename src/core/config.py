"""
Configuration management for Company Researcher.

This module provides centralized configuration with:
- Environment-based profiles (development, staging, production)
- Pydantic validation with SecretStr for sensitive values
- Nested configuration via env delimiter (e.g., AI__PRIMARY=anthropic)
- Graceful degradation with validation warnings

Usage:
    from src.core.config import get_settings, get_profile

    settings = get_settings()
    profile = get_profile()  # "development", "staging", or "production"
"""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, Literal, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, SecretStr


class Profile(str, Enum):
    """Application environment profiles."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def from_env(cls) -> "Profile":
        """Get profile from environment variable."""
        env_value = os.getenv("APP_PROFILE", os.getenv("ENVIRONMENT", "development"))
        try:
            return cls(env_value.lower())
        except ValueError:
            return cls.DEVELOPMENT


class AIProviderConfig(BaseModel):
    """Configuration for a single AI provider."""

    model: str
    temperature: float = 0.7
    max_tokens: int = 4096


class AIConfig(BaseModel):
    """AI provider configuration."""

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


class CacheConfig(BaseModel):
    """Cache configuration settings."""

    enabled: bool = True  # Enable/disable caching globally
    default_ttl: int = 3600  # Default TTL in seconds (1 hour)
    ai_cache_enabled: bool = True  # Enable AI response caching
    max_size_mb: Optional[int] = None  # Max cache size (None = unlimited)
    cleanup_interval: int = 3600  # Cleanup interval in seconds


class RuntimeConfig(BaseModel):
    """Runtime configuration for application behavior."""

    headless: bool = False  # Run without UI, for CLI/API/CI use
    log_to_file: bool = False  # Redirect logs to file instead of stdout
    log_file_path: Optional[str] = None  # Path for log file
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    disable_interactive: bool = False  # Disable interactive prompts
    quiet: bool = False  # Suppress non-essential output
    verbose: bool = False  # Enable verbose output


class ProfileDefaults:
    """Profile-specific default configurations."""

    @staticmethod
    def get_defaults(profile: Profile) -> dict[str, Any]:
        """Get default configuration values for a profile."""
        defaults = {
            Profile.DEVELOPMENT: {
                "runtime": {
                    "log_level": "DEBUG",
                    "verbose": True,
                },
                "MAX_SEARCH_RESULTS": 3,
                "CONCURRENT_SEARCHES": 2,
            },
            Profile.STAGING: {
                "runtime": {
                    "log_level": "INFO",
                    "verbose": False,
                },
                "MAX_SEARCH_RESULTS": 5,
                "CONCURRENT_SEARCHES": 3,
            },
            Profile.PRODUCTION: {
                "runtime": {
                    "log_level": "WARNING",
                    "verbose": False,
                    "headless": True,
                },
                "MAX_SEARCH_RESULTS": 10,
                "CONCURRENT_SEARCHES": 5,
            },
        }
        return defaults.get(profile, {})


class Settings(BaseSettings):
    """Application settings with profile-based defaults.

    Configuration priority (highest to lowest):
    1. Environment variables
    2. .env file
    3. Profile-specific defaults
    4. Class defaults
    """

    # Profile - determines default values
    profile: Profile = Profile.DEVELOPMENT

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

    # Additional Search Providers (for fallback chain)
    SERPER_API_KEY: Optional[SecretStr] = None  # serper.dev - cheap Google results
    JINA_API_KEY: Optional[SecretStr] = None  # jina.ai - optional for higher limits
    LANGSEARCH_API_KEY: Optional[SecretStr] = None  # langsearch.com - FREE AI-optimized search

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[SecretStr] = None
    LANGFUSE_SECRET_KEY: Optional[SecretStr] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # AI Configuration
    ai: AIConfig = AIConfig()

    # Runtime Configuration
    runtime: RuntimeConfig = RuntimeConfig()

    # Cache Configuration
    cache: CacheConfig = CacheConfig()

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    def get_cache_dir(self) -> Path:
        """Get cache directory, configurable via CACHE_DIR env var."""
        cache_path = os.getenv("CACHE_DIR")
        if cache_path:
            return Path(cache_path)
        return self.BASE_DIR / ".cache"

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

    def model_post_init(self, __context: Any) -> None:
        """Apply profile-specific defaults after initialization."""
        # Get profile from env if not explicitly set
        if self.profile == Profile.DEVELOPMENT:
            self.profile = Profile.from_env()

        # Apply profile defaults for unset values
        defaults = ProfileDefaults.get_defaults(self.profile)

        # Apply runtime defaults
        runtime_defaults = defaults.get("runtime", {})
        for key, value in runtime_defaults.items():
            # Only apply if not explicitly set via env
            env_key = f"RUNTIME__{key.upper()}"
            if not os.getenv(env_key):
                current = getattr(self.runtime, key, None)
                default_class_value = RuntimeConfig.model_fields[key].default
                if current == default_class_value:
                    setattr(self.runtime, key, value)

        # Apply other defaults
        for key in ["MAX_SEARCH_RESULTS", "CONCURRENT_SEARCHES"]:
            if key in defaults and not os.getenv(key):
                current = getattr(self, key)
                default_class_value = self.model_fields[key].default
                if current == default_class_value:
                    setattr(self, key, defaults[key])

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

        # Check search API keys - now using fallback chain, so not critical
        has_any_search = (
            self._has_secret(self.TAVILY_API_KEY) or
            self._has_secret(self.SERPER_API_KEY)
        )
        if not has_any_search:
            # Not a warning anymore - DuckDuckGo is free and works without keys
            pass  # Free providers (DuckDuckGo, Jina) available by default

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


def get_profile() -> Profile:
    """Get the current application profile."""
    return get_settings().profile


def is_production() -> bool:
    """Check if running in production profile."""
    return get_profile() == Profile.PRODUCTION


def is_development() -> bool:
    """Check if running in development profile."""
    return get_profile() == Profile.DEVELOPMENT


def clear_settings():
    """Clear the cached settings (useful for testing)."""
    get_settings.cache_clear()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Classes
    "Settings",
    "Profile",
    "ProfileDefaults",
    "AIConfig",
    "AIProviderConfig",
    "RuntimeConfig",
    "CacheConfig",
    # Functions
    "get_settings",
    "get_profile",
    "is_production",
    "is_development",
    "clear_settings",
]
