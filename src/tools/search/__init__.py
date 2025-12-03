"""
Search Package

Provides search functionality with multiple provider implementations.
Free providers (DuckDuckGo, Jina) are prioritized over paid providers.

Usage:
    from src.tools.search import SearchManager, SearchTool

    # Using SearchManager directly
    manager = SearchManager()
    results = await manager.search("query", max_results=10)

    # Using SearchTool (higher-level interface)
    tool = SearchTool()
    results = await tool.search("query")
"""

from .base import SearchProvider, SearchResult, SearchError, RateLimitError
from .manager import SearchManager, get_search_manager, reset_search_manager
from .tool import SearchTool, SEARCH_TIMEOUT_SECONDS
from .providers.duckduckgo import DuckDuckGoProvider
from .providers.jina import JinaSearchProvider
from .providers.langsearch import LangSearchProvider
from .providers.serper import SerperProvider
from .providers.tavily_provider import TavilyProvider
from .providers.brave import BraveSearchProvider
from .providers.bing import BingSearchProvider

__all__ = [
    # Base classes
    "SearchProvider",
    "SearchResult",
    "SearchError",
    "RateLimitError",
    # Manager and Tool
    "SearchManager",
    "get_search_manager",
    "reset_search_manager",
    "SearchTool",
    "SEARCH_TIMEOUT_SECONDS",
    # Providers
    "DuckDuckGoProvider",
    "JinaSearchProvider",
    "LangSearchProvider",
    "SerperProvider",
    "TavilyProvider",
    "BraveSearchProvider",
    "BingSearchProvider",
]
