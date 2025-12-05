"""
Service configurations (Cache, Search, Browser).
"""

from typing import Optional
from pydantic import BaseModel


class CacheConfig(BaseModel):
    """Cache configuration settings."""

    enabled: bool = True  # Enable/disable caching globally
    default_ttl: int = 3600  # Default TTL in seconds (1 hour)
    ai_cache_enabled: bool = True  # Enable AI response caching
    max_size_mb: Optional[int] = None  # Max cache size (None = unlimited)
    cleanup_interval: int = 3600  # Cleanup interval in seconds


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

    # Manager settings (CQ-132, CQ-133, CQ-134, CQ-135)
    max_backoff_seconds: float = 30.0  # Maximum backoff time
    sleep_duration_seconds: float = 0.5  # Sleep between operations
    acquire_timeout_seconds: float = 10.0  # Timeout for acquiring resources
    retry_timeout_seconds: float = 5.0  # Timeout for retry operations


class BrowserConfig(BaseModel):
    """Browser/scraping configuration settings (ARCH-004)."""

    fetch_timeout_seconds: int = 60
    page_navigation_timeout_ms: int = 30000
    max_concurrent: int = 5
    enable_html_cache: bool = True
