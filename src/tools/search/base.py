"""
Base classes for search providers.

Defines the interface that all search providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchError(Exception):
    """Base exception for search errors."""

    def __init__(self, message: str, provider: str = "unknown", query: str = ""):
        self.message = message
        self.provider = provider
        self.query = query
        super().__init__(f"[{provider}] {message}")


class RateLimitError(SearchError):
    """Raised when a provider's rate limit is exceeded."""

    def __init__(self, provider: str, query: str = "", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message, provider, query)


class ProviderUnavailableError(SearchError):
    """Raised when a provider is not configured or unavailable."""

    def __init__(self, provider: str, reason: str = "not configured"):
        super().__init__(f"Provider unavailable: {reason}", provider)


@dataclass
class SearchResult:
    """Standardized search result from any provider."""

    title: str
    url: str
    snippet: str
    source: str  # Provider name (e.g., "duckduckgo", "jina", "serper")

    # Optional metadata
    published_date: Optional[str] = None
    score: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "published_date": self.published_date,
            "score": self.score,
        }


class SearchProvider(ABC):
    """
    Abstract base class for search providers.

    All search providers must implement this interface.
    """

    # Provider identification
    name: str = "base"
    priority: int = 100  # Lower = higher priority (used in fallback chain)

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Execute a search query.

        Args:
            query: The search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: On search failure
            RateLimitError: When rate limited
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is configured and available.

        Returns:
            True if the provider can be used, False otherwise
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get provider status information."""
        return {
            "name": self.name,
            "priority": self.priority,
            "available": self.is_available(),
        }
