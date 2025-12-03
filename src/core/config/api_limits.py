"""
API Rate Limits Configuration.

Centralized configuration for all API rate limits, making static values configurable
via environment variables with sensible defaults based on documented provider limits.

This module provides:
- Documented rate limits for all API providers (AI, Search, Financial, etc.)
- Environment variable overrides for all limits
- Helper functions to get limits for any provider
- Integration with the main config system

Rate Limit Sources (as of December 2024):
- OpenAI: https://platform.openai.com/docs/guides/rate-limits
- Anthropic: https://docs.claude.com/en/api/rate-limits
- Google Gemini: https://ai.google.dev/gemini-api/docs/rate-limits
- Groq: https://console.groq.com/docs/rate-limits
- Tavily: https://docs.tavily.com/documentation/rate-limits
- Serper: https://serper.dev/
- Brave: https://brave.com/search/api/
- Jina: https://jina.ai/reader/
- Alpha Vantage: https://www.alphavantage.co/premium/
- FRED: https://fred.stlouisfed.org/docs/api/fred/errors.html
- NewsAPI: https://newsapi.org/pricing

Usage:
    from src.core.config.api_limits import get_provider_limits, APILimitsConfig, get_api_limits_config

    # Get limits for a specific provider
    limits = get_provider_limits("openai")
    print(f"OpenAI RPM: {limits.requests_per_minute}")

    # Get all configured limits
    config = get_api_limits_config()
    print(config.ai_providers["gemini"].requests_per_minute)
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Dict, List, Optional, Any


class ProviderTier(str, Enum):
    """API provider pricing/access tiers."""
    FREE = "free"
    TIER_1 = "tier_1"  # Basic paid tier
    TIER_2 = "tier_2"  # Standard paid tier
    TIER_3 = "tier_3"  # Premium paid tier
    TIER_4 = "tier_4"  # Enterprise tier
    ENTERPRISE = "enterprise"


@dataclass
class ProviderRateLimits:
    """Rate limits for a single API provider."""

    # Request limits
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    requests_per_day: int = 86400

    # Token limits (for AI providers)
    tokens_per_minute: int = 0
    tokens_per_day: int = 0

    # Concurrency limits
    concurrent_requests: int = 10

    # Cooldown/retry configuration
    cooldown_seconds: float = 60.0
    retry_after_default: float = 60.0
    max_retries: int = 3

    # Provider metadata
    tier: ProviderTier = ProviderTier.FREE
    priority: int = 5  # Lower = higher priority (1-10)
    cost_per_request: float = 0.0  # USD
    free_quota_monthly: int = 0  # Monthly free requests

    # Notes about the provider
    notes: str = ""


# =============================================================================
# AI PROVIDER LIMITS
# =============================================================================

def _get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable with default."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    """Get float from environment variable with default."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_openai_limits() -> ProviderRateLimits:
    """
    OpenAI API rate limits.

    Tier system based on cumulative spend:
    - Tier 1: $5 spent - 500 RPM, 30K TPM
    - Tier 2: $50 spent - 5,000 RPM, 90K TPM
    - Tier 3: $100 spent - 5,000 RPM, 150K TPM
    - Tier 4: $250 spent - 10,000 RPM, 300K TPM
    - Tier 5: $1,000 spent - 10,000 RPM, 10M TPM

    Source: https://platform.openai.com/docs/guides/rate-limits
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("OPENAI_RPM", 60),
        requests_per_hour=_get_env_int("OPENAI_RPH", 3600),
        requests_per_day=_get_env_int("OPENAI_RPD", 10000),
        tokens_per_minute=_get_env_int("OPENAI_TPM", 90000),
        tokens_per_day=_get_env_int("OPENAI_TPD", 10000000),
        concurrent_requests=_get_env_int("OPENAI_CONCURRENT", 10),
        cooldown_seconds=_get_env_float("OPENAI_COOLDOWN", 60.0),
        retry_after_default=_get_env_float("OPENAI_RETRY_AFTER", 60.0),
        max_retries=_get_env_int("OPENAI_MAX_RETRIES", 3),
        tier=ProviderTier.TIER_2,
        priority=2,
        cost_per_request=0.0,  # Token-based pricing
        notes="Tier 2 defaults. Adjust based on your account tier."
    )


def get_anthropic_limits() -> ProviderRateLimits:
    """
    Anthropic Claude API rate limits.

    Tier system based on usage:
    - Tier 1: 50 RPM, 40K TPM, 1M TPD
    - Tier 2: 100 RPM, 80K TPM, 2.5M TPD
    - Tier 3: 200 RPM, 160K TPM, 5M TPD
    - Tier 4: 500 RPM, 400K TPM, 10M TPD

    Source: https://docs.claude.com/en/api/rate-limits
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("ANTHROPIC_RPM", 60),
        requests_per_hour=_get_env_int("ANTHROPIC_RPH", 3600),
        requests_per_day=_get_env_int("ANTHROPIC_RPD", 10000),
        tokens_per_minute=_get_env_int("ANTHROPIC_TPM", 100000),
        tokens_per_day=_get_env_int("ANTHROPIC_TPD", 5000000),
        concurrent_requests=_get_env_int("ANTHROPIC_CONCURRENT", 10),
        cooldown_seconds=_get_env_float("ANTHROPIC_COOLDOWN", 60.0),
        retry_after_default=_get_env_float("ANTHROPIC_RETRY_AFTER", 60.0),
        max_retries=_get_env_int("ANTHROPIC_MAX_RETRIES", 3),
        tier=ProviderTier.TIER_2,
        priority=2,
        cost_per_request=0.0,
        notes="Tier 2 defaults. Check console.anthropic.com for your tier."
    )


