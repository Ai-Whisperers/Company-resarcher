"""
Unified HTTP Client Module.

Provides a centralized, async HTTP client with:
- Connection pooling (session reuse)
- Automatic retry with exponential backoff
- Rate limiting integration
- Consistent timeout handling
- Request/response logging

Usage:
    from src.infrastructure.network.http_client import get_http_client, http_get, http_post

    # Simple usage
    response = await http_get("https://api.example.com/data")

    # With client instance for more control
    client = get_http_client()
    response = await client.get("https://api.example.com/data", headers={"X-API-Key": "..."})

    # With rate limiting
    response = await client.get(url, rate_limit_key="tavily")
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class HTTPClientConfig:
    """Configuration for the HTTP client."""

    # Timeout settings
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    retry_on_status: tuple = (429, 500, 502, 503, 504)

    # Connection pool settings
    pool_size: int = 100
    keepalive_timeout: float = 30.0

    # Default headers
    default_headers: dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": "CompanyResearcher/1.0",
            "Accept": "application/json",
        }
    )


class HTTPClient:
    """
    Unified async HTTP client with connection pooling and retry logic.

    Features:
    - Shared session for connection reuse
    - Automatic retry with exponential backoff
    - Rate limiting integration
    - Detailed logging and metrics
    """

    _instance: Optional["HTTPClient"] = None
    _session: Optional[aiohttp.ClientSession] = None
    _config: HTTPClientConfig
    # Typed as Any to avoid circular import issues or complex types
    _rate_manager: Any
    _request_count: int

    def __new__(cls, config: Optional[HTTPClientConfig] = None) -> "HTTPClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = config or HTTPClientConfig()
            cls._instance._session = None
            # Import here to avoid circular imports
            from src.infrastructure.resilience.rate_limiting import get_rate_limiter_manager

            cls._instance._rate_manager = get_rate_limiter_manager()
            cls._instance._request_count = 0
        return cls._instance

    @property
    def config(self) -> HTTPClientConfig:
        return self._config

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the shared session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                connect=self._config.connect_timeout,
                sock_read=self._config.read_timeout,
                total=self._config.total_timeout,
            )
            connector = aiohttp.TCPConnector(
                limit=self._config.pool_size,
                keepalive_timeout=self._config.keepalive_timeout,
                enable_cleanup_closed=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self._config.default_headers,
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Execute request with retry logic."""
        session = await self._get_session()
        last_exception: Optional[Exception] = None

        # Apply rate limiting if key provided
        if rate_limit_key:
            acquired = await self._rate_manager.acquire(rate_limit_key, timeout=30.0)
            if not acquired:
                raise RateLimitExceededError(
                    f"Rate limit exceeded for {rate_limit_key}"
                )

        for attempt in range(self._config.max_retries + 1):
            try:
                self._request_count += 1
                start_time = time.time()

                response = await session.request(method, url, **kwargs)

                duration = time.time() - start_time
                logger.debug(
                    f"HTTP {method} {url} -> {response.status} " f"({duration:.2f}s)"
                )

                # Check if we should retry on this status
                if response.status in self._config.retry_on_status:
                    if attempt < self._config.max_retries:
                        retry_after = self._get_retry_after(response, attempt)
                        logger.warning(
                            f"HTTP {response.status} from {url}, retrying in "
                            f"{retry_after:.1f}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(retry_after)
                        continue

                return response

            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"HTTP error for {url}: {e}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"HTTP request failed after {attempt + 1} attempts: " f"{e}"
                    )
                    raise

            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Timeout for {url}, retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"HTTP request timed out after {attempt + 1} attempts")
                    raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")

    def _get_retry_after(self, response: aiohttp.ClientResponse, attempt: int) -> float:
        """Get retry delay from response headers or calculate backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self._calculate_backoff(attempt)

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self._config.retry_base_delay * (2**attempt)
        # Add jitter (10-20% random variation)
        import random

        jitter = delay * random.uniform(0.1, 0.2)
        return min(delay + jitter, self._config.retry_max_delay)

    async def get(
        self,
        url: str,
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Perform GET request."""
        return await self._request_with_retry("GET", url, rate_limit_key, **kwargs)

    async def post(
        self,
        url: str,
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Perform POST request."""
        return await self._request_with_retry("POST", url, rate_limit_key, **kwargs)

    async def put(
        self,
        url: str,
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Perform PUT request."""
        return await self._request_with_retry("PUT", url, rate_limit_key, **kwargs)

    async def delete(
        self,
        url: str,
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Perform DELETE request."""
        return await self._request_with_retry("DELETE", url, rate_limit_key, **kwargs)

    async def get_json(
        self,
        url: str,
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Perform GET request and return JSON response."""
        response = await self.get(url, rate_limit_key, **kwargs)
        async with response:
            response.raise_for_status()
            return await response.json()

    async def post_json(
        self,
        url: str,
        data: dict[str, Any],
        rate_limit_key: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Perform POST request with JSON body and return JSON response."""
        response = await self.post(url, rate_limit_key, json=data, **kwargs)
        async with response:
            response.raise_for_status()
            return await response.json()

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            "total_requests": self._request_count,
            "session_active": self._session is not None and not self._session.closed,
            "pool_size": self._config.pool_size,
        }


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""

    pass


# Global instance
_http_client: Optional[HTTPClient] = None


def get_http_client(config: Optional[HTTPClientConfig] = None) -> HTTPClient:
    """Get the global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = HTTPClient(config)
    return _http_client


async def http_get(
    url: str,
    rate_limit_key: str | None = None,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    """Convenience function for GET requests."""
    client = get_http_client()
    return await client.get(url, rate_limit_key, **kwargs)


async def http_post(
    url: str,
    rate_limit_key: str | None = None,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    """Convenience function for POST requests."""
    client = get_http_client()
    return await client.post(url, rate_limit_key, **kwargs)


async def http_get_json(
    url: str,
    rate_limit_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience function for GET requests returning JSON."""
    client = get_http_client()
    return await client.get_json(url, rate_limit_key, **kwargs)


async def http_post_json(
    url: str,
    data: dict[str, Any],
    rate_limit_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience function for POST requests with JSON."""
    client = get_http_client()
    return await client.post_json(url, data, rate_limit_key, **kwargs)


@asynccontextmanager
async def managed_http_client(config: Optional[HTTPClientConfig] = None):
    """
    Context manager for HTTP client that ensures cleanup.

    Usage:
        async with managed_http_client() as client:
            response = await client.get("https://api.example.com")
    """
    client = HTTPClient(config)
    try:
        yield client
    finally:
        await client.close()


# Exports
__all__ = [
    "HTTPClient",
    "HTTPClientConfig",
    "RateLimitExceededError",
    "get_http_client",
    "http_get",
    "http_post",
    "http_get_json",
    "http_post_json",
    "managed_http_client",
]
