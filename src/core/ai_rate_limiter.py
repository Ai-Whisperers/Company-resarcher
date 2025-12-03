"""
AI Rate Limit Handler (PERF-016).

Proactive rate limit tracking and balanced provider distribution
to prevent hitting rate limits and reduce log spam.
"""

import asyncio
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque

from .logger import setup_logger

logger = setup_logger("ai_rate_limiter")


@dataclass
class ProviderLimits:
    """Rate limits for a provider."""
    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int = 0
    concurrent_requests: int = 10


# Known rate limits for providers (conservative estimates)
# Note: Gemini limits updated for Google AI Ultra subscription
DEFAULT_PROVIDER_LIMITS = {
    "groq": ProviderLimits(
        requests_per_minute=30,
        requests_per_day=1000,
        tokens_per_minute=6000,
        concurrent_requests=5,
    ),
    "openai": ProviderLimits(
        requests_per_minute=60,
        requests_per_day=10000,
        tokens_per_minute=90000,
        concurrent_requests=10,
    ),
    "gemini": ProviderLimits(
        requests_per_minute=2000,  # Paid Tier 1: 2K RPM for gemini-2.0-flash
        requests_per_day=1000000,  # Unlimited, but set high cap
        tokens_per_minute=4000000,  # 4M TPM
        concurrent_requests=50,
    ),
    "anthropic": ProviderLimits(
        requests_per_minute=60,
        requests_per_day=10000,
        tokens_per_minute=100000,
        concurrent_requests=10,
    ),
}


@dataclass
class ProviderUsage:
    """Tracks usage for a provider."""
    name: str
    request_timestamps: deque = field(default_factory=lambda: deque(maxlen=1000))
    daily_requests: int = 0
    daily_reset_time: float = 0.0
    tokens_used_minute: int = 0
    minute_reset_time: float = 0.0
    rate_limited_until: Optional[float] = None
    consecutive_rate_limits: int = 0
    last_log_time: float = 0.0

    def __post_init__(self):
        if self.daily_reset_time == 0.0:
            self.daily_reset_time = time.time()
        if self.minute_reset_time == 0.0:
            self.minute_reset_time = time.time()