def get_gemini_limits() -> ProviderRateLimits:
    """
    Google Gemini API rate limits.

    Free tier:
    - Gemini 2.5 Pro: 5 RPM, 250K TPM, 100 RPD
    - Gemini 2.5 Flash: 10 RPM, 250K TPM, 250 RPD

    Paid Tier 1 (billing enabled):
    - 300 RPM, 1M TPM, 1K RPD

    Paid Tier 2 ($250 spend + 30 days):
    - 1,000 RPM, 2M TPM, 10K RPD

    Source: https://ai.google.dev/gemini-api/docs/rate-limits
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("GEMINI_RPM", 2000),  # Paid Tier 1 default
        requests_per_hour=_get_env_int("GEMINI_RPH", 60000),
        requests_per_day=_get_env_int("GEMINI_RPD", 1000000),  # Effectively unlimited
        tokens_per_minute=_get_env_int("GEMINI_TPM", 4000000),
        tokens_per_day=_get_env_int("GEMINI_TPD", 100000000),
        concurrent_requests=_get_env_int("GEMINI_CONCURRENT", 50),
        cooldown_seconds=_get_env_float("GEMINI_COOLDOWN", 60.0),
        retry_after_default=_get_env_float("GEMINI_RETRY_AFTER", 60.0),
        max_retries=_get_env_int("GEMINI_MAX_RETRIES", 3),
        tier=ProviderTier.TIER_1,
        priority=1,  # High priority due to generous limits
        cost_per_request=0.0,
        free_quota_monthly=0,  # Varies by model
        notes="Paid Tier 1 defaults. Free tier has much lower limits."
    )


def get_groq_limits() -> ProviderRateLimits:
    """
    Groq API rate limits.

    Free tier:
    - ~30 RPM, 6K TPM (varies by model)

    Developer tier:
    - Up to 10x rate limits

    Source: https://console.groq.com/docs/rate-limits
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("GROQ_RPM", 30),
        requests_per_hour=_get_env_int("GROQ_RPH", 1000),
        requests_per_day=_get_env_int("GROQ_RPD", 1000),
        tokens_per_minute=_get_env_int("GROQ_TPM", 6000),
        tokens_per_day=_get_env_int("GROQ_TPD", 1000000),
        concurrent_requests=_get_env_int("GROQ_CONCURRENT", 5),
        cooldown_seconds=_get_env_float("GROQ_COOLDOWN", 60.0),
        retry_after_default=_get_env_float("GROQ_RETRY_AFTER", 60.0),
        max_retries=_get_env_int("GROQ_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=3,
        cost_per_request=0.0,
        notes="Free tier defaults. Very fast inference but limited rate."
    )


