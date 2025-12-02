"""
Configuration Models - DEBT-003

Pydantic models for all configuration objects, enabling:
- Type validation at runtime
- JSON serialization/deserialization
- Environment variable overrides
- Easy persistence and loading
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


# =============================================================================
# Browser Configuration
# =============================================================================


class BrowserConfig(BaseModel):
    """Configuration for browser/crawling operations."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout_ms: int = Field(default=30000, description="Page navigation timeout in ms")
    max_concurrent_pages: int = Field(default=5, description="Maximum concurrent browser pages")
    user_agent: Optional[str] = Field(default=None, description="Custom user agent string")
    viewport_width: int = Field(default=1920, description="Browser viewport width")
    viewport_height: int = Field(default=1080, description="Browser viewport height")
    ignore_https_errors: bool = Field(default=False, description="Ignore HTTPS certificate errors")
    proxy_server: Optional[str] = Field(default=None, description="Proxy server URL")
    enable_cache: bool = Field(default=True, description="Enable HTML caching")

    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """Create config from environment variables."""
        return cls(
            headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            timeout_ms=int(os.getenv("BROWSER_PAGE_TIMEOUT_MS", "30000")),
            max_concurrent_pages=int(os.getenv("BROWSER_MAX_CONCURRENT", "5")),
            user_agent=os.getenv("BROWSER_USER_AGENT"),
            viewport_width=int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1920")),
            viewport_height=int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080")),
            ignore_https_errors=os.getenv("BROWSER_IGNORE_HTTPS_ERRORS", "false").lower() == "true",
            proxy_server=os.getenv("BROWSER_PROXY"),
            enable_cache=os.getenv("ENABLE_HTML_CACHE", "true").lower() == "true",
        )


class CrawlerConfig(BaseModel):
    """Configuration for web crawling operations."""

    max_depth: int = Field(default=2, description="Maximum crawl depth")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    strategy: Literal["bfs", "dfs"] = Field(default="bfs", description="Crawling strategy")
    same_domain_only: bool = Field(default=True, description="Only crawl same domain")
    respect_robots_txt: bool = Field(default=True, description="Respect robots.txt")
    delay_between_requests_ms: int = Field(default=1000, description="Delay between requests")
    priority_keywords: List[str] = Field(
        default_factory=lambda: ["investor", "annual", "report", "financial"],
        description="Keywords for URL prioritization",
    )


# =============================================================================
# AI/LLM Configuration
# =============================================================================


