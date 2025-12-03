"""
Cross-Company URL Cache (PERF-018).

Extends URL caching to work across companies in batch research.
Prevents re-fetching the same URLs when researching multiple companies
in the same market/industry.
"""

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, Optional, List, Any
from urllib.parse import urlparse

from .logger import setup_logger
from .types import ResearchSource

logger = setup_logger("cross_company_cache")


@dataclass
class CrossCompanyCacheEntry:
    """Cache entry with company attribution."""
    source: ResearchSource
    companies_used: Set[str] = field(default_factory=set)
    fetch_time: float = 0.0
    hit_count: int = 0

    def __post_init__(self):
        if self.fetch_time == 0.0:
            self.fetch_time = time.time()


@dataclass
class CrossCompanyCacheStats:
    """Statistics for cross-company cache."""
    total_urls: int = 0
    cross_company_hits: int = 0
    same_company_hits: int = 0
    cache_misses: int = 0
    bytes_saved: int = 0
    companies_benefited: Set[str] = field(default_factory=set)

    @property
    def total_hits(self) -> int:
        return self.cross_company_hits + self.same_company_hits

    @property
    def hit_rate(self) -> float:
        total = self.total_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.total_hits / total * 100


class CrossCompanyURLCache:
    """
    Cross-company URL cache for batch research.

    Maintains a shared cache across all companies in a batch run.
    Tracks which companies have used which URLs to enable intelligent
    cross-referencing.

    Features:
    - Shared cache across companies in batch
    - Tracks company usage per URL
    - Domain-level statistics
    - Persistence support for long batches
    - Memory-efficient with LRU eviction

    Usage:
        cache = CrossCompanyURLCache()

        # Company 1 fetches URL
        source = await fetch_url(url)
        cache.put(url, source, company="COPACO")

        # Company 2 gets cached result
        cached = cache.get(url, company="Tigo Paraguay")
        if cached:
            print(f"Reused from {cached.companies_used}")
    """

    # Maximum cache size
    MAX_ENTRIES = 50000

    # Domains that shouldn't be shared (company-specific)
    NON_SHAREABLE_DOMAINS = {
        "linkedin.com",  # Company-specific profiles
        "crunchbase.com",  # Company-specific pages
        "glassdoor.com",  # Company-specific reviews
    }

    def __init__(
        self,
        max_entries: int = MAX_ENTRIES,
        persist_path: Optional[str] = None,
    ):
        self._cache: Dict[str, CrossCompanyCacheEntry] = {}
        self._domain_stats: Dict[str, Dict[str, int]] = {}  # domain -> {hits, misses}
        self._lock = threading.RLock()
        self._max_entries = max_entries
        self._persist_path = persist_path
        self._stats = CrossCompanyCacheStats()

        # Load persisted cache if available
        if persist_path and os.path.exists(persist_path):
            self._load_from_disk()

        logger.info(
            f"Cross-company cache initialized (max={max_entries}, "
            f"persist={persist_path is not None})"
        )

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent caching."""
        try:
            parsed = urlparse(url)
            # Normalize to lowercase host, remove www, remove trailing slash
            host = parsed.netloc.lower()
            if host.startswith("www."):
                host = host[4:]
            path = parsed.path.rstrip("/") or "/"
            return f"{parsed.scheme}://{host}{path}"
        except Exception:
            return url

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    def _is_shareable(self, url: str) -> bool:
        """Check if URL content can be shared across companies."""
        domain = self._get_domain(url)
        return domain not in self.NON_SHAREABLE_DOMAINS

    def get(
        self,
        url: str,
        company: str,
        require_shareable: bool = True,
    ) -> Optional[ResearchSource]:
        """
        Get cached content for URL.

        Args:
            url: URL to look up
            company: Company requesting the content
            require_shareable: Only return if URL is shareable

        Returns:
            Cached ResearchSource if found
        """
        normalized = self._normalize_url(url)
        domain = self._get_domain(url)

        with self._lock:
            if normalized not in self._cache:
                self._stats.cache_misses += 1
                self._update_domain_stats(domain, hit=False)
                return None

            entry = self._cache[normalized]

            # Check shareability
            if require_shareable and not self._is_shareable(url):
                if company not in entry.companies_used:
                    # Different company, non-shareable domain
                    self._stats.cache_misses += 1
                    return None

            # Record hit
            entry.hit_count += 1

            if company in entry.companies_used:
                self._stats.same_company_hits += 1
            else:
                self._stats.cross_company_hits += 1
                self._stats.companies_benefited.add(company)
                entry.companies_used.add(company)

            self._update_domain_stats(domain, hit=True)

            logger.debug(
                f"Cross-company cache hit: {url} "
                f"(used by: {entry.companies_used})"
            )

            return entry.source

    def put(
        self,
        url: str,
        source: ResearchSource,
        company: str,
    ) -> None:
        """
        Cache content for URL.

        Args:
            url: URL that was fetched
            source: Content that was fetched
            company: Company that fetched it
        """
        normalized = self._normalize_url(url)

        with self._lock:
            # Check capacity
            if len(self._cache) >= self._max_entries:
                self._evict_oldest()

            # Create or update entry
            if normalized in self._cache:
                entry = self._cache[normalized]
                entry.companies_used.add(company)
            else:
                entry = CrossCompanyCacheEntry(
                    source=source,
                    companies_used={company},
                )
                self._cache[normalized] = entry
                self._stats.total_urls += 1

                # Track content size for stats
                if source.content:
                    self._stats.bytes_saved += len(source.content.encode('utf-8', errors='ignore'))

    def get_urls_for_company(self, company: str) -> List[str]:
        """Get all URLs used by a specific company."""
        with self._lock:
            return [
                url for url, entry in self._cache.items()
                if company in entry.companies_used
            ]

    def get_shared_urls(self) -> List[str]:
        """Get URLs that have been used by multiple companies."""
        with self._lock:
            return [
                url for url, entry in self._cache.items()
                if len(entry.companies_used) > 1
            ]

    def get_potential_shares(self, company: str) -> List[str]:
        """
        Get URLs that could be useful for a company.

        Returns URLs fetched by other companies but not yet used
        by the specified company.
        """
        with self._lock:
            return [
                url for url, entry in self._cache.items()
                if company not in entry.companies_used
                and self._is_shareable(url)
            ]

    def _update_domain_stats(self, domain: str, hit: bool) -> None:
        """Update domain-level statistics."""
        if domain not in self._domain_stats:
            self._domain_stats[domain] = {"hits": 0, "misses": 0}

        if hit:
            self._domain_stats[domain]["hits"] += 1
        else:
            self._domain_stats[domain]["misses"] += 1

    def _evict_oldest(self, count: int = 100) -> None:
        """Evict oldest entries to make room."""
        # Sort by fetch time, evict oldest
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].fetch_time,
        )

        for url, _ in sorted_entries[:count]:
            del self._cache[url]

        logger.debug(f"Evicted {count} oldest cache entries")

    def get_stats(self) -> CrossCompanyCacheStats:
        """Get cache statistics."""
        with self._lock:
            return CrossCompanyCacheStats(
                total_urls=self._stats.total_urls,
                cross_company_hits=self._stats.cross_company_hits,
                same_company_hits=self._stats.same_company_hits,
                cache_misses=self._stats.cache_misses,
                bytes_saved=self._stats.bytes_saved,
                companies_benefited=self._stats.companies_benefited.copy(),
            )

    def get_domain_stats(self) -> Dict[str, Dict[str, int]]:
        """Get per-domain statistics."""
        with self._lock:
            return self._domain_stats.copy()

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._domain_stats.clear()
            self._stats = CrossCompanyCacheStats()
            logger.info("Cross-company cache cleared")

    def persist(self) -> None:
        """Persist cache to disk."""
        if not self._persist_path:
            return

        with self._lock:
            try:
                data = {
                    "entries": {
                        url: {
                            "source": {
                                "url": e.source.url,
                                "title": e.source.title,
                                "content": e.source.content[:10000],  # Truncate for size
                                "source_type": e.source.source_type,
                            },
                            "companies": list(e.companies_used),
                            "fetch_time": e.fetch_time,
                            "hit_count": e.hit_count,
                        }
                        for url, e in self._cache.items()
                    },
                    "stats": {
                        "total_urls": self._stats.total_urls,
                        "cross_company_hits": self._stats.cross_company_hits,
                        "same_company_hits": self._stats.same_company_hits,
                    },
                }

                with open(self._persist_path, "w") as f:
                    json.dump(data, f)

                logger.info(f"Persisted {len(self._cache)} cache entries")

            except Exception as e:
                logger.warning(f"Failed to persist cache: {e}")

    def _load_from_disk(self) -> None:
        """Load cache from disk."""
        try:
            with open(self._persist_path, "r") as f:
                data = json.load(f)

            for url, entry_data in data.get("entries", {}).items():
                source_data = entry_data["source"]
                source = ResearchSource(
                    url=source_data["url"],
                    title=source_data["title"],
                    content=source_data["content"],
                    source_type=source_data["source_type"],
                )

                self._cache[url] = CrossCompanyCacheEntry(
                    source=source,
                    companies_used=set(entry_data["companies"]),
                    fetch_time=entry_data["fetch_time"],
                    hit_count=entry_data["hit_count"],
                )

            logger.info(f"Loaded {len(self._cache)} cached entries from disk")

        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")


# Global instance for batch runs
_cross_company_cache: Optional[CrossCompanyURLCache] = None
_cache_lock = threading.Lock()


def get_cross_company_cache(
    persist_path: Optional[str] = None,
) -> CrossCompanyURLCache:
    """Get or create the global cross-company cache."""
    global _cross_company_cache
    if _cross_company_cache is None:
        with _cache_lock:
            if _cross_company_cache is None:
                _cross_company_cache = CrossCompanyURLCache(persist_path=persist_path)
    return _cross_company_cache


def reset_cross_company_cache() -> None:
    """Reset the global cross-company cache."""
    global _cross_company_cache
    with _cache_lock:
        if _cross_company_cache is not None:
            _cross_company_cache.clear()
            _cross_company_cache = None
        logger.info("Cross-company cache reset")


__all__ = [
    "CrossCompanyURLCache",
    "CrossCompanyCacheEntry",
    "CrossCompanyCacheStats",
    "get_cross_company_cache",
    "reset_cross_company_cache",
]
