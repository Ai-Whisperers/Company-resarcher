"""
Domain-based Timeout Management (PERF-014).

Provides tiered timeout settings for different domain types,
and tracks domain failure rates for adaptive timeout adjustment.
"""

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List
from urllib.parse import urlparse

from .logger import setup_logger

logger = setup_logger("domain_timeout")


@dataclass
class DomainStats:
    """Statistics for a single domain."""
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    total_time: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None

    @property
    def total_requests(self) -> int:
        return self.success_count + self.failure_count

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests

    @property
    def avg_time(self) -> float:
        if self.success_count == 0:
            return 0.0
        return self.total_time / self.success_count


class DomainTimeoutManager:
    """
    Manages timeouts for different domains based on tier and history.

    Features:
    - Domain-based timeout tiers (fast, medium, default)
    - Tracks failure rates per domain
    - Reduces timeout for consistently failing domains
    - Circuit breaker for domains with high failure rates

    Usage:
        manager = DomainTimeoutManager()
        timeout = manager.get_timeout(url)
        try:
            result = await fetch_with_timeout(url, timeout)
            manager.record_success(url, elapsed_time)
        except TimeoutError:
            manager.record_failure(url, is_timeout=True)
    """

    # Timeout tiers based on domain characteristics
    TIMEOUT_TIERS = {
        # Very fast for sites that consistently block/timeout
        "skip_prone": {
            "timeout": 10,
            "domains": {
                "scribd.com",
                "academia.edu",
                "researchgate.net",
                "jstor.org",
                "springer.com",
            }
        },
        # Fast timeout for known-problematic sites (usually block/require login)
        "fast": {
            "timeout": 15,
            "domains": {
                "instagram.com",
                "facebook.com",
                "twitter.com",
                "x.com",
                "linkedin.com",
                "pinterest.com",
                "tiktok.com",
                "zhihu.com",
                "baidu.com",
                "weibo.com",
                "quora.com",
                "glassdoor.com",
                "yelp.com",
            }
        },
        # Medium timeout for dynamic/social sites
        "medium": {
            "timeout": 30,
            "domains": {
                "youtube.com",
                "reddit.com",
                "medium.com",
                "substack.com",
                "github.com",
                "bloomberg.com",
                "reuters.com",
                "wsj.com",
                "ft.com",
                "nytimes.com",
            }
        },
        # Extended timeout for known slow but valuable sites
        "slow": {
            "timeout": 60,
            "domains": {
                "crunchbase.com",
                "pitchbook.com",
                "statista.com",
                "mordorintelligence.com",
                "grandviewresearch.com",
                "marketresearch.com",
                "ibisworld.com",
                "sec.gov",
                "edgar-online.com",
                "ahrefs.com",
                "semrush.com",
                "similarweb.com",
            }
        },
    }

    # Default timeout (increased from 30s to 45s for better success rate)
    DEFAULT_TIMEOUT = int(os.getenv("BROWSER_FETCH_TIMEOUT_SECONDS", "45"))

    # Circuit breaker settings
    CIRCUIT_BREAKER_THRESHOLD = 5  # consecutive failures to trip
    CIRCUIT_BREAKER_RESET_SECONDS = 300  # 5 minutes

    # Adaptive timeout settings
    ADAPTIVE_THRESHOLD_REQUESTS = 3  # minimum requests before adapting
    ADAPTIVE_FAILURE_RATE = 0.5  # failure rate to trigger reduction
    ADAPTIVE_REDUCED_TIMEOUT = 15  # reduced timeout for failing domains

    def __init__(self):
        self._domain_stats: Dict[str, DomainStats] = {}
        self._consecutive_failures: Dict[str, int] = {}
        self._circuit_open_until: Dict[str, float] = {}
        self._lock = threading.Lock()

        # Build domain to tier lookup
        self._domain_tier: Dict[str, str] = {}
        for tier_name, tier_config in self.TIMEOUT_TIERS.items():
            for domain in tier_config["domains"]:
                self._domain_tier[domain] = tier_name

        logger.info(
            f"Domain timeout manager initialized: "
            f"default={self.DEFAULT_TIMEOUT}s, "
            f"tiers={list(self.TIMEOUT_TIERS.keys())}"
        )

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            if ":" in domain:
                domain = domain.split(":")[0]
            return domain
        except Exception:
            return ""

    def get_tier(self, domain: str) -> Optional[str]:
        """Get the tier for a domain."""
        if domain in self._domain_tier:
            return self._domain_tier[domain]

        # Check parent domains
        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._domain_tier:
                return self._domain_tier[parent]

        return None

    def get_base_timeout(self, url: str) -> int:
        """Get the base timeout for a URL based on its tier."""
        domain = self.extract_domain(url)
        tier = self.get_tier(domain)

        if tier and tier in self.TIMEOUT_TIERS:
            return self.TIMEOUT_TIERS[tier]["timeout"]

        return self.DEFAULT_TIMEOUT

    def get_timeout(self, url: str) -> int:
        """
        Get the effective timeout for a URL.

        Considers:
        - Domain tier
        - Historical failure rate
        - Adaptive reduction for failing domains

        Args:
            url: URL to get timeout for

        Returns:
            Timeout in seconds
        """
        domain = self.extract_domain(url)
        if not domain:
            return self.DEFAULT_TIMEOUT

        base_timeout = self.get_base_timeout(url)

        with self._lock:
            # Check for adaptive reduction based on history
            if domain in self._domain_stats:
                stats = self._domain_stats[domain]
                if stats.total_requests >= self.ADAPTIVE_THRESHOLD_REQUESTS:
                    if stats.failure_rate >= self.ADAPTIVE_FAILURE_RATE:
                        reduced = min(base_timeout, self.ADAPTIVE_REDUCED_TIMEOUT)
                        logger.debug(
                            f"Reduced timeout for {domain}: {base_timeout}s -> {reduced}s "
                            f"(failure rate: {stats.failure_rate:.1%})"
                        )
                        return reduced

        return base_timeout

    def is_circuit_open(self, url: str) -> bool:
        """
        Check if circuit breaker is open for a domain.

        Args:
            url: URL to check

        Returns:
            True if circuit is open (don't fetch), False otherwise
        """
        domain = self.extract_domain(url)
        if not domain:
            return False

        with self._lock:
            # Check consecutive failures
            consecutive = self._consecutive_failures.get(domain, 0)
            if consecutive >= self.CIRCUIT_BREAKER_THRESHOLD:
                # Check if circuit should reset
                open_until = self._circuit_open_until.get(domain, 0)
                if time.time() < open_until:
                    return True
                else:
                    # Reset circuit
                    self._consecutive_failures[domain] = 0
                    self._circuit_open_until.pop(domain, None)
                    logger.info(f"Circuit breaker reset for {domain}")

        return False

    def record_success(self, url: str, elapsed_seconds: float = 0) -> None:
        """
        Record a successful fetch.

        Args:
            url: URL that was fetched
            elapsed_seconds: Time taken to fetch
        """
        domain = self.extract_domain(url)
        if not domain:
            return

        with self._lock:
            if domain not in self._domain_stats:
                self._domain_stats[domain] = DomainStats()

            stats = self._domain_stats[domain]
            stats.success_count += 1
            stats.total_time += elapsed_seconds
            stats.last_success = time.time()

            # Reset consecutive failures on success
            self._consecutive_failures[domain] = 0

    def record_failure(self, url: str, is_timeout: bool = False) -> None:
        """
        Record a failed fetch.

        Args:
            url: URL that failed
            is_timeout: True if failure was due to timeout
        """
        domain = self.extract_domain(url)
        if not domain:
            return

        with self._lock:
            if domain not in self._domain_stats:
                self._domain_stats[domain] = DomainStats()

            stats = self._domain_stats[domain]
            stats.failure_count += 1
            if is_timeout:
                stats.timeout_count += 1
            stats.last_failure = time.time()

            # Track consecutive failures
            self._consecutive_failures[domain] = (
                self._consecutive_failures.get(domain, 0) + 1
            )

            # Open circuit breaker if threshold reached
            if self._consecutive_failures[domain] >= self.CIRCUIT_BREAKER_THRESHOLD:
                self._circuit_open_until[domain] = (
                    time.time() + self.CIRCUIT_BREAKER_RESET_SECONDS
                )
                logger.warning(
                    f"Circuit breaker opened for {domain} "
                    f"(reset in {self.CIRCUIT_BREAKER_RESET_SECONDS}s)"
                )

    def get_domain_stats(self, url: str) -> Optional[DomainStats]:
        """Get statistics for a domain."""
        domain = self.extract_domain(url)
        with self._lock:
            return self._domain_stats.get(domain)

    def get_all_stats(self) -> Dict[str, DomainStats]:
        """Get statistics for all domains."""
        with self._lock:
            return self._domain_stats.copy()

    def get_open_circuits(self) -> List[str]:
        """Get list of domains with open circuit breakers."""
        result = []
        now = time.time()
        with self._lock:
            for domain, open_until in self._circuit_open_until.items():
                if now < open_until:
                    result.append(domain)
        return result


# Global instance
_timeout_manager: Optional[DomainTimeoutManager] = None
_timeout_manager_lock = threading.Lock()


def get_timeout_manager() -> DomainTimeoutManager:
    """Get or create the global timeout manager instance."""
    global _timeout_manager
    if _timeout_manager is None:
        with _timeout_manager_lock:
            if _timeout_manager is None:
                _timeout_manager = DomainTimeoutManager()
    return _timeout_manager


def get_timeout_for_url(url: str) -> int:
    """
    Get the appropriate timeout for a URL.

    Args:
        url: URL to get timeout for

    Returns:
        Timeout in seconds
    """
    return get_timeout_manager().get_timeout(url)


def is_domain_circuit_open(url: str) -> bool:
    """
    Check if circuit breaker is open for a URL's domain.

    Args:
        url: URL to check

    Returns:
        True if should skip fetching, False otherwise
    """
    return get_timeout_manager().is_circuit_open(url)
