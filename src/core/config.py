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
import threading
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, Literal, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, SecretStr, field_validator


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


class DatabaseConfig(BaseModel):
    """Database configuration settings (ARCH-004)."""

    url: str = "sqlite:///data/research.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False  # SQL logging


class RedisConfig(BaseModel):
    """Redis configuration settings (ARCH-004)."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    default_ttl: int = 3600
    key_prefix: str = "company_researcher:"
    max_connections: int = 10


class ServerConfig(BaseModel):
    """API server configuration settings (ARCH-004)."""

    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    cors_max_age: int = 600
    cors_methods: str = "GET,POST,DELETE,OPTIONS"
    max_request_size: int = 65536
    shutdown_timeout_seconds: int = 30
    research_timeout_seconds: int = 1800  # 30 minutes


class AgentConfig(BaseModel):
    """Agent execution configuration settings (ARCH-004)."""

    max_concurrent_queries: int = 5
    max_requests_per_domain: int = 3
    domain_cooldown_seconds: float = 1.0
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 3
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 500


class BrowserConfig(BaseModel):
    """Browser/scraping configuration settings (ARCH-004)."""

    fetch_timeout_seconds: int = 60
    page_navigation_timeout_ms: int = 30000
    max_concurrent: int = 5
    enable_html_cache: bool = True


class GraphConfig(BaseModel):
    """Research graph configuration settings (ARCH-004)."""

    node_timeout_seconds: int = 300
    max_retry_attempts: int = 3
    retry_backoff_base: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60


class DeepResearchConfig(BaseModel):
    """Deep research configuration settings (ARCH-004)."""

    max_context_words: int = 25000
    default_breadth: int = 4
    default_depth: int = 2
    concurrency: int = 2


class SearchConfig(BaseModel):
    """Search configuration settings (ARCH-004)."""

    timeout_seconds: int = 30
    rate_limit_per_minute: int = 30
    cooldown_seconds: float = 60.0
    max_retries: int = 3
    base_backoff_seconds: float = 2.0
    # Pagination settings (TECH-003)
    results_per_page: int = 10
    max_pages: int = 3
    page_delay_seconds: float = 1.0


class TelemetryConfig(BaseModel):
    """Telemetry/observability configuration settings (ARCH-004)."""

    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1
    otel_service_name: str = "company-researcher"
    otel_enabled: bool = True
    otel_endpoint: Optional[str] = None
    otel_console_exporter: bool = False
    otel_trace_sample_rate: float = 1.0
    prometheus_enabled: bool = True
    prometheus_port: int = 9090


class IntegrationKeysConfig(BaseModel):
    """Third-party integration API keys (ARCH-004)."""

    glassdoor_api_key: Optional[str] = None
    glassdoor_rapidapi_host: str = "glassdoor-api.p.rapidapi.com"
    proxycurl_api_key: Optional[str] = None
    linkedin_api_key: Optional[str] = None
    crunchbase_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    neo4j_uri: Optional[str] = None
    llama_cloud_api_key: Optional[str] = None


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


class KeyRotationStrategy(str, Enum):
    """API key rotation strategies (SEC-001)."""

    ROUND_ROBIN = "round_robin"  # Rotate through keys sequentially
    FAILOVER = "failover"  # Use primary until it fails, then fallback


class APIKeyPool:
    """
    Thread-safe API key rotation pool (SEC-001).

    Supports multiple API keys per provider with round-robin or failover strategy.
    Keys can be provided as comma-separated values in env vars:
        OPENAI_API_KEY=key1,key2,key3

    Usage:
        pool = APIKeyPool(["key1", "key2"], strategy=KeyRotationStrategy.ROUND_ROBIN)
        key = pool.get_key()  # Returns next key in rotation
        pool.mark_failed("key1")  # Mark key as failed (will skip in rotation)
    """

    def __init__(
        self,
        keys: list[str],
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ):
        self._keys = [k.strip() for k in keys if k and k.strip()]
        self._strategy = strategy
        self._current_index = 0
        self._failed_keys: set[str] = set()
        self._lock = threading.Lock()

    @property
    def available_keys(self) -> list[str]:
        """Get list of non-failed keys."""
        with self._lock:
            return [k for k in self._keys if k not in self._failed_keys]

    @property
    def has_keys(self) -> bool:
        """Check if any keys are available."""
        return len(self.available_keys) > 0

    @property
    def key_count(self) -> int:
        """Get total number of keys (including failed)."""
        return len(self._keys)

    def get_key(self) -> Optional[str]:
        """
        Get the next API key based on rotation strategy.

        Returns:
            API key string, or None if no keys available.
        """
        with self._lock:
            available = [k for k in self._keys if k not in self._failed_keys]
            if not available:
                return None

            if self._strategy == KeyRotationStrategy.FAILOVER:
                # Always return first available key
                return available[0]

            # Round-robin: cycle through available keys
            self._current_index = self._current_index % len(available)
            key = available[self._current_index]
            self._current_index = (self._current_index + 1) % len(available)
            return key

    def mark_failed(self, key: str) -> None:
        """Mark a key as failed (will be skipped in rotation)."""
        with self._lock:
            self._failed_keys.add(key)

    def mark_recovered(self, key: str) -> None:
        """Mark a previously failed key as recovered."""
        with self._lock:
            self._failed_keys.discard(key)

    def reset(self) -> None:
        """Reset all failed keys and rotation index."""
        with self._lock:
            self._failed_keys.clear()
            self._current_index = 0

    @classmethod
    def from_env(
        cls,
        env_var: str,
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ) -> "APIKeyPool":
        """
        Create key pool from environment variable.

        Supports comma-separated keys: OPENAI_API_KEY=key1,key2,key3
        """
        value = os.getenv(env_var, "")
        keys = [k.strip() for k in value.split(",") if k.strip()]
        return cls(keys, strategy)

    @classmethod
    def from_secret(
        cls,
        secret: Optional[SecretStr],
        strategy: KeyRotationStrategy = KeyRotationStrategy.ROUND_ROBIN,
    ) -> "APIKeyPool":
        """Create key pool from a SecretStr (may contain comma-separated keys)."""
        if not secret:
            return cls([], strategy)
        value = secret.get_secret_value()
        keys = [k.strip() for k in value.split(",") if k.strip()]
        return cls(keys, strategy)


class ResearchConfig(BaseModel):
    """Research-specific configuration settings (CODE-001)."""

    # Configurable research tone - affects report writing style
    tone: Literal["Objective", "Analytical", "Casual", "Professional", "Academic"] = "Objective"

    # Research depth settings
    max_iterations: int = 3  # Maximum research iterations
    min_sources: int = 5  # Minimum sources per topic
    max_sources: int = 20  # Maximum sources per topic

    # Title fallback behavior (CODE-002)
    use_domain_as_fallback_title: bool = True  # Use domain name when title is Unknown


class RuntimeConfig(BaseModel):
    """Runtime configuration for application behavior."""

    headless: bool = False  # Run without UI, for CLI/API/CI use
    log_to_file: bool = False  # Redirect logs to file instead of stdout
    log_file_path: Optional[str] = None  # Path for log file
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    disable_interactive: bool = False  # Disable interactive prompts
    quiet: bool = False  # Suppress non-essential output
    verbose: bool = False  # Enable verbose output


class CLIConfig(BaseModel):
    """
    CLI argument overrides that take precedence over environment variables.

    This allows CLI arguments to override Settings values at runtime.
    Use apply_cli_overrides() to merge CLI args into settings.

    Example:
        cli_config = CLIConfig(
            verbose=True,
            log_level="DEBUG",
            max_search_results=10
        )
        settings = apply_cli_overrides(get_settings(), cli_config)
    """

    # Runtime overrides
    verbose: Optional[bool] = None
    quiet: Optional[bool] = None
    headless: Optional[bool] = None
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = None
    log_to_file: Optional[bool] = None
    log_file_path: Optional[str] = None
    disable_interactive: Optional[bool] = None

    # Research overrides
    max_search_results: Optional[int] = None
    concurrent_searches: Optional[int] = None
    tone: Optional[Literal["Objective", "Analytical", "Casual", "Professional", "Academic"]] = None
    max_iterations: Optional[int] = None
    min_sources: Optional[int] = None
    max_sources: Optional[int] = None

    # AI provider override
    ai_provider: Optional[Literal["openai", "anthropic", "gemini", "groq", "ollama"]] = None

    # Path overrides
    output_dir: Optional[str] = None
    cache_dir: Optional[str] = None

    # Cache overrides
    cache_enabled: Optional[bool] = None
    cache_ttl: Optional[int] = None


def apply_cli_overrides(settings: "Settings", cli: CLIConfig) -> "Settings":
    """
    Apply CLI configuration overrides to settings.

    CLI arguments take highest precedence over environment variables.
    This creates a modified settings instance without affecting the cached singleton.

    Args:
        settings: Base Settings instance
        cli: CLI configuration overrides

    Returns:
        Settings instance with CLI overrides applied
    """
    # Create a copy of settings data
    data = settings.model_dump()

    # Apply runtime overrides
    if cli.verbose is not None:
        data["runtime"]["verbose"] = cli.verbose
    if cli.quiet is not None:
        data["runtime"]["quiet"] = cli.quiet
    if cli.headless is not None:
        data["runtime"]["headless"] = cli.headless
    if cli.log_level is not None:
        data["runtime"]["log_level"] = cli.log_level
    if cli.log_to_file is not None:
        data["runtime"]["log_to_file"] = cli.log_to_file
    if cli.log_file_path is not None:
        data["runtime"]["log_file_path"] = cli.log_file_path
    if cli.disable_interactive is not None:
        data["runtime"]["disable_interactive"] = cli.disable_interactive

    # Apply research overrides
    if cli.max_search_results is not None:
        data["MAX_SEARCH_RESULTS"] = cli.max_search_results
    if cli.concurrent_searches is not None:
        data["CONCURRENT_SEARCHES"] = cli.concurrent_searches
    if cli.tone is not None:
        data["research"]["tone"] = cli.tone
    if cli.max_iterations is not None:
        data["research"]["max_iterations"] = cli.max_iterations
    if cli.min_sources is not None:
        data["research"]["min_sources"] = cli.min_sources
    if cli.max_sources is not None:
        data["research"]["max_sources"] = cli.max_sources

    # Apply AI provider override
    if cli.ai_provider is not None:
        data["ai"]["primary"] = cli.ai_provider

    # Apply cache overrides
    if cli.cache_enabled is not None:
        data["cache"]["enabled"] = cli.cache_enabled
    if cli.cache_ttl is not None:
        data["cache"]["default_ttl"] = cli.cache_ttl

    # Create new Settings with overrides (bypass validation for path overrides)
    new_settings = Settings.model_validate(data)

    # Store path overrides as attributes (not in Pydantic model)
    if cli.output_dir is not None:
        new_settings._cli_output_dir = cli.output_dir
    if cli.cache_dir is not None:
        new_settings._cli_cache_dir = cli.cache_dir

    return new_settings


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

    # INT-002: Alpha Vantage API for financial fundamentals
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None

    # INT-003: FRED API for bond yield data
    FRED_API_KEY: Optional[SecretStr] = None

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
            "newsapi": self.NEWSAPI_KEY,
        }

        secret = provider_to_secret.get(provider.lower())
        return APIKeyPool.from_secret(secret, strategy)

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
    "ResearchConfig",
    # ARCH-004: Additional Config Classes
    "DatabaseConfig",
    "RedisConfig",
    "ServerConfig",
    "AgentConfig",
    "BrowserConfig",
    "GraphConfig",
    "DeepResearchConfig",
    "SearchConfig",
    "TelemetryConfig",
    "IntegrationKeysConfig",
    # Key Rotation (SEC-001)
    "KeyRotationStrategy",
    "APIKeyPool",
    # CLI Configuration (ARCH-001)
    "CLIConfig",
    "apply_cli_overrides",
    # Functions
    "get_settings",
    "get_profile",
    "is_production",
    "is_development",
    "clear_settings",
]