class AIRateLimiter:
    """
    Proactive AI rate limit tracking and management.

    Features:
    - Tracks request rates per provider
    - Throttles before hitting limits (at 80% threshold)
    - Balances load across providers
    - Reduces log spam for repeated rate limit messages
    - Parses retry-after headers for optimal wait times

    Usage:
        limiter = AIRateLimiter()

        # Check if should throttle
        if limiter.should_throttle("groq"):
            await limiter.wait_if_needed("groq")

        # Record request
        limiter.record_request("groq", tokens=1000)

        # Handle rate limit error
        limiter.record_rate_limit("groq", retry_after=60)

        # Get next best provider
        provider = limiter.get_best_provider(["groq", "openai", "gemini"])
    """

    # Throttle at 80% of limit
    THROTTLE_THRESHOLD = 0.8

    # Minimum wait when throttling
    MIN_THROTTLE_WAIT = 2.0

    # Log rate limit messages at most once per minute per provider
    LOG_INTERVAL_SECONDS = 60

    def __init__(
        self,
        provider_limits: Optional[Dict[str, ProviderLimits]] = None,
    ):
        self._limits = provider_limits or DEFAULT_PROVIDER_LIMITS.copy()
        self._usage: Dict[str, ProviderUsage] = {}
        self._lock = threading.Lock()

        # Initialize usage tracking for known providers
        for name in self._limits:
            self._usage[name] = ProviderUsage(name=name)

        logger.info(f"AI rate limiter initialized for providers: {list(self._limits.keys())}")

    def _get_usage(self, provider: str) -> ProviderUsage:
        """Get or create usage tracker for a provider."""
        if provider not in self._usage:
            self._usage[provider] = ProviderUsage(name=provider)
        return self._usage[provider]

    def _get_limits(self, provider: str) -> ProviderLimits:
        """Get limits for a provider."""
        return self._limits.get(
            provider,
            ProviderLimits(requests_per_minute=60, requests_per_day=10000)
        )

    def _requests_in_window(self, usage: ProviderUsage, window_seconds: float) -> int:
        """Count requests in a time window."""
        now = time.time()
        cutoff = now - window_seconds
        count = sum(1 for ts in usage.request_timestamps if ts >= cutoff)
        return count

    def _reset_daily_if_needed(self, usage: ProviderUsage) -> None:
        """Reset daily counter if 24 hours have passed."""
        now = time.time()
        if now - usage.daily_reset_time >= 86400:  # 24 hours
            usage.daily_requests = 0
            usage.daily_reset_time = now

    def _reset_minute_if_needed(self, usage: ProviderUsage) -> None:
        """Reset minute counter if 60 seconds have passed."""
        now = time.time()
        if now - usage.minute_reset_time >= 60:
            usage.tokens_used_minute = 0
            usage.minute_reset_time = now

    def should_throttle(self, provider: str) -> bool:
        """
        Check if requests to a provider should be throttled.

        Returns True if we're approaching the rate limit.
        """
        with self._lock:
            usage = self._get_usage(provider)
            limits = self._get_limits(provider)

            # Check if currently rate limited
            if usage.rate_limited_until:
                if time.time() < usage.rate_limited_until:
                    return True
                else:
                    usage.rate_limited_until = None
                    usage.consecutive_rate_limits = 0

            # Check requests per minute
            requests_last_minute = self._requests_in_window(usage, 60)
            threshold = limits.requests_per_minute * self.THROTTLE_THRESHOLD

            if requests_last_minute >= threshold:
                return True

            # Check daily requests
            self._reset_daily_if_needed(usage)
            daily_threshold = limits.requests_per_day * self.THROTTLE_THRESHOLD

            if usage.daily_requests >= daily_threshold:
                return True

            return False

    def get_throttle_wait_time(self, provider: str) -> float:
        """Get how long to wait before making another request."""
        with self._lock:
            usage = self._get_usage(provider)
            limits = self._get_limits(provider)

            # If rate limited, return time until reset
            if usage.rate_limited_until:
                remaining = usage.rate_limited_until - time.time()
                return max(0, remaining)

            # Calculate wait based on request rate
            requests_last_minute = self._requests_in_window(usage, 60)
            if requests_last_minute >= limits.requests_per_minute * self.THROTTLE_THRESHOLD:
                # Wait proportional to how far over threshold
                overage = requests_last_minute - (limits.requests_per_minute * self.THROTTLE_THRESHOLD)
                wait = max(self.MIN_THROTTLE_WAIT, overage * 2)
                return min(wait, 30.0)  # Cap at 30 seconds

            return 0

    async def wait_if_needed(self, provider: str) -> None:
        """Wait if provider should be throttled."""
        wait_time = self.get_throttle_wait_time(provider)
        if wait_time > 0:
            # Only log if not recently logged
            with self._lock:
                usage = self._get_usage(provider)
                now = time.time()
                if now - usage.last_log_time >= self.LOG_INTERVAL_SECONDS:
                    logger.info(f"Throttling {provider} for {wait_time:.1f}s to avoid rate limit")
                    usage.last_log_time = now

            await asyncio.sleep(wait_time)

    def record_request(self, provider: str, tokens: int = 0) -> None:
        """Record a request to a provider."""
        with self._lock:
            usage = self._get_usage(provider)

            usage.request_timestamps.append(time.time())
            usage.daily_requests += 1
            usage.tokens_used_minute += tokens

    def record_rate_limit(
        self,
        provider: str,
        error: Optional[Exception] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        """Record that a rate limit was hit."""
        with self._lock:
            usage = self._get_usage(provider)

            # Try to parse retry-after from error message
            if retry_after is None and error:
                retry_after = self._parse_retry_after(str(error))

            # Use default if not parsed
            if retry_after is None:
                # Increase wait time for consecutive rate limits
                base_wait = self._get_limits(provider).requests_per_minute / 60 * 2
                retry_after = base_wait * (usage.consecutive_rate_limits + 1)
                retry_after = min(retry_after, 120)  # Cap at 2 minutes

            usage.rate_limited_until = time.time() + retry_after
            usage.consecutive_rate_limits += 1

            # Only log if not recently logged
            now = time.time()
            if now - usage.last_log_time >= self.LOG_INTERVAL_SECONDS:
                logger.warning(
                    f"Rate limit hit for {provider}, "
                    f"waiting {retry_after:.1f}s "
                    f"(consecutive: {usage.consecutive_rate_limits})"
                )
                usage.last_log_time = now

    def _parse_retry_after(self, error_message: str) -> Optional[float]:
        """Try to parse retry-after from error message."""
        patterns = [
            r'retry after (\d+)',
            r'retry-after:\s*(\d+)',
            r'wait (\d+) seconds',
            r'try again in (\d+)',
        ]

        error_lower = error_message.lower()
        for pattern in patterns:
            match = re.search(pattern, error_lower)
            if match:
                return float(match.group(1))

        return None

    def get_best_provider(
        self,
        available_providers: List[str],
        exclude_rate_limited: bool = True,
    ) -> Optional[str]:
        """
        Get the best provider to use based on current usage.

        Balances load by selecting the least-used provider that isn't
        rate limited.

        Args:
            available_providers: List of available provider names
            exclude_rate_limited: Skip rate-limited providers

        Returns:
            Best provider name, or None if all are rate limited
        """
        with self._lock:
            candidates = []

            for provider in available_providers:
                usage = self._get_usage(provider)

                # Skip if rate limited
                if exclude_rate_limited:
                    if usage.rate_limited_until and time.time() < usage.rate_limited_until:
                        continue

                # Calculate usage score (lower is better)
                limits = self._get_limits(provider)
                requests_last_minute = self._requests_in_window(usage, 60)
                usage_ratio = requests_last_minute / limits.requests_per_minute

                candidates.append((provider, usage_ratio))

            if not candidates:
                return None

            # Sort by usage ratio (lowest first)
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

    def get_provider_status(self, provider: str) -> Dict[str, any]:
        """Get status of a provider."""
        with self._lock:
            usage = self._get_usage(provider)
            limits = self._get_limits(provider)

            self._reset_daily_if_needed(usage)
            self._reset_minute_if_needed(usage)

            requests_last_minute = self._requests_in_window(usage, 60)

            return {
                "provider": provider,
                "requests_last_minute": requests_last_minute,
                "daily_requests": usage.daily_requests,
                "rate_limited": usage.rate_limited_until is not None and time.time() < usage.rate_limited_until,
                "time_until_available": max(0, (usage.rate_limited_until or 0) - time.time()),
                "usage_ratio": requests_last_minute / limits.requests_per_minute,
                "should_throttle": self.should_throttle(provider),
            }

    def get_all_status(self) -> Dict[str, any]:
        """Get status of all providers."""
        return {
            provider: self.get_provider_status(provider)
            for provider in self._usage
        }

    def reset_provider(self, provider: str) -> None:
        """Reset usage tracking for a provider."""
        with self._lock:
            self._usage[provider] = ProviderUsage(name=provider)


# Global instance
_ai_rate_limiter: Optional[AIRateLimiter] = None
_ai_rate_limiter_lock = threading.Lock()


def get_ai_rate_limiter() -> AIRateLimiter:
    """Get or create the global AI rate limiter."""
    global _ai_rate_limiter
    if _ai_rate_limiter is None:
        with _ai_rate_limiter_lock:
            if _ai_rate_limiter is None:
                _ai_rate_limiter = AIRateLimiter()
    return _ai_rate_limiter