# =============================================================================
# SEARCH PROVIDER LIMITS
# =============================================================================

def get_tavily_limits() -> ProviderRateLimits:
    """
    Tavily Search API limits.

    Free: 1,000 requests/month
    Pay-as-you-go: $0.008/request ($8/1K)
    Max: 100 RPM (docs), 10 concurrent

    Source: https://docs.tavily.com/documentation/rate-limits
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("TAVILY_RPM", 100),  # Increased from 60
        requests_per_hour=_get_env_int("TAVILY_RPH", 1000),
        requests_per_day=_get_env_int("TAVILY_RPD", 1000),
        concurrent_requests=_get_env_int("TAVILY_CONCURRENT", 10),  # Increased from 5
        cooldown_seconds=_get_env_float("TAVILY_COOLDOWN", 30.0),
        max_retries=_get_env_int("TAVILY_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=5,  # Lower priority due to cost
        cost_per_request=0.008,
        free_quota_monthly=1000,
        notes="1,000 free/month. Excellent AI-optimized results."
    )


def get_serper_limits() -> ProviderRateLimits:
    """
    Serper.dev API limits (Google Search API).

    Free: 2,500 queries on signup
    Paid: Credit-based, up to 300 queries/SECOND (18,000 RPM!)
    Max: Ultimate plan allows 300 QPS = 18,000 RPM

    Source: https://serper.dev/
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("SERPER_RPM", 3000),  # 50 QPS conservative (max 18,000)
        requests_per_hour=_get_env_int("SERPER_RPH", 50000),
        requests_per_day=_get_env_int("SERPER_RPD", 100000),
        concurrent_requests=_get_env_int("SERPER_CONCURRENT", 50),  # Increased from 10
        cooldown_seconds=_get_env_float("SERPER_COOLDOWN", 1.0),
        max_retries=_get_env_int("SERPER_MAX_RETRIES", 3),
        tier=ProviderTier.TIER_1,
        priority=4,
        cost_per_request=0.001,  # ~$50/50K = $0.001
        free_quota_monthly=2500,  # One-time signup bonus
        notes="FASTEST: Up to 300 QPS. 2,500 free on signup."
    )


def get_brave_limits() -> ProviderRateLimits:
    """
    Brave Search API limits.

    Free: 2,000 requests/month, 1 request/second
    Paid: $3-5 per 1,000 searches

    Source: https://brave.com/search/api/
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("BRAVE_RPM", 60),  # 1 req/sec = 60 RPM
        requests_per_hour=_get_env_int("BRAVE_RPH", 500),
        requests_per_day=_get_env_int("BRAVE_RPD", 2000),
        concurrent_requests=_get_env_int("BRAVE_CONCURRENT", 5),  # Increased from 1
        cooldown_seconds=_get_env_float("BRAVE_COOLDOWN", 60.0),
        max_retries=_get_env_int("BRAVE_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=3,
        cost_per_request=0.004,  # ~$4/1K
        free_quota_monthly=2000,
        notes="2,000 free/month. Independent index (not Google/Bing)."
    )


def get_bing_limits() -> ProviderRateLimits:
    """
    Bing Search API limits (Azure).

    NOTE: Bing Search API is being retired August 11, 2025.
    Replacement: "Grounding with Bing Search" (40-483% more expensive)

    Source: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/search-api/
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("BING_RPM", 60),
        requests_per_hour=_get_env_int("BING_RPH", 1000),
        requests_per_day=_get_env_int("BING_RPD", 1000),
        concurrent_requests=_get_env_int("BING_CONCURRENT", 5),
        cooldown_seconds=_get_env_float("BING_COOLDOWN", 60.0),
        max_retries=_get_env_int("BING_MAX_RETRIES", 3),
        tier=ProviderTier.TIER_1,
        priority=4,
        cost_per_request=0.025,  # $25/1K
        free_quota_monthly=1000,
        notes="RETIRING Aug 2025. 1K free/month via Azure."
    )