class AIProviderConfig(BaseModel):
    """Configuration for a single AI provider."""

    name: str = Field(description="Provider name (openai, anthropic, google, groq)")
    api_key: Optional[str] = Field(default=None, description="API key (can also use env var)")
    api_key_env_var: Optional[str] = Field(default=None, description="Environment variable for API key")
    model: str = Field(description="Default model to use")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")
    max_tokens: int = Field(default=4096, description="Maximum tokens for generation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    timeout_seconds: int = Field(default=120, description="Request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment."""
        if self.api_key:
            return self.api_key
        if self.api_key_env_var:
            return os.getenv(self.api_key_env_var)
        return None


class AIConfig(BaseModel):
    """Configuration for AI/LLM operations."""

    primary_provider: str = Field(default="openai", description="Primary AI provider")
    fallback_providers: List[str] = Field(
        default_factory=lambda: ["anthropic", "google"],
        description="Fallback providers in order",
    )
    providers: Dict[str, AIProviderConfig] = Field(
        default_factory=dict,
        description="Provider configurations",
    )
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    @classmethod
    def default(cls) -> "AIConfig":
        """Create default AI configuration."""
        return cls(
            primary_provider="openai",
            fallback_providers=["anthropic", "google"],
            providers={
                "openai": AIProviderConfig(
                    name="openai",
                    api_key_env_var="OPENAI_API_KEY",
                    model="gpt-4o-mini",
                ),
                "anthropic": AIProviderConfig(
                    name="anthropic",
                    api_key_env_var="ANTHROPIC_API_KEY",
                    model="claude-3-haiku-20240307",
                ),
                "google": AIProviderConfig(
                    name="google",
                    api_key_env_var="GOOGLE_API_KEY",
                    model="gemini-1.5-flash",
                ),
            },
        )


# =============================================================================
# Research Configuration
# =============================================================================


class ResearchConfig(BaseModel):
    """Configuration for research operations."""

    max_sources: int = Field(default=20, description="Maximum sources per research")
    search_depth: Literal["quick", "moderate", "deep"] = Field(
        default="moderate",
        description="Research depth",
    )
    include_financials: bool = Field(default=True, description="Include financial data")
    include_news: bool = Field(default=True, description="Include recent news")
    include_social: bool = Field(default=False, description="Include social media")
    output_format: Literal["markdown", "json", "html"] = Field(
        default="markdown",
        description="Output format",
    )
    template: str = Field(default="comprehensive", description="Report template name")
    max_report_length: int = Field(default=50000, description="Maximum report length")


class SearchConfig(BaseModel):
    """Configuration for search operations."""

    primary_provider: str = Field(default="tavily", description="Primary search provider")
    fallback_providers: List[str] = Field(
        default_factory=lambda: ["duckduckgo"],
        description="Fallback search providers",
    )
    max_results: int = Field(default=10, description="Maximum results per query")
    safe_search: bool = Field(default=True, description="Enable safe search")
    timeout_seconds: int = Field(default=30, description="Search timeout")


# =============================================================================
# Storage Configuration
# =============================================================================


class CacheConfig(BaseModel):
    """Configuration for caching."""

    type: Literal["memory", "redis", "file"] = Field(default="memory", description="Cache type")
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    file_path: Optional[str] = Field(default=None, description="File cache directory")
    ttl_seconds: int = Field(default=3600, description="Default TTL")
    max_size_mb: int = Field(default=100, description="Maximum cache size in MB")


class DatabaseConfig(BaseModel):
    """Configuration for database connections."""

    type: Literal["sqlite", "postgresql"] = Field(default="sqlite", description="Database type")
    url: str = Field(default="sqlite:///data/research.db", description="Database URL")
    pool_size: int = Field(default=5, description="Connection pool size")
    echo_sql: bool = Field(default=False, description="Echo SQL statements")


class VaultConfig(BaseModel):
    """Configuration for secure storage (vault)."""

    path: str = Field(default="data/vault", description="Vault storage path")
    encryption_enabled: bool = Field(default=False, description="Enable encryption")
    encryption_key_env_var: str = Field(
        default="VAULT_ENCRYPTION_KEY",
        description="Environment variable for encryption key",
    )


# =============================================================================
# Main Application Configuration
# =============================================================================


class AppConfig(BaseSettings):
    """
    Main application configuration.

    Combines all sub-configurations into a single root config.
    Supports loading from environment and JSON files.
    """

    # Application metadata
    app_name: str = Field(default="Company Researcher", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Sub-configurations
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    ai: AIConfig = Field(default_factory=AIConfig.default)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    vault: VaultConfig = Field(default_factory=VaultConfig)

    class Config:
        env_prefix = "APP_"
        env_nested_delimiter = "__"

    # ==========================================================================
    # Serialization Methods
    # ==========================================================================

    def to_json(self, indent: int = 2) -> str:
        """Serialize config to JSON string."""
        return self.model_dump_json(indent=indent)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return self.model_dump()

    def save(self, path: str) -> None:
        """Save config to JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_json())

    @classmethod
    def load(cls, path: str) -> "AppConfig":
        """Load config from JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        data = json.loads(file_path.read_text())
        return cls(**data)

    @classmethod
    def load_or_default(cls, path: str) -> "AppConfig":
        """Load config from file or return default."""
        try:
            return cls.load(path)
        except FileNotFoundError:
            return cls()

    # ==========================================================================
    # Factory Methods
    # ==========================================================================

    @classmethod
    def development(cls) -> "AppConfig":
        """Create development configuration."""
        return cls(
            environment="development",
            debug=True,
            log_level="DEBUG",
            browser=BrowserConfig(headless=False),
        )

    @classmethod
    def production(cls) -> "AppConfig":
        """Create production configuration."""
        return cls(
            environment="production",
            debug=False,
            log_level="WARNING",
            browser=BrowserConfig(headless=True),
            cache=CacheConfig(type="redis"),
        )


# =============================================================================
# Global Config Instance
# =============================================================================


_app_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global application configuration."""
    global _app_config
    if _app_config is None:
        config_path = os.getenv("APP_CONFIG_PATH", "config.json")
        _app_config = AppConfig.load_or_default(config_path)
    return _app_config


def set_config(config: AppConfig) -> None:
    """Set the global application configuration."""
    global _app_config
    _app_config = config


def reset_config() -> None:
    """Reset the global configuration to default."""
    global _app_config
    _app_config = None
