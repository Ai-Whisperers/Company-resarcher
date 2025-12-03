"""
Unified Rate Limiting Module.

Consolidates all rate limiting into a single system that integrates with api_limits.py
for provider-specific configurations.

Features:
- Token bucket algorithm for smooth rate limiting
- Daily limit tracking
- Provider-specific limits from api_limits.py
- Thread-safe and async-friendly
- Automatic configuration from environment variables
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from .api_limits import ProviderRateLimits

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"  # Smooth, allows bursts
    SLIDING_WINDOW = "sliding_window"  # More strict, better for APIs with strict limits


@dataclass
class RateLimitConfig:
    """Configuration for a rate limiter."""

    rate: float  # Requests per second (derived from requests_per_minute / 60)
    burst: int = 10  # Maximum burst size
    daily_limit: Optional[int] = None  # Daily request limit
    hourly_limit: Optional[int] = None  # Hourly request limit
    tokens_per_minute: Optional[int] = None  # Token limit (for AI providers)
    cooldown_seconds: float = 60.0  # Cooldown after rate limit hit
    max_retries: int = 3  # Max retries on rate limit

    @classmethod
    def from_provider_limits(cls, limits: "ProviderRateLimits") -> "RateLimitConfig":
        """Create config from ProviderRateLimits."""
        # Convert RPM to RPS
        rate = limits.requests_per_minute / 60.0
        return cls(
            rate=rate,
            burst=min(limits.concurrent_requests, 10),  # Burst = concurrent limit, max 10
            daily_limit=limits.requests_per_day if limits.requests_per_day < 100000 else None,
            hourly_limit=limits.requests_per_hour if limits.requests_per_hour < 10000 else None,
            tokens_per_minute=limits.tokens_per_minute if limits.tokens_per_minute > 0 else None,
            cooldown_seconds=limits.cooldown_seconds,
            max_retries=limits.max_retries,
        )


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling request rates.
    Allows bursts up to bucket_size, then limits to rate requests per second.
    """

    def __init__(
        self,
        rate: float,
        bucket_size: int = 10,
        name: str = "default",
    ):
        self.rate = rate
        self.bucket_size = bucket_size
        self.name = name
        self.tokens = float(bucket_size)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token, waiting if necessary.
        """
        start_time = time.monotonic()

        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(
                    float(self.bucket_size), self.tokens + elapsed * self.rate
                )
                self.last_update = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

                wait_time = (1.0 - self.tokens) / self.rate

                if timeout is not None:
                    elapsed_total = now - start_time
                    if elapsed_total + wait_time > timeout:
                        logger.warning(f"[{self.name}] Rate limit timeout")
                        return False

                if wait_time > 0:
                    await asyncio.sleep(wait_time)


class RateLimiterManager:
    """
    Centralized manager for rate limiters.

    Integrates with api_limits.py to automatically configure provider-specific limits.
    Provides a unified interface for all rate limiting needs across the application.

    Usage:
        # Get manager instance
        manager = get_rate_limiter_manager()

        # Acquire permission (auto-configures from api_limits if available)
        if await manager.acquire("openai"):
            # Make API call
            pass

        # Or get limiter directly for more control
        limiter = manager.get_limiter("tavily")
        await limiter.acquire()
    """

    _instance: Optional["RateLimiterManager"] = None
    _limiters: Dict[str, TokenBucketRateLimiter] = {}
    _configs: Dict[str, RateLimitConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._limiters = {}
            cls._instance._daily_usage = {}
            cls._instance._daily_reset = {}
            cls._instance._hourly_usage = {}
            cls._instance._hourly_reset = {}
            cls._instance._configs = {}
            cls._instance._initialized_providers = set()
        return cls._instance

    def _get_provider_config(self, name: str) -> Optional[RateLimitConfig]:
        """Get rate limit config from api_limits.py for a provider."""
        try:
            from ..config.api_limits import get_provider_limits
            limits = get_provider_limits(name)
            if limits:
                return RateLimitConfig.from_provider_limits(limits)
        except ImportError as e:
            logger.debug(f"api_limits module not available: {e}")
        except Exception as e:
            logger.warning(f"Error getting provider limits for {name}: {e}")
        return None

    def get_limiter(
        self, name: str, config: Optional[RateLimitConfig] = None
    ) -> TokenBucketRateLimiter:
        """
        Get or create a rate limiter for a provider.

        If no config provided, automatically loads from api_limits.py.
        Falls back to safe defaults if no configuration is available.
        """
        if name not in self._limiters:
            if config is None:
                # Try to get from api_limits.py first
                config = self._get_provider_config(name)

            if config is None:
                # Default fallback - conservative limits
                logger.debug(f"No config for {name}, using default (1 RPS, burst 5)")
                config = RateLimitConfig(rate=1.0, burst=5)

            self._limiters[name] = TokenBucketRateLimiter(
                rate=config.rate, bucket_size=config.burst, name=name
            )
            self._configs[name] = config

            # Initialize daily tracking if needed
            if config.daily_limit:
                self._daily_usage[name] = 0
                self._daily_reset[name] = time.time()

            # Initialize hourly tracking if needed
            if config.hourly_limit:
                self._hourly_usage[name] = 0
                self._hourly_reset[name] = time.time()

            self._initialized_providers.add(name)
            logger.debug(
                f"Initialized rate limiter for {name}: "
                f"{config.rate:.2f} RPS, burst {config.burst}, "
                f"daily={config.daily_limit}, hourly={config.hourly_limit}"
            )

        # Update config if explicitly provided (allow re-configuration)
        elif config:
            self._configs[name] = config
            # Update tracking if limits changed
            if config.daily_limit and name not in self._daily_usage:
                self._daily_usage[name] = 0
                self._daily_reset[name] = time.time()
            if config.hourly_limit and name not in self._hourly_usage:
                self._hourly_usage[name] = 0
                self._hourly_reset[name] = time.time()

        return self._limiters[name]

    async def acquire(
        self, name: str, tokens: int = 1, timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire permission to proceed.

        Checks in order:
        1. Daily limit
        2. Hourly limit
        3. Rate limit (token bucket)

        Args:
            name: Provider name (e.g., "openai", "tavily")
            tokens: Number of tokens to acquire (default 1)
            timeout: Maximum time to wait for rate limit

        Returns:
            True if acquired, False if limit exceeded
        """
        # Ensure limiter exists (auto-configures from api_limits if available)
        limiter = self.get_limiter(name)
        config = self._configs.get(name)

        # Check daily limit first
        if name in self._daily_usage:
            now = time.time()
            if now - self._daily_reset[name] > 86400:
                self._daily_usage[name] = 0
                self._daily_reset[name] = now
                logger.info(f"Daily limit reset for {name}")

            if config and config.daily_limit:
                if self._daily_usage[name] + tokens > config.daily_limit:
                    logger.warning(
                        f"Daily limit exceeded for {name}: "
                        f"{self._daily_usage[name]}/{config.daily_limit}"
                    )
                    return False

        # Check hourly limit
        if name in self._hourly_usage:
            now = time.time()
            if now - self._hourly_reset[name] > 3600:
                self._hourly_usage[name] = 0
                self._hourly_reset[name] = now

            if config and config.hourly_limit:
                if self._hourly_usage[name] + tokens > config.hourly_limit:
                    logger.warning(
                        f"Hourly limit exceeded for {name}: "
                        f"{self._hourly_usage[name]}/{config.hourly_limit}"
                    )
                    return False

        # Acquire from token bucket
        acquired = await limiter.acquire(timeout=timeout)

        if acquired:
            # Update usage counters
            if name in self._daily_usage:
                self._daily_usage[name] += tokens
            if name in self._hourly_usage:
                self._hourly_usage[name] += tokens

        return acquired

    def get_usage_stats(self, name: str) -> Dict[str, Any]:
        """Get current usage statistics for a provider."""
        config = self._configs.get(name)
        stats = {
            "provider": name,
            "configured": name in self._initialized_providers,
        }

        if config:
            stats["rate_per_second"] = config.rate
            stats["burst_size"] = config.burst

            if config.daily_limit:
                stats["daily_usage"] = self._daily_usage.get(name, 0)
                stats["daily_limit"] = config.daily_limit
                stats["daily_remaining"] = config.daily_limit - self._daily_usage.get(name, 0)

            if config.hourly_limit:
                stats["hourly_usage"] = self._hourly_usage.get(name, 0)
                stats["hourly_limit"] = config.hourly_limit
                stats["hourly_remaining"] = config.hourly_limit - self._hourly_usage.get(name, 0)

        return stats

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all configured providers."""
        return {name: self.get_usage_stats(name) for name in self._initialized_providers}

    def reset_provider(self, name: str) -> None:
        """Reset usage counters for a provider (useful for testing)."""
        if name in self._daily_usage:
            self._daily_usage[name] = 0
            self._daily_reset[name] = time.time()
        if name in self._hourly_usage:
            self._hourly_usage[name] = 0
            self._hourly_reset[name] = time.time()
        if name in self._limiters:
            limiter = self._limiters[name]
            limiter.tokens = float(limiter.bucket_size)
            limiter.last_update = time.monotonic()
        logger.info(f"Reset rate limiter for {name}")

    def reset_all(self) -> None:
        """Reset all rate limiters (useful for testing)."""
        for name in self._initialized_providers.copy():
            self.reset_provider(name)


# Global instance - use get_rate_limiter_manager() instead of direct access
_rate_limiter_manager: Optional[RateLimiterManager] = None


def get_rate_limiter_manager() -> RateLimiterManager:
    """Get the global rate limiter manager instance."""
    global _rate_limiter_manager
    if _rate_limiter_manager is None:
        _rate_limiter_manager = RateLimiterManager()
    return _rate_limiter_manager


# Backward compatibility alias
rate_limiter_manager = RateLimiterManager()
