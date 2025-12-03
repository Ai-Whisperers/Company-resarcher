"""
Main Settings class.
"""

import os
from pathlib import Path
from typing import Optional, Any
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import Profile, ProfileDefaults, APIKeyPool, KeyRotationStrategy
from .providers import AIConfig, IntegrationKeysConfig
from .services import CacheConfig, SearchConfig, BrowserConfig
from .database import DatabaseConfig, RedisConfig
from .server import ServerConfig
from .pipeline import ResearchConfig, GraphConfig, DeepResearchConfig, AgentConfig
from .telemetry import TelemetryConfig
from .runtime import RuntimeConfig


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

    # INT-002: Alpha Vantage API for financial fundamentals
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None

    # INT-003: FRED API for bond yield data
    FRED_API_KEY: Optional[SecretStr] = None

    # INT-004: GitHub API for tech stack analysis
    GITHUB_API_TOKEN: Optional[SecretStr] = None

    # INT-005: Financial Modeling Prep API for comprehensive financials
    FINANCIAL_MODELING_PREP_API_KEY: Optional[SecretStr] = None

    # INT-006: OpenCorporates API for company registry data
    OPENCORPORATES_API_KEY: Optional[SecretStr] = None

    # INT-007: WHOIS API for domain ownership data
    WHOIS_API_KEY: Optional[SecretStr] = None

    # Additional Search Providers (for fallback chain)
    SERPER_API_KEY: Optional[SecretStr] = None  # serper.dev - cheap Google results
    JINA_API_KEY: Optional[SecretStr] = None  # jina.ai - optional for higher limits
    LANGSEARCH_API_KEY: Optional[SecretStr] = (
        None  # langsearch.com - FREE AI-optimized search
    )
    BRAVE_API_KEY: Optional[SecretStr] = None  # brave.com - 2K free/month
    BING_API_KEY: Optional[SecretStr] = (
        None  # Bing Search API via Azure - 1K free/month
    )

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: Optional[SecretStr] = None
    LANGFUSE_SECRET_KEY: Optional[SecretStr] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = True  # Feature flag to enable/disable observability

    # AI Configuration
    ai: AIConfig = AIConfig()

    # Runtime Configuration
    runtime: RuntimeConfig = RuntimeConfig()

    # Cache Configuration
    cache: CacheConfig = CacheConfig()

    # Research Configuration (CODE-001, CODE-002)
    research: ResearchConfig = ResearchConfig()

    # Database Configuration (ARCH-004)
    database: DatabaseConfig = DatabaseConfig()

    # Redis Configuration (ARCH-004)
    redis: RedisConfig = RedisConfig()

    # Server Configuration (ARCH-004)
    server: ServerConfig = ServerConfig()

    # Agent Configuration (ARCH-004)
    agent: AgentConfig = AgentConfig()

    # Browser Configuration (ARCH-004)
    browser: BrowserConfig = BrowserConfig()

    # Graph Configuration (ARCH-004)
    graph: GraphConfig = GraphConfig()

    # Deep Research Configuration (ARCH-004)
    deep_research: DeepResearchConfig = DeepResearchConfig()

    # Search Configuration (ARCH-004)
    search: SearchConfig = SearchConfig()

    # Telemetry Configuration (ARCH-004)
    telemetry: TelemetryConfig = TelemetryConfig()

    # Integration Keys (ARCH-004)
    integrations: IntegrationKeysConfig = IntegrationKeysConfig()

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent

    def get_cache_dir(self) -> Path:
        """Get cache directory, configurable via CACHE_DIR env var."""
        if hasattr(self, "_cli_cache_dir") and self._cli_cache_dir:
            return Path(self._cli_cache_dir)

        cache_path = os.getenv("CACHE_DIR")
        if cache_path:
            return Path(cache_path)
        return self.BASE_DIR / ".cache"

    def get_output_dir(self) -> Path:
        """Get output directory, configurable via OUTPUT_DIR env var."""
        if hasattr(self, "_cli_output_dir") and self._cli_output_dir:
            return Path(self._cli_output_dir)

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
            warnings.append(
                f"Primary AI provider '{primary}' has no API key configured"
            )

        # Check fallback if configured
        fallback = self.ai.fallback
        if fallback and fallback != "ollama" and not provider_key_map.get(fallback):
            warnings.append(
                f"Fallback AI provider '{fallback}' has no API key configured"
            )

        # Check search API keys - now using fallback chain, so not critical
        has_any_search = self._has_secret(self.TAVILY_API_KEY) or self._has_secret(
            self.SERPER_API_KEY
        )
        if not has_any_search:
            # Not a warning anymore - DuckDuckGo is free and works without keys
            pass  # Free providers (DuckDuckGo, Jina) available by default

        return warnings

    def get_key_pool(
        self,
        provider: str,
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ) -> APIKeyPool:
        """
        Get API key pool for a provider with rotation support (SEC-001).

        Supports comma-separated keys in env vars for multi-key rotation.

        Args:
            provider: Provider name (openai, anthropic, gemini, groq, tavily, serper, etc.)
            strategy: Rotation strategy (round_robin or failover)

        Returns:
            APIKeyPool instance for the provider

        Example:
            pool = settings.get_key_pool("openai")
            key = pool.get_key()  # Gets next key in rotation
        """
        provider_to_secret = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
            "groq": self.GROQ_API_KEY,
            "tavily": self.TAVILY_API_KEY,
            "serper": self.SERPER_API_KEY,
            "serpapi": self.SERPAPI_API_KEY,
            "jina": self.JINA_API_KEY,
            "langsearch": self.LANGSEARCH_API_KEY,
            "brave": self.BRAVE_API_KEY,
            "bing": self.BING_API_KEY,
            "newsapi": self.NEWSAPI_KEY,
        }

        secret = provider_to_secret.get(provider.lower())
        return APIKeyPool.from_secret(secret, strategy)

    def has_any_ai_provider(self) -> bool:
        """Check if at least one AI provider is configured."""
        return any(
            [
                self._has_secret(self.OPENAI_API_KEY),
                self._has_secret(self.ANTHROPIC_API_KEY),
                self._has_secret(self.GEMINI_API_KEY),
                self._has_secret(self.GROQ_API_KEY),
                self.ai.primary == "ollama",  # Ollama works without API key
            ]
        )

    @property
    def is_headless(self) -> bool:
        """Check if running in headless mode."""
        # Can be set via config or environment variable
        return self.runtime.headless or os.getenv("HEADLESS", "").lower() in (
            "1",
            "true",
            "yes",
        )

    @property
    def is_interactive(self) -> bool:
        """Check if interactive mode is enabled."""
        return not self.runtime.disable_interactive and not self.is_headless

    @property
    def is_quiet(self) -> bool:
        """Check if quiet mode is enabled."""
        return self.runtime.quiet or os.getenv("QUIET", "").lower() in (
            "1",
            "true",
            "yes",
        )

    @property
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.runtime.verbose or os.getenv("VERBOSE", "").lower() in (
            "1",
            "true",
            "yes",
        )
