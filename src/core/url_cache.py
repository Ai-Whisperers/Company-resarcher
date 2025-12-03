"""
URL Fetch Cache - Session-level URL deduplication (PERF-011).

Prevents fetching the same URL multiple times during a research session.
Tracks both successful fetches and failed URLs to avoid retrying failures.
"""

import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from .logger import setup_logger
from .types import ResearchSource

logger = setup_logger("url_cache")


@dataclass
class CacheEntry:
    """Entry in the URL cache with metadata."""
    source: ResearchSource
    fetch_time: float
    hit_count: int = 0


@dataclass
class CacheStats:
    """Statistics about cache performance."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    failed_url_skips: int = 0
    normalized_dedup_hits: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def time_saved_seconds(self) -> float:
        """Estimate time saved (assuming 30s per fetch)."""
        return (self.cache_hits + self.failed_url_skips) * 30


class URLFetchCache:
    """
    Session-level URL cache to prevent duplicate fetches.

    Features:
    - Stores successful fetch results
    - Tracks failed URLs to avoid retrying
    - URL normalization for better dedup (removes tracking params)
    - Thread-safe for concurrent access
    - Provides cache statistics

    Usage:
        cache = URLFetchCache()

        # Check if URL was already fetched
        cached = cache.get(url)
        if cached:
            return cached

        # Fetch and cache result
        result = await browser.fetch_page(url)
        cache.put(url, result)
    """

    # URL parameters that are often tracking-related and can be ignored for dedup
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'ref', 'source', 'mc_cid', 'mc_eid',
        '_ga', '_gac', 'dclid', 'msclkid', 'zanpid', 'yclid',
    }

    def __init__(self, max_size: int = 10000, failed_url_ttl: int = 300):
        """
        Initialize the URL cache.

        Args:
            max_size: Maximum number of cached entries
            failed_url_ttl: TTL for failed URLs in seconds (default 5 minutes)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._failed_urls: Dict[str, float] = {}  # URL -> failure timestamp
        self._normalized_to_original: Dict[str, str] = {}  # normalized -> original URL
        self._lock = threading.RLock()
        self._max_size = max_size
        self._failed_url_ttl = failed_url_ttl
        self._stats = CacheStats()

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for better deduplication.

        - Removes tracking parameters
        - Normalizes scheme to lowercase
        - Removes default ports
        - Sorts query parameters
        - Removes trailing slashes
        """
        try:
            parsed = urlparse(url)

            # Normalize scheme
            scheme = parsed.scheme.lower()

            # Normalize host
            host = parsed.netloc.lower()
            # Remove default ports
            if ':80' in host and scheme == 'http':
                host = host.replace(':80', '')
            elif ':443' in host and scheme == 'https':
                host = host.replace(':443', '')

            # Normalize path (remove trailing slash except for root)
            path = parsed.path
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')

            # Filter and sort query parameters
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=True)
                # Remove tracking parameters
                filtered_params = {
                    k: v for k, v in params.items()
                    if k.lower() not in self.TRACKING_PARAMS
                }
                # Sort for consistency
                sorted_params = sorted(filtered_params.items())
                query = urlencode(sorted_params, doseq=True)
            else:
                query = ''

            # Rebuild URL
            normalized = urlunparse((scheme, host, path, '', query, ''))
            return normalized

        except Exception as e:
            logger.debug(f"URL normalization failed for {url}: {e}")
            return url

    def get(self, url: str) -> Optional[ResearchSource]:
        """
        Get cached result for URL if available.

        Args:
            url: URL to look up

        Returns:
            Cached ResearchSource if found, None otherwise
        """
        with self._lock:
            self._stats.total_requests += 1

            # Check if URL previously failed
            if self._is_failed_url(url):
                self._stats.failed_url_skips += 1
                logger.debug(f"Skipping previously failed URL: {url}")
                return ResearchSource(
                    url=url,
                    title="Previously Failed",
                    content="This URL failed in a previous fetch attempt",
                    source_type="error",
                    category="error",
                )

            # Try exact match first
            if url in self._cache:
                entry = self._cache[url]
                entry.hit_count += 1
                self._stats.cache_hits += 1
                logger.debug(f"Cache hit (exact): {url}")
                return entry.source

            # Try normalized URL match
            normalized = self.normalize_url(url)
            if normalized in self._normalized_to_original:
                original = self._normalized_to_original[normalized]
                if original in self._cache:
                    entry = self._cache[original]
                    entry.hit_count += 1
                    self._stats.cache_hits += 1
                    self._stats.normalized_dedup_hits += 1
                    logger.debug(f"Cache hit (normalized): {url} -> {original}")
                    return entry.source

            self._stats.cache_misses += 1
            return None

    def put(self, url: str, source: ResearchSource) -> None:
        """
        Cache a fetch result.

        Args:
            url: URL that was fetched
            source: Result of the fetch
        """
        with self._lock:
            # Don't cache if at max size (simple eviction: just stop caching)
            if len(self._cache) >= self._max_size:
                logger.warning(f"URL cache full ({self._max_size} entries)")
                return

            # If fetch was an error, record as failed URL
            if source.source_type == "error":
                self._failed_urls[url] = time.time()
                logger.debug(f"Recorded failed URL: {url}")
                return

            # Cache successful result
            entry = CacheEntry(
                source=source,
                fetch_time=time.time(),
            )
            self._cache[url] = entry

            # Also map normalized URL to original
            normalized = self.normalize_url(url)
            self._normalized_to_original[normalized] = url

            logger.debug(f"Cached URL: {url}")

    def mark_failed(self, url: str) -> None:
        """
        Mark a URL as failed without storing a full result.

        Args:
            url: URL that failed
        """
        with self._lock:
            self._failed_urls[url] = time.time()
            logger.debug(f"Marked URL as failed: {url}")

    def _is_failed_url(self, url: str) -> bool:
        """Check if URL is in failed list and not expired."""
        if url not in self._failed_urls:
            return False

        failure_time = self._failed_urls[url]
        if time.time() - failure_time > self._failed_url_ttl:
            # Expired, remove and allow retry
            del self._failed_urls[url]
            return False

        return True

    def contains(self, url: str) -> bool:
        """
        Check if URL is in cache (either successful or failed).

        Args:
            url: URL to check

        Returns:
            True if URL has been fetched before
        """
        with self._lock:
            if url in self._cache:
                return True
            if self._is_failed_url(url):
                return True

            # Check normalized version
            normalized = self.normalize_url(url)
            if normalized in self._normalized_to_original:
                return True

            return False

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        with self._lock:
            return CacheStats(
                total_requests=self._stats.total_requests,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                failed_url_skips=self._stats.failed_url_skips,
                normalized_dedup_hits=self._stats.normalized_dedup_hits,
            )

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._failed_urls.clear()
            self._normalized_to_original.clear()
            self._stats = CacheStats()
            logger.info("URL cache cleared")

    def __len__(self) -> int:
        """Return number of cached entries."""
        with self._lock:
            return len(self._cache)


# Global URL cache instance (lazy initialized)
_url_cache: Optional[URLFetchCache] = None
_url_cache_lock = threading.Lock()


def get_url_cache() -> URLFetchCache:
    """Get or create the global URL cache instance."""
    global _url_cache
    if _url_cache is None:
        with _url_cache_lock:
            if _url_cache is None:
                _url_cache = URLFetchCache()
                logger.info("URL fetch cache initialized")
    return _url_cache


def reset_url_cache() -> None:
    """Reset the global URL cache (for new research sessions)."""
    global _url_cache
    with _url_cache_lock:
        if _url_cache is not None:
            _url_cache.clear()
            _url_cache = None
        logger.info("URL fetch cache reset")