def get_jina_limits() -> ProviderRateLimits:
    """
    Jina AI Reader/Search API limits.

    Free: 20 RPM (no API key), 200 RPM (with free key)
    Premium: 2,000 RPM, 20 concurrent
    New keys: 10M free tokens

    Source: https://jina.ai/reader/
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("JINA_RPM", 200),  # With API key (2000 premium)
        requests_per_hour=_get_env_int("JINA_RPH", 10000),
        requests_per_day=_get_env_int("JINA_RPD", 100000),
        concurrent_requests=_get_env_int("JINA_CONCURRENT", 10),  # Increased from 5 (max 20)
        cooldown_seconds=_get_env_float("JINA_COOLDOWN", 30.0),
        max_retries=_get_env_int("JINA_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=2,
        cost_per_request=0.0,
        free_quota_monthly=0,  # Token-based
        notes="200 RPM free (2K premium). 10M free tokens."
    )


def get_duckduckgo_limits() -> ProviderRateLimits:
    """
    DuckDuckGo search limits.

    Free: Unlimited (no official API, uses scraping)
    Rate limited but generous for normal use.

    Note: Slower than other providers (can take 30-60s)
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("DUCKDUCKGO_RPM", 30),
        requests_per_hour=_get_env_int("DUCKDUCKGO_RPH", 500),
        requests_per_day=_get_env_int("DUCKDUCKGO_RPD", 5000),
        concurrent_requests=_get_env_int("DUCKDUCKGO_CONCURRENT", 3),
        cooldown_seconds=_get_env_float("DUCKDUCKGO_COOLDOWN", 60.0),
        max_retries=_get_env_int("DUCKDUCKGO_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=1,  # Highest priority (free, always available)
        cost_per_request=0.0,
        notes="Free but can be slow (30-60s timeout). No API key needed."
    )


def get_langsearch_limits() -> ProviderRateLimits:
    """
    LangSearch API limits.

    Free AI-optimized search with API key required.
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("LANGSEARCH_RPM", 30),
        requests_per_hour=_get_env_int("LANGSEARCH_RPH", 500),
        requests_per_day=_get_env_int("LANGSEARCH_RPD", 5000),
        concurrent_requests=_get_env_int("LANGSEARCH_CONCURRENT", 5),
        cooldown_seconds=_get_env_float("LANGSEARCH_COOLDOWN", 60.0),
        max_retries=_get_env_int("LANGSEARCH_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=3,
        cost_per_request=0.0,
        notes="Free AI-optimized search. Requires API key."
    )


# =============================================================================
# FINANCIAL DATA PROVIDER LIMITS
# =============================================================================

def get_alpha_vantage_limits() -> ProviderRateLimits:
    """
    Alpha Vantage API limits.

    Free tier: 25 requests/day, 5 requests/minute
    Premium: Unlimited daily requests

    Source: https://www.alphavantage.co/premium/
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("ALPHA_VANTAGE_RPM", 5),
        requests_per_hour=_get_env_int("ALPHA_VANTAGE_RPH", 25),
        requests_per_day=_get_env_int("ALPHA_VANTAGE_RPD", 25),
        concurrent_requests=_get_env_int("ALPHA_VANTAGE_CONCURRENT", 1),
        cooldown_seconds=_get_env_float("ALPHA_VANTAGE_COOLDOWN", 60.0),
        max_retries=_get_env_int("ALPHA_VANTAGE_MAX_RETRIES", 2),
        tier=ProviderTier.FREE,
        priority=5,
        cost_per_request=0.0,
        free_quota_monthly=750,  # 25 * 30
        notes="25 requests/day free. Licensed by NASDAQ."
    )


