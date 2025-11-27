"""
Rate-limited AI Client to prevent hitting API limits.
"""

from aiolimiter import AsyncLimiter
from .ai_client import BaseAIClient
from .logger import setup_logger

logger = setup_logger("rate_limited_client")


class RateLimitedAIClient(BaseAIClient):
    """
    Wrapper that enforces rate limits on AI API calls.
    Prevents 429 errors and ensures stable production usage.
    """

    def __init__(
        self,
        client: BaseAIClient,
        requests_per_minute: int = 10,
        requests_per_hour: int = 500,
    ):
        """
        Args:
            client: The underlying AI client to wrap
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
        """
        self.client = client
        # Create rate limiters
        self.minute_limiter = AsyncLimiter(requests_per_minute, 60)
        self.hour_limiter = AsyncLimiter(requests_per_hour, 3600)
        self.total_requests = 0

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
        # Wait for both minute and hour limits
        async with self.minute_limiter:
            async with self.hour_limiter:
                self.total_requests += 1
                logger.debug(
                    f"Making request #{self.total_requests} to "
                    f"{self.client.get_provider_name()}"
                )

                import time
                from .metrics import metrics

                start_time = time.time()
                provider = self.client.get_provider_name()

                try:
                    response = await self.client.generate(
                        prompt, system, temperature, max_tokens, response_format
                    )

                    duration = time.time() - start_time
                    metrics.record_ai_request(provider, "unknown", "success")
                    metrics.record_latency(provider, "unknown", duration)

                    return response
                except Exception as e:
                    metrics.record_ai_request(provider, "unknown", "error")
                    raise e

    def get_provider_name(self) -> str:
        """Pass through to underlying client."""
        return f"RateLimited<{self.client.get_provider_name()}>"

    def get_stats(self) -> dict:
        """Get rate limiting statistics."""
        return {
            "total_requests": self.total_requests,
            "minute_limit": self.minute_limiter.max_rate,
            "hour_limit": self.hour_limiter.max_rate,
        }
