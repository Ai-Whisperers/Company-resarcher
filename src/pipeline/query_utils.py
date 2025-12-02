"""
Query Utilities for Research Pipeline.

Provides:
- QUERY-004: Time-bounded query generation
- QUERY-006: Query deduplication

Usage:
    from src.pipeline.query_utils import (
        add_time_bounds,
        deduplicate_queries,
        QueryDeduplicator,
        RecencyFilter,
    )
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# Time-Bounded Queries (QUERY-004)
# =============================================================================


class RecencyFilter(str, Enum):
    """Time periods for filtering search results."""

    RECENT = "recent"  # Last 30 days
    LAST_QUARTER = "last_quarter"  # Last 90 days
    LAST_YEAR = "last_year"  # Last 365 days
    LAST_2_YEARS = "last_2_years"  # Last 730 days
    ALL_TIME = "all_time"  # No filter


@dataclass
class TimeRange:
    """Date range for time-bounded queries."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @classmethod
    def from_filter(cls, filter_type: RecencyFilter) -> "TimeRange":
        """Create a TimeRange from a RecencyFilter."""
        now = datetime.now()

        if filter_type == RecencyFilter.ALL_TIME:
            return cls()

        days_map = {
            RecencyFilter.RECENT: 30,
            RecencyFilter.LAST_QUARTER: 90,
            RecencyFilter.LAST_YEAR: 365,
            RecencyFilter.LAST_2_YEARS: 730,
        }

        days = days_map.get(filter_type, 365)
        start = now - timedelta(days=days)

        return cls(start_date=start, end_date=now)

    def to_search_suffix(self) -> str:
        """
        Convert to a search query suffix.

        Returns search operators like "after:2024-01-01" or date range text.
        """
        if not self.start_date:
            return ""

        year = self.start_date.year

        # For Google-style searches
        if self.end_date and self.start_date.year == self.end_date.year:
            return f"{year}"

        return f"after:{self.start_date.strftime('%Y-%m-%d')}"


def add_time_bounds(
    query: str,
    recency: RecencyFilter = RecencyFilter.LAST_YEAR,
    style: str = "suffix",
) -> str:
    """
    Add time bounds to a search query.

    Args:
        query: Original search query
        recency: How recent the data should be
        style: "suffix" adds year, "operator" adds after:date

    Returns:
        Query with time bounds added

    Examples:
        >>> add_time_bounds("Apple revenue", RecencyFilter.RECENT)
        'Apple revenue 2024'

        >>> add_time_bounds("market share", RecencyFilter.LAST_YEAR, style="operator")
        'market share after:2024-01-01'
    """
    if recency == RecencyFilter.ALL_TIME:
        return query

    time_range = TimeRange.from_filter(recency)

    if style == "suffix":
        # Add year to query (most search engines understand this)
        year = datetime.now().year
        if recency == RecencyFilter.RECENT:
            return f"{query} {year}"
        elif recency == RecencyFilter.LAST_QUARTER:
            return f"{query} {year}"
        elif recency == RecencyFilter.LAST_YEAR:
            return f"{query} {year}"
        else:
            return f"{query} {year - 1} OR {year}"
    else:
        # Use search operator syntax
        suffix = time_range.to_search_suffix()
        return f"{query} {suffix}" if suffix else query


def get_financial_time_bounds() -> str:
    """Get time bounds for financial data (current and previous fiscal year)."""
    now = datetime.now()
    current_year = now.year
    # If we're in Q1, include previous year
    if now.month <= 3:
        return f"{current_year - 1} OR {current_year}"
    return str(current_year)


def get_market_time_bounds() -> str:
    """Get time bounds for market data (current year focus)."""
    return str(datetime.now().year)


# Query type to default recency mapping
QUERY_TYPE_RECENCY: Dict[str, RecencyFilter] = {
    "market": RecencyFilter.LAST_YEAR,
    "financial": RecencyFilter.LAST_YEAR,
    "competitor": RecencyFilter.LAST_YEAR,
    "brand": RecencyFilter.LAST_2_YEARS,  # Brand info changes less frequently
    "sales": RecencyFilter.LAST_YEAR,
    "news": RecencyFilter.RECENT,
    "events": RecencyFilter.RECENT,
    "default": RecencyFilter.LAST_YEAR,
}


def get_recency_for_query_type(query_type: str) -> RecencyFilter:
    """Get the appropriate recency filter for a query type."""
    return QUERY_TYPE_RECENCY.get(query_type, QUERY_TYPE_RECENCY["default"])


# =============================================================================
# Query Deduplication (QUERY-006)
# =============================================================================


def normalize_query(query: str) -> str:
    """
    Normalize a query for comparison and deduplication.

    Args:
        query: Raw search query

    Returns:
        Normalized query string

    Normalization steps:
    - Lowercase
    - Remove extra whitespace
    - Remove quotes
    - Remove common stop words for comparison
    - Sort words alphabetically (for semantic similarity)
    """
    # Lowercase
    normalized = query.lower()

    # Remove quotes
    normalized = normalized.replace('"', "").replace("'", "")

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    # Remove search operators
    operators = ["site:", "inurl:", "filetype:", "intitle:", "after:", "before:"]
    for op in operators:
        normalized = re.sub(rf"{op}\S+", "", normalized)

    # Clean up
    normalized = " ".join(normalized.split())

    return normalized


