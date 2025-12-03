"""
Rate-limited AI Client to prevent hitting API limits.

Uses the unified rate limiting system from rate_limiting.py which integrates
with api_limits.py for provider-specific configuration.
"""

import time
from typing import Optional

from .. import BaseAIClient
from ...logging import setup_logger
from ...resilience.rate_limiting import get_rate_limiter_manager, RateLimitConfig

logger = setup_logger("rate_limited_client")


class RateLimitedAIClient(BaseAIClient):
    """
    Wrapper that enforces rate limits on AI API calls.

    Uses the unified RateLimiterManager which automatically loads
    provider-specific limits from api_limits.py.

    Features:
    - Automatic provider configuration from api_limits.py
    - Per-minute and per-hour rate limiting
    - Daily limit tracking
    - Metrics recording
    """

    def __init__(
        self,
        client: BaseAIClient,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
    ):
        """
        Args:
            client: The underlying AI client to wrap
            requests_per_minute: Override RPM (uses api_limits.py if not provided)
            requests_per_hour: Override RPH (uses api_limits.py if not provided)
        """
        self.client = client
        self.total_requests = 0
        self._rate_manager = get_rate_limiter_manager()

        # Get provider name for rate limiter lookup
        self._provider_name = client.get_provider_name()

        # If custom limits provided, configure the limiter
        if requests_per_minute is not None or requests_per_hour is not None:
            config = RateLimitConfig(
                rate=(requests_per_minute or 60) / 60.0,  # Convert to RPS
                burst=5,
                hourly_limit=requests_per_hour,
            )
            self._rate_manager.get_limiter(self._provider_name, config)
        else:
            # Ensure limiter exists (auto-configures from api_limits.py)
            self._rate_manager.get_limiter(self._provider_name)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "text",
    ) -> str:
        """
        Generate with rate limiting.
        Automatically throttles requests if limit is reached.
        """
        # Acquire rate limit permission (waits if needed)
        acquired = await self._rate_manager.acquire(
            self._provider_name,
            timeout=60.0  # Wait up to 60s for rate limit
        )

        if not acquired:
            from ...exceptions import AIRateLimitError
            raise AIRateLimitError(
                f"Rate limit exceeded for {self._provider_name}"
            )

        self.total_requests += 1
        logger.debug(
            f"Making request #{self.total_requests} to "
            f"{self.client.get_provider_name()}"
        )

        start_time = time.time()
        provider = self.client.get_provider_name()

        try:
            from ...metrics import metrics

            response = await self.client.generate(
                prompt, system, temperature, max_tokens, response_format
            )

            duration = time.time() - start_time
            metrics.record_ai_request(provider, "unknown", "success")
            metrics.record_latency(provider, "unknown", duration)

            return response
        except Exception:
            from ...metrics import metrics
            metrics.record_ai_request(provider, "unknown", "error")
            raise

    def get_provider_name(self) -> str:
        """Pass through to underlying client."""
        return f"RateLimited<{self.client.get_provider_name()}>"

    def get_stats(self) -> dict:
        """Get rate limiting statistics."""
        stats = self._rate_manager.get_usage_stats(self._provider_name)
        stats["total_requests"] = self.total_requests
        return stats