def get_fred_limits() -> ProviderRateLimits:
    """
    FRED (Federal Reserve Economic Data) API limits.

    Free: 120 requests/minute, unlimited daily

    Source: https://fred.stlouisfed.org/docs/api/fred/errors.html
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("FRED_RPM", 120),
        requests_per_hour=_get_env_int("FRED_RPH", 7200),
        requests_per_day=_get_env_int("FRED_RPD", 100000),  # Effectively unlimited
        concurrent_requests=_get_env_int("FRED_CONCURRENT", 10),
        cooldown_seconds=_get_env_float("FRED_COOLDOWN", 60.0),
        max_retries=_get_env_int("FRED_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=1,
        cost_per_request=0.0,
        notes="Free. 765,000+ economic time series from St. Louis Fed."
    )


def get_newsapi_limits() -> ProviderRateLimits:
    """
    NewsAPI.org rate limits.

    Free: Limited requests, 24-hour delay on results
    Paid: $449/month for production use

    Source: https://newsapi.org/pricing
    """
    return ProviderRateLimits(
        requests_per_minute=_get_env_int("NEWSAPI_RPM", 10),
        requests_per_hour=_get_env_int("NEWSAPI_RPH", 100),
        requests_per_day=_get_env_int("NEWSAPI_RPD", 100),
        concurrent_requests=_get_env_int("NEWSAPI_CONCURRENT", 2),
        cooldown_seconds=_get_env_float("NEWSAPI_COOLDOWN", 60.0),
        max_retries=_get_env_int("NEWSAPI_MAX_RETRIES", 3),
        tier=ProviderTier.FREE,
        priority=4,
        cost_per_request=0.0,
        notes="Free tier has 24-hour delay. Good for development."
    )


# =============================================================================
# GLOBAL SEARCH CONFIGURATION
# =============================================================================

def get_search_manager_limits() -> Dict[str, Any]:
    """
    Get global search manager configuration.

    These values apply across all search providers.
    """
    return {
        "requests_per_minute": _get_env_int("SEARCH_RATE_LIMIT_PER_MIN", 30),
        "cooldown_seconds": _get_env_float("SEARCH_COOLDOWN_SECONDS", 60.0),
        "max_retries": _get_env_int("SEARCH_MAX_RETRIES", 3),
        "base_backoff_seconds": _get_env_float("SEARCH_BASE_BACKOFF", 2.0),
        "timeout_seconds": _get_env_int("SEARCH_TIMEOUT_SECONDS", 30),
        "parallel_timeout_seconds": _get_env_float("SEARCH_PARALLEL_TIMEOUT", 30.0),
        "results_per_page": _get_env_int("SEARCH_RESULTS_PER_PAGE", 10),
        "max_pages": _get_env_int("SEARCH_MAX_PAGES", 3),
        "page_delay_seconds": _get_env_float("SEARCH_PAGE_DELAY", 1.0),
    }


# =============================================================================
# AGGREGATED CONFIG
# =============================================================================

@dataclass
class APILimitsConfig:
    """Complete API limits configuration for all providers."""

    # AI Providers
    ai_providers: Dict[str, ProviderRateLimits] = field(default_factory=dict)

    # Search Providers
    search_providers: Dict[str, ProviderRateLimits] = field(default_factory=dict)

    # Financial Data Providers
    financial_providers: Dict[str, ProviderRateLimits] = field(default_factory=dict)

    # Global Search Settings
    search_manager: Dict[str, Any] = field(default_factory=dict)

    def get_provider(self, name: str) -> Optional[ProviderRateLimits]:
        """Get limits for any provider by name."""
        name_lower = name.lower()

        # Check all provider dicts
        for provider_dict in [self.ai_providers, self.search_providers, self.financial_providers]:
            if name_lower in provider_dict:
                return provider_dict[name_lower]

        return None

    def get_ai_provider(self, name: str) -> Optional[ProviderRateLimits]:
        """Get limits for an AI provider."""
        return self.ai_providers.get(name.lower())

    def get_search_provider(self, name: str) -> Optional[ProviderRateLimits]:
        """Get limits for a search provider."""
        return self.search_providers.get(name.lower())

    def list_providers(self) -> Dict[str, List[str]]:
        """List all configured providers by category."""
        return {
            "ai": list(self.ai_providers.keys()),
            "search": list(self.search_providers.keys()),
            "financial": list(self.financial_providers.keys()),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        def limits_to_dict(limits: ProviderRateLimits) -> Dict[str, Any]:
            return {
                "requests_per_minute": limits.requests_per_minute,
                "requests_per_hour": limits.requests_per_hour,
                "requests_per_day": limits.requests_per_day,
                "tokens_per_minute": limits.tokens_per_minute,
                "tokens_per_day": limits.tokens_per_day,
                "concurrent_requests": limits.concurrent_requests,
                "cooldown_seconds": limits.cooldown_seconds,
                "max_retries": limits.max_retries,
                "tier": limits.tier.value,
                "priority": limits.priority,
                "cost_per_request": limits.cost_per_request,
                "free_quota_monthly": limits.free_quota_monthly,
                "notes": limits.notes,
            }

        return {
            "ai_providers": {k: limits_to_dict(v) for k, v in self.ai_providers.items()},
            "search_providers": {k: limits_to_dict(v) for k, v in self.search_providers.items()},
            "financial_providers": {k: limits_to_dict(v) for k, v in self.financial_providers.items()},
            "search_manager": self.search_manager,
        }


@lru_cache()
def get_api_limits_config() -> APILimitsConfig:
    """
    Get the complete API limits configuration.

    Returns cached config with all providers initialized from environment
    variables or defaults.
    """
    return APILimitsConfig(
        ai_providers={
            "openai": get_openai_limits(),
            "anthropic": get_anthropic_limits(),
            "gemini": get_gemini_limits(),
            "groq": get_groq_limits(),
        },
        search_providers={
            "duckduckgo": get_duckduckgo_limits(),
            "jina": get_jina_limits(),
            "langsearch": get_langsearch_limits(),
            "brave": get_brave_limits(),
            "serper": get_serper_limits(),
            "bing": get_bing_limits(),
            "tavily": get_tavily_limits(),
        },
        financial_providers={
            "alpha_vantage": get_alpha_vantage_limits(),
            "fred": get_fred_limits(),
            "newsapi": get_newsapi_limits(),
        },
        search_manager=get_search_manager_limits(),
    )


def get_provider_limits(provider_name: str) -> Optional[ProviderRateLimits]:
    """
    Get rate limits for a specific provider.

    Args:
        provider_name: Name of the provider (case-insensitive)

    Returns:
        ProviderRateLimits or None if provider not found

    Example:
        limits = get_provider_limits("openai")
        print(f"OpenAI allows {limits.requests_per_minute} RPM")
    """
    config = get_api_limits_config()
    return config.get_provider(provider_name)


def clear_limits_cache():
    """Clear the cached limits configuration (for testing)."""
    get_api_limits_config.cache_clear()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "ProviderTier",
    "ProviderRateLimits",
    "APILimitsConfig",
    # Functions - Individual providers
    "get_openai_limits",
    "get_anthropic_limits",
    "get_gemini_limits",
    "get_groq_limits",
    "get_tavily_limits",
    "get_serper_limits",
    "get_brave_limits",
    "get_bing_limits",
    "get_jina_limits",
    "get_duckduckgo_limits",
    "get_langsearch_limits",
    "get_alpha_vantage_limits",
    "get_fred_limits",
    "get_newsapi_limits",
    # Functions - Aggregated
    "get_search_manager_limits",
    "get_api_limits_config",
    "get_provider_limits",
    "clear_limits_cache",
]
