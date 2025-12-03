"""
Shared tool instances to reduce resource usage.
Each tool is instantiated once and reused across all agents.
Thread-safe singleton pattern using locks.
"""

import threading
from .search.tool import SearchTool
from .browser import ModularBrowserTool as BrowserTool
from .specialized.local_search import LocalSearchTool
from .specialized.patent import PatentSearchTool
from .specialized.chart import ChartGeneratorTool
from .search.manager import reset_search_manager
from .data.company.github import GitHubTool, get_shared_github_tool, reset_github_tool

# Singleton instances
_search_tool_instance: SearchTool | None = None
_local_search_tool_instance: LocalSearchTool | None = None
_browser_tool_instance: BrowserTool | None = None
_patent_tool_instance: PatentSearchTool | None = None
_github_tool_instance: GitHubTool | None = None

# Locks for thread-safe singleton access
_search_tool_lock = threading.Lock()
_local_search_tool_lock = threading.Lock()
_browser_tool_lock = threading.Lock()
_patent_tool_lock = threading.Lock()


def get_shared_search_tool() -> SearchTool:
    """Get or create the shared SearchTool instance (thread-safe)."""
    global _search_tool_instance
    if _search_tool_instance is None:
        with _search_tool_lock:
            # Double-check locking pattern
            if _search_tool_instance is None:
                _search_tool_instance = SearchTool()
    return _search_tool_instance


def get_shared_local_search_tool() -> LocalSearchTool:
    """Get or create the shared LocalSearchTool instance (thread-safe)."""
    global _local_search_tool_instance
    if _local_search_tool_instance is None:
        with _local_search_tool_lock:
            # Double-check locking pattern
            if _local_search_tool_instance is None:
                _local_search_tool_instance = LocalSearchTool()
    return _local_search_tool_instance


def get_shared_browser_tool() -> BrowserTool:
    """Get or create the shared BrowserTool instance (thread-safe)."""
    global _browser_tool_instance
    if _browser_tool_instance is None:
        with _browser_tool_lock:
            # Double-check locking pattern
            if _browser_tool_instance is None:
                _browser_tool_instance = BrowserTool()
    return _browser_tool_instance


def get_shared_patent_tool() -> PatentSearchTool:
    """Get or create the shared PatentSearchTool instance (thread-safe)."""
    global _patent_tool_instance
    if _patent_tool_instance is None:
        with _patent_tool_lock:
            # Double-check locking pattern
            if _patent_tool_instance is None:
                _patent_tool_instance = PatentSearchTool()
    return _patent_tool_instance


def reset_shared_tools():
    """Reset all shared tools (useful for testing)."""
    global _search_tool_instance, _browser_tool_instance, _local_search_tool_instance, _patent_tool_instance
    with _search_tool_lock:
        _search_tool_instance = None
    with _local_search_tool_lock:
        _local_search_tool_instance = None
    with _browser_tool_lock:
        _browser_tool_instance = None
    with _patent_tool_lock:
        _patent_tool_instance = None
    # Also reset the search manager and github tool singletons
    reset_search_manager()
    reset_github_tool()
