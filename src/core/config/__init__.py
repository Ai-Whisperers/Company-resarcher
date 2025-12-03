"""
Centralized configuration module.

Exports:
    get_settings: Get the global settings instance.
    Settings: The main settings class.
    Profile: Application profile enum.
    AIConfig: AI configuration model.
    AIProviderConfig: AI provider configuration model.
    RuntimeConfig: Runtime configuration model.
    CacheConfig: Cache configuration model.
    ResearchConfig: Research configuration model.
    DatabaseConfig: Database configuration model.
    RedisConfig: Redis configuration model.
    ServerConfig: Server configuration model.
    AgentConfig: Agent configuration model.
    BrowserConfig: Browser configuration model.
    GraphConfig: Graph configuration model.
    DeepResearchConfig: Deep research configuration model.
    SearchConfig: Search configuration model.
    TelemetryConfig: Telemetry configuration model.
    IntegrationKeysConfig: Integration keys configuration model.
"""

from functools import lru_cache
from .settings import Settings
from .base import Profile, ProfileDefaults, APIKeyPool, KeyRotationStrategy
from .providers import AIConfig, AIProviderConfig, IntegrationKeysConfig
from .services import CacheConfig, SearchConfig, BrowserConfig
from .database import DatabaseConfig, RedisConfig, VaultConfig
from .server import ServerConfig
from .pipeline import ResearchConfig, GraphConfig, DeepResearchConfig, AgentConfig
from .telemetry import TelemetryConfig
from .runtime import RuntimeConfig, CLIConfig, apply_cli_overrides
from .defaults import *
from .api_limits import *
from .products import *


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


__all__ = [
    # Functions
    "get_settings",
    "get_profile",
    "is_production",
    "is_development",
    "clear_settings",
    "apply_cli_overrides",
    # Classes
    "Settings",
    "Profile",
    "ProfileDefaults",
    "APIKeyPool",
    "KeyRotationStrategy",
    "AIConfig",
    "AIProviderConfig",
    "IntegrationKeysConfig",
    "CacheConfig",
    "SearchConfig",
    "BrowserConfig",
    "DatabaseConfig",
    "RedisConfig",
    "VaultConfig",
    "ServerConfig",
    "ResearchConfig",
    "GraphConfig",
    "DeepResearchConfig",
    "AgentConfig",
    "TelemetryConfig",
    "RuntimeConfig",
    "CLIConfig",
    # Constants
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_REGION",
    "UNKNOWN_VALUE",
    "PROMPTS_DIR",
    "OUTPUT_DIR",
    "DB_PATH",
    "STATUS_PENDING",
    "STATUS_IN_PROGRESS",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "PHASE_INITIAL",
    "PHASE_DEEP_DIVE",
    "PHASE_SYNTHESIS",
    "PHASE_REVIEW",
    "AGENT_FINANCIAL",
    "AGENT_MARKET",
    "AGENT_COMPETITOR",
    "AGENT_BRAND",
    "AGENT_SALES",
]