def query_hash(query: str) -> str:
    """Generate a hash for a normalized query."""
    normalized = normalize_query(query)
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def query_words_set(query: str) -> Set[str]:
    """Get the set of meaningful words in a query for similarity comparison."""
    normalized = normalize_query(query)

    # Remove stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "vs", "versus", "about", "into", "through", "during", "before", "after",
    }

    words = set(normalized.split())
    return words - stop_words


def query_similarity(query1: str, query2: str) -> float:
    """
    Calculate similarity between two queries using Jaccard similarity.

    Args:
        query1: First query
        query2: Second query

    Returns:
        Similarity score between 0 and 1
    """
    words1 = query_words_set(query1)
    words2 = query_words_set(query2)

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


@dataclass
class QueryDeduplicator:
    """
    Deduplicates queries using normalization and similarity matching.

    Usage:
        dedup = QueryDeduplicator(similarity_threshold=0.8)
        unique_queries = dedup.deduplicate(queries)
    """

    similarity_threshold: float = 0.75  # Queries more similar are duplicates
    _seen_hashes: Set[str] = field(default_factory=set)
    _seen_queries: List[str] = field(default_factory=list)

    def is_duplicate(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a query is a duplicate of previously seen queries.

        Args:
            query: Query to check

        Returns:
            Tuple of (is_duplicate, similar_query_if_duplicate)
        """
        q_hash = query_hash(query)

        # Check exact match (by hash)
        if q_hash in self._seen_hashes:
            return True, None

        # Check similarity with seen queries
        for seen in self._seen_queries:
            sim = query_similarity(query, seen)
            if sim >= self.similarity_threshold:
                return True, seen

        return False, None

    def add(self, query: str) -> bool:
        """
        Add a query to the seen set.

        Args:
            query: Query to add

        Returns:
            True if added (not a duplicate), False if duplicate
        """
        is_dup, _ = self.is_duplicate(query)
        if is_dup:
            return False

        self._seen_hashes.add(query_hash(query))
        self._seen_queries.append(query)
        return True

    def deduplicate(self, queries: List[str]) -> List[str]:
        """
        Deduplicate a list of queries.

        Args:
            queries: List of queries to deduplicate

        Returns:
            List of unique queries (preserving order)
        """
        unique = []
        for query in queries:
            if self.add(query):
                unique.append(query)
        return unique

    def reset(self) -> None:
        """Clear the deduplicator state."""
        self._seen_hashes.clear()
        self._seen_queries.clear()

    @property
    def stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return {
            "unique_queries": len(self._seen_queries),
            "unique_hashes": len(self._seen_hashes),
        }


def deduplicate_queries(
    queries: List[str],
    similarity_threshold: float = 0.75,
) -> List[str]:
    """
    Convenience function to deduplicate a list of queries.

    Args:
        queries: List of queries
        similarity_threshold: Similarity threshold for deduplication

    Returns:
        Deduplicated list of queries
    """
    dedup = QueryDeduplicator(similarity_threshold=similarity_threshold)
    return dedup.deduplicate(queries)


# =============================================================================
# Combined Query Enhancement
# =============================================================================


def enhance_query(
    query: str,
    query_type: str = "default",
    add_recency: bool = True,
    company_name: Optional[str] = None,
) -> str:
    """
    Apply all query enhancements.

    Args:
        query: Original query
        query_type: Type of query (market, financial, etc.)
        add_recency: Whether to add time bounds
        company_name: Company name for disambiguation

    Returns:
        Enhanced query
    """
    enhanced = query

    # Add recency bounds if requested
    if add_recency:
        recency = get_recency_for_query_type(query_type)
        enhanced = add_time_bounds(enhanced, recency)

    return enhanced


def prepare_queries(
    queries: List[str],
    query_type: str = "default",
    add_recency: bool = True,
    deduplicate: bool = True,
    similarity_threshold: float = 0.75,
) -> List[str]:
    """
    Prepare a list of queries with enhancement and deduplication.

    Args:
        queries: List of raw queries
        query_type: Type of queries (for recency selection)
        add_recency: Whether to add time bounds
        deduplicate: Whether to deduplicate
        similarity_threshold: Threshold for deduplication

    Returns:
        Enhanced and deduplicated queries
    """
    # Enhance each query
    enhanced = [
        enhance_query(q, query_type, add_recency) for q in queries
    ]

    # Deduplicate if requested
    if deduplicate:
        enhanced = deduplicate_queries(enhanced, similarity_threshold)

    return enhanced


__all__ = [
    # Time-bounded queries
    "RecencyFilter",
    "TimeRange",
    "add_time_bounds",
    "get_financial_time_bounds",
    "get_market_time_bounds",
    "get_recency_for_query_type",
    "QUERY_TYPE_RECENCY",
    # Query deduplication
    "normalize_query",
    "query_hash",
    "query_similarity",
    "QueryDeduplicator",
    "deduplicate_queries",
    # Combined
    "enhance_query",
    "prepare_queries",
]
