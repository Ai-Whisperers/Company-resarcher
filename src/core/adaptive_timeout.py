"""
Adaptive Search Timeout (PERF-013).

Tracks query patterns and adjusts timeouts based on historical success rates.
Reduces timeout for query types that consistently fail or return nothing.
"""

import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

from .logger import setup_logger

logger = setup_logger("adaptive_timeout")


@dataclass
class QueryStats:
    """Statistics for a query pattern."""
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    empty_result_count: int = 0
    total_time: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None

    @property
    def total_attempts(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 1.0  # Assume success until proven otherwise
        return self.success_count / self.total_attempts

    @property
    def timeout_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.timeout_count / self.total_attempts

    @property
    def avg_time(self) -> float:
        if self.success_count == 0:
            return 0.0
        return self.total_time / self.success_count


@dataclass
class SectionStats:
    """Statistics for a research section."""
    queries_attempted: int = 0
    queries_with_results: int = 0
    consecutive_empty: int = 0
    consecutive_timeout: int = 0

    @property
    def hit_rate(self) -> float:
        if self.queries_attempted == 0:
            return 1.0
        return self.queries_with_results / self.queries_attempted

    def should_skip(self, threshold: int = 5) -> bool:
        """Check if section should be skipped due to consecutive failures."""
        return self.consecutive_empty >= threshold or self.consecutive_timeout >= threshold


class AdaptiveTimeoutManager:
    """
    Manages adaptive timeouts for search queries.

    Features:
    - Tracks success/failure rates per query pattern
    - Reduces timeout for consistently failing patterns
    - Detects sections with no results and suggests skipping
    - Early termination for hopeless queries

    Usage:
        manager = AdaptiveTimeoutManager()

        # Get timeout for a query
        timeout = manager.get_timeout(query, section="market_intelligence")

        # Record result
        if results:
            manager.record_success(query, section, elapsed_time, len(results))
        else:
            manager.record_failure(query, section, is_timeout=True)

        # Check if section should be skipped
        if manager.should_skip_section(section):
            logger.info(f"Skipping section {section} - too many failures")
    """

    # Minimum timeout (floor)
    MIN_TIMEOUT = 5

    # Adaptive thresholds
    REDUCE_TIMEOUT_THRESHOLD = 3  # Reduce after N consecutive failures
    SKIP_SECTION_THRESHOLD = 5   # Skip section after N consecutive empty results

    # Query pattern extraction
    QUERY_STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can",
    }

    @staticmethod
    def _get_default_timeout() -> int:
        """Get default timeout from env var at runtime (not import time)."""
        return int(os.getenv("SEARCH_TIMEOUT_SECONDS", "60"))

    def __init__(self, default_timeout: int = None):
        # Read from env var at runtime if not specified
        if default_timeout is None:
            default_timeout = self._get_default_timeout()
        self.default_timeout = default_timeout
        self._query_stats: Dict[str, QueryStats] = {}
        self._section_stats: Dict[str, SectionStats] = {}
        self._consecutive_failures: Dict[str, int] = {}  # pattern -> count
        self._lock = threading.Lock()
        logger.info(f"Adaptive timeout manager initialized (default={default_timeout}s)")

    def _get_query_pattern(self, query: str) -> str:
        """
        Extract a pattern from a query for grouping similar queries.

        Removes company-specific terms to group queries by structure.
        """
        # Normalize
        words = query.lower().split()

        # Remove stop words and very short words
        pattern_words = [
            w for w in words
            if w not in self.QUERY_STOP_WORDS and len(w) > 2
        ]

        # Take first 5 significant words
        pattern = " ".join(pattern_words[:5])

        # Hash if too long
        if len(pattern) > 50:
            return hashlib.md5(pattern.encode()).hexdigest()[:12]

        return pattern or "generic"

    def get_timeout(
        self,
        query: str,
        section: Optional[str] = None,
    ) -> int:
        """
        Get adaptive timeout for a query.

        Args:
            query: The search query
            section: Optional section name for section-level tracking

        Returns:
            Timeout in seconds
        """
        pattern = self._get_query_pattern(query)

        with self._lock:
            # Check pattern-level failures
            consecutive = self._consecutive_failures.get(pattern, 0)

            if consecutive >= self.REDUCE_TIMEOUT_THRESHOLD:
                # Reduce timeout progressively
                reduction = min(consecutive - self.REDUCE_TIMEOUT_THRESHOLD + 1, 3)
                reduced = max(self.MIN_TIMEOUT, self.default_timeout - (reduction * 5))
                logger.debug(
                    f"Reduced timeout for pattern '{pattern}': "
                    f"{self.default_timeout}s -> {reduced}s "
                    f"({consecutive} consecutive failures)"
                )
                return reduced

            # Check section-level failures
            if section and section in self._section_stats:
                section_stat = self._section_stats[section]
                if section_stat.consecutive_timeout >= 3:
                    reduced = max(self.MIN_TIMEOUT, self.default_timeout - 10)
                    logger.debug(
                        f"Reduced timeout for section '{section}': "
                        f"{self.default_timeout}s -> {reduced}s"
                    )
                    return reduced

        return self.default_timeout

    def record_success(
        self,
        query: str,
        section: Optional[str] = None,
        elapsed_seconds: float = 0,
        result_count: int = 0,
    ) -> None:
        """Record a successful query."""
        pattern = self._get_query_pattern(query)

        with self._lock:
            # Update pattern stats
            if pattern not in self._query_stats:
                self._query_stats[pattern] = QueryStats()

            stats = self._query_stats[pattern]
            stats.success_count += 1
            stats.total_time += elapsed_seconds
            stats.last_success = time.time()

            # Reset consecutive failures
            self._consecutive_failures[pattern] = 0

            # Update section stats
            if section:
                if section not in self._section_stats:
                    self._section_stats[section] = SectionStats()

                section_stat = self._section_stats[section]
                section_stat.queries_attempted += 1
                if result_count > 0:
                    section_stat.queries_with_results += 1
                    section_stat.consecutive_empty = 0
                    section_stat.consecutive_timeout = 0
                else:
                    section_stat.consecutive_empty += 1

    def record_failure(
        self,
        query: str,
        section: Optional[str] = None,
        is_timeout: bool = False,
        is_empty: bool = False,
    ) -> None:
        """Record a failed query."""
        pattern = self._get_query_pattern(query)

        with self._lock:
            # Update pattern stats
            if pattern not in self._query_stats:
                self._query_stats[pattern] = QueryStats()

            stats = self._query_stats[pattern]
            stats.failure_count += 1
            if is_timeout:
                stats.timeout_count += 1
            if is_empty:
                stats.empty_result_count += 1
            stats.last_failure = time.time()

            # Track consecutive failures
            self._consecutive_failures[pattern] = (
                self._consecutive_failures.get(pattern, 0) + 1
            )

            # Update section stats
            if section:
                if section not in self._section_stats:
                    self._section_stats[section] = SectionStats()

                section_stat = self._section_stats[section]
                section_stat.queries_attempted += 1
                if is_timeout:
                    section_stat.consecutive_timeout += 1
                if is_empty:
                    section_stat.consecutive_empty += 1

    def should_skip_section(self, section: str) -> bool:
        """
        Check if a section should be skipped due to too many failures.

        Args:
            section: Section name

        Returns:
            True if section should be skipped
        """
        with self._lock:
            if section in self._section_stats:
                return self._section_stats[section].should_skip(self.SKIP_SECTION_THRESHOLD)
        return False

    def get_section_stats(self, section: str) -> Optional[SectionStats]:
        """Get statistics for a section."""
        with self._lock:
            return self._section_stats.get(section)

    def get_stats_summary(self) -> Dict[str, any]:
        """Get summary of all statistics."""
        with self._lock:
            total_patterns = len(self._query_stats)
            failing_patterns = sum(
                1 for s in self._query_stats.values()
                if s.success_rate < 0.5 and s.total_attempts >= 3
            )

            skippable_sections = [
                name for name, stats in self._section_stats.items()
                if stats.should_skip()
            ]

            return {
                "total_patterns": total_patterns,
                "failing_patterns": failing_patterns,
                "skippable_sections": skippable_sections,
                "section_hit_rates": {
                    name: stats.hit_rate
                    for name, stats in self._section_stats.items()
                },
            }

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._query_stats.clear()
            self._section_stats.clear()
            self._consecutive_failures.clear()
            logger.info("Adaptive timeout statistics reset")


# Global instance
_adaptive_manager: Optional[AdaptiveTimeoutManager] = None
_adaptive_manager_lock = threading.Lock()


def get_adaptive_timeout_manager() -> AdaptiveTimeoutManager:
    """Get or create the global adaptive timeout manager."""
    global _adaptive_manager
    if _adaptive_manager is None:
        with _adaptive_manager_lock:
            if _adaptive_manager is None:
                _adaptive_manager = AdaptiveTimeoutManager()
    return _adaptive_manager


def get_adaptive_search_timeout(query: str, section: Optional[str] = None) -> int:
    """Get adaptive timeout for a search query."""
    return get_adaptive_timeout_manager().get_timeout(query, section)
