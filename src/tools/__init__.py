"""
Shared tool instances to reduce resource usage.
Each tool is instantiated once and reused across all agents.
"""

from .search import SearchTool
from .browser import BrowserTool
from .local_search import LocalSearchTool

# Singleton instances
_search_tool_instance = None
_local_search_tool_instance = None
_browser_tool_instance = None


def get_shared_search_tool() -> SearchTool:
    """Get or create the shared SearchTool instance."""
    global _search_tool_instance
    if _search_tool_instance is None:
        _search_tool_instance = SearchTool()
    return _search_tool_instance


def get_shared_local_search_tool() -> LocalSearchTool:
    """Get or create the shared LocalSearchTool instance."""
    global _local_search_tool_instance
    if _local_search_tool_instance is None:
        _local_search_tool_instance = LocalSearchTool()
    return _local_search_tool_instance


def get_shared_browser_tool() -> BrowserTool:
    """Get or create the shared BrowserTool instance."""
    global _browser_tool_instance
    if _browser_tool_instance is None:
        _browser_tool_instance = BrowserTool()
    return _browser_tool_instance


def reset_shared_tools():
    """Reset all shared tools (useful for testing)."""
    global _search_tool_instance, _browser_tool_instance, _local_search_tool_instance
    _search_tool_instance = None
    _browser_tool_instance = None
    _local_search_tool_instance = None
