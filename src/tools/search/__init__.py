"""
Search Providers Package

Provides multiple search provider implementations with automatic fallback.
Free providers (DuckDuckGo, Jina) are prioritized over paid providers.

Usage:
    from src.tools.search import SearchManager

    manager = SearchManager()
    results = await manager.search("query", max_results=10)
"""

from .base import SearchProvider, SearchResult, SearchError, RateLimitError
from .manager import SearchManager, get_search_manager
from .duckduckgo import DuckDuckGoProvider
from .jina import JinaSearchProvider
from .langsearch import LangSearchProvider
from .serper import SerperProvider
from .tavily_provider import TavilyProvider

__all__ = [
    # Base classes
    "SearchProvider",
    "SearchResult",
    "SearchError",
    "RateLimitError",
    # Manager
    "SearchManager",
    "get_search_manager",
    # Providers
    "DuckDuckGoProvider",
    "JinaSearchProvider",
    "LangSearchProvider",
    "SerperProvider",
    "TavilyProvider",
]
