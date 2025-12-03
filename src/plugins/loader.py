"""
Plugin discovery and loading system.

Automatically discovers and loads plugins from the plugins directory.
"""

import importlib.util
import json
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..core.logging import setup_logger
from .base import BaseTool

logger = setup_logger("plugin_loader")

# Default plugins directory relative to project root
DEFAULT_PLUGINS_DIR = "plugins"


class PluginManifest:
    """Represents a plugin manifest.json file."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        entry_point: str,
        author: str = "",
        dependencies: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.entry_point = entry_point
        self.author = author
        self.dependencies = dependencies or []

    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        """Load manifest from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_fields = ["name", "version", "description", "entry_point"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Manifest missing required field: {field}")

        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            entry_point=data["entry_point"],
            author=data.get("author", ""),
            dependencies=data.get("dependencies", []),
        )


class PluginLoader:
    """
    Discovers and loads plugins from a directory.

    Plugins can be:
    1. A single Python file with a class inheriting from BaseTool
    2. A directory with a manifest.json and entry point module
    """

    def __init__(self, plugins_dir: Optional[str] = None):
        """
        Initialize the plugin loader.

        Args:
            plugins_dir: Path to the plugins directory. Defaults to 'plugins/' in project root.
        """
        if plugins_dir:
            self.plugins_dir = Path(plugins_dir)
        else:
            # Find project root and use default plugins dir
            self.plugins_dir = self._find_project_root() / DEFAULT_PLUGINS_DIR

        self._plugins: Dict[str, BaseTool] = {}
        self._lock = threading.Lock()
        self._loaded = False

    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        # Start from this file's directory and go up
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        # Fallback to current working directory
        return Path.cwd()

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugins directory.

        Returns:
            List of discovered plugin names.
        """
        if not self.plugins_dir.exists():
            logger.info(f"Plugins directory not found: {self.plugins_dir}")
            return []

        discovered = []

        for item in self.plugins_dir.iterdir():
            if item.is_file() and item.suffix == ".py" and not item.name.startswith("_"):
                # Single file plugin
                discovered.append(item.stem)
            elif item.is_dir() and not item.name.startswith("_"):
                # Directory plugin with manifest
                manifest_path = item / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = PluginManifest.from_file(manifest_path)
                        discovered.append(manifest.name)
                    except Exception as e:
                        logger.warning(f"Failed to load manifest from {item}: {e}")

        logger.info(f"Discovered {len(discovered)} plugins: {discovered}")
        return discovered

    def _load_module_from_file(self, path: Path, module_name: str):
        """Load a Python module from a file path."""
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _find_tool_class(self, module) -> Optional[Type[BaseTool]]:
        """Find a BaseTool subclass in a module."""
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseTool)
                and attr is not BaseTool
            ):
                return attr

        return None

    def load_plugin(self, name: str) -> Optional[BaseTool]:
        """
        Load a single plugin by name.

        Args:
            name: Name of the plugin to load.

        Returns:
            The loaded plugin instance, or None if loading failed.
        """
        with self._lock:
            if name in self._plugins:
                return self._plugins[name]

            try:
                # Check for single file plugin
                file_path = self.plugins_dir / f"{name}.py"
                if file_path.exists():
                    return self._load_file_plugin(name, file_path)

                # Check for directory plugin
                dir_path = self.plugins_dir / name
                manifest_path = dir_path / "manifest.json"
                if manifest_path.exists():
                    return self._load_dir_plugin(name, dir_path)

                logger.warning(f"Plugin not found: {name}")
                return None

            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {e}")
                return None

    def _load_file_plugin(self, name: str, path: Path) -> Optional[BaseTool]:
        """Load a plugin from a single Python file."""
        module_name = f"plugins.{name}"
        module = self._load_module_from_file(path, module_name)

        tool_class = self._find_tool_class(module)
        if tool_class is None:
            logger.warning(f"No BaseTool subclass found in {path}")
            return None

        plugin = tool_class()
        self._plugins[plugin.name] = plugin
        logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
        return plugin

    def _load_dir_plugin(self, name: str, path: Path) -> Optional[BaseTool]:
        """Load a plugin from a directory with manifest."""
        manifest = PluginManifest.from_file(path / "manifest.json")

        # Load entry point module
        entry_path = path / manifest.entry_point
        if not entry_path.exists():
            logger.error(f"Entry point not found: {entry_path}")
            return None

        module_name = f"plugins.{manifest.name}"
        module = self._load_module_from_file(entry_path, module_name)

        tool_class = self._find_tool_class(module)
        if tool_class is None:
            logger.warning(f"No BaseTool subclass found in {entry_path}")
            return None

        plugin = tool_class()
        self._plugins[plugin.name] = plugin
        logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
        return plugin

    def load_all(self) -> Dict[str, BaseTool]:
        """
        Load all discovered plugins.

        Returns:
            Dictionary mapping plugin names to plugin instances.
        """
        if self._loaded:
            return self._plugins.copy()

        discovered = self.discover_plugins()
        for name in discovered:
            self.load_plugin(name)

        self._loaded = True
        return self._plugins.copy()

    def get_plugin(self, name: str) -> Optional[BaseTool]:
        """
        Get a loaded plugin by name.

        Args:
            name: Name of the plugin.

        Returns:
            The plugin instance, or None if not found.
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, BaseTool]:
        """
        Get all loaded plugins.

        Returns:
            Dictionary mapping plugin names to plugin instances.
        """
        return self._plugins.copy()

    def reload_plugin(self, name: str) -> Optional[BaseTool]:
        """
        Reload a specific plugin.

        Args:
            name: Name of the plugin to reload.

        Returns:
            The reloaded plugin instance, or None if loading failed.
        """
        with self._lock:
            # Remove from cache
            if name in self._plugins:
                del self._plugins[name]

            # Remove from sys.modules to force reload
            module_name = f"plugins.{name}"
            if module_name in sys.modules:
                del sys.modules[module_name]

        return self.load_plugin(name)


# Global plugin loader instance
_plugin_loader: Optional[PluginLoader] = None
_plugin_loader_lock = threading.Lock()


def get_plugin_loader(plugins_dir: Optional[str] = None) -> PluginLoader:
    """
    Get or create the global plugin loader instance.

    Args:
        plugins_dir: Optional custom plugins directory.

    Returns:
        The global PluginLoader instance.
    """
    global _plugin_loader

    if _plugin_loader is None:
        with _plugin_loader_lock:
            if _plugin_loader is None:
                _plugin_loader = PluginLoader(plugins_dir)

    return _plugin_loader


def reset_plugin_loader():
    """Reset the global plugin loader (useful for testing)."""
    global _plugin_loader
    with _plugin_loader_lock:
        _plugin_loader = None
