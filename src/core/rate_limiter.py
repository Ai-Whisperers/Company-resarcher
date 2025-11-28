"""
Generic rate limiting utilities for external API calls.
"""

import asyncio
import time
from typing import Dict, Optional
from functools import wraps
from .logger import setup_logger

logger = setup_logger("rate_limiter")


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
        """
        Args:
            rate: Maximum requests per second (sustained rate)
            bucket_size: Maximum burst size (token bucket capacity)
            name: Name for logging purposes
        """
        self.rate = rate
        self.bucket_size = bucket_size
        self.name = name
        self.tokens = bucket_size
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait for a token (None = wait forever)

        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.monotonic()

        async with self._lock:
            while True:
                # Refill tokens based on elapsed time
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.bucket_size, self.tokens + elapsed * self.rate
                )
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    logger.debug(
                        f"[{self.name}] Token acquired, {self.tokens:.1f} remaining"
                    )
                    return True

                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.rate

                # Check timeout
                if timeout is not None:
                    elapsed_total = now - start_time
                    if elapsed_total + wait_time > timeout:
                        logger.warning(
                            f"[{self.name}] Rate limit timeout after {elapsed_total:.1f}s"
                        )
                        return False

                logger.debug(f"[{self.name}] Waiting {wait_time:.2f}s for token")
                await asyncio.sleep(min(wait_time, 0.1))  # Check periodically

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class RateLimiterRegistry:
    """
    Registry for managing multiple rate limiters.
    Ensures consistent rate limiting across tool instances.
    """

    _instance: Optional["RateLimiterRegistry"] = None
    _limiters: Dict[str, TokenBucketRateLimiter]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._limiters = {}
        return cls._instance

    def get_limiter(
        self,
        name: str,
        rate: float = 1.0,
        bucket_size: int = 10,
    ) -> TokenBucketRateLimiter:
        """
        Get or create a rate limiter by name.

        Args:
            name: Unique identifier for the limiter
            rate: Requests per second (only used on creation)
            bucket_size: Burst capacity (only used on creation)

        Returns:
            The rate limiter instance
        """
        if name not in self._limiters:
            self._limiters[name] = TokenBucketRateLimiter(
                rate=rate, bucket_size=bucket_size, name=name
            )
            logger.info(
                f"Created rate limiter '{name}': {rate}/s, burst={bucket_size}"
            )
        return self._limiters[name]

    def get_stats(self) -> Dict[str, dict]:
        """Get statistics for all rate limiters."""
        return {
            name: {
                "rate": limiter.rate,
                "bucket_size": limiter.bucket_size,
                "current_tokens": limiter.tokens,
            }
            for name, limiter in self._limiters.items()
        }


# Global registry instance
rate_limiter_registry = RateLimiterRegistry()


def rate_limited(
    limiter_name: str,
    rate: float = 1.0,
    bucket_size: int = 10,
):
    """
    Decorator for rate limiting async functions.

    Args:
        limiter_name: Name of the rate limiter to use
        rate: Requests per second
        bucket_size: Burst capacity
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = rate_limiter_registry.get_limiter(
                limiter_name, rate, bucket_size
            )
            async with limiter:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
