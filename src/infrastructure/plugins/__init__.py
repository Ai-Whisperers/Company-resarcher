"""
Plugin system for extending the Company Researcher with custom tools.

Usage:
    from src.plugins import BaseTool, get_plugin_loader

    # Create a custom plugin
    class MyPlugin(BaseTool):
        name = "my_plugin"
        description = "Does something useful"

        async def run(self, **kwargs):
            return "result"

    # Load plugins
    loader = get_plugin_loader()
    plugins = loader.load_all()
"""

from .base import BaseTool
from .loader import (
    PluginLoader,
    PluginManifest,
    get_plugin_loader,
    reset_plugin_loader,
)

__all__ = [
    "BaseTool",
    "PluginLoader",
    "PluginManifest",
    "get_plugin_loader",
    "reset_plugin_loader",
]
