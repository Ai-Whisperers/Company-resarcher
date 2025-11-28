"""Tests for the plugin system."""

import pytest
import tempfile
import json
from pathlib import Path

from src.plugins import BaseTool, PluginLoader, get_plugin_loader, reset_plugin_loader


class SampleTool(BaseTool):
    """Sample tool for testing."""

    name = "sample_tool"
    description = "A sample tool for testing"
    version = "1.0.0"

    async def run(self, value: str = "default") -> str:
        return f"result: {value}"


class TestBaseTool:
    """Tests for BaseTool base class."""

    def test_tool_requires_name(self):
        """Test that tools must have a name."""

        class NoNameTool(BaseTool):
            description = "No name"

            async def run(self, **kwargs):
                pass

        with pytest.raises(ValueError, match="must define a 'name'"):
            NoNameTool()

    def test_tool_requires_description(self):
        """Test that tools must have a description."""

        class NoDescTool(BaseTool):
            name = "no_desc"

            async def run(self, **kwargs):
                pass

        with pytest.raises(ValueError, match="must define a 'description'"):
            NoDescTool()

    def test_valid_tool_creation(self):
        """Test that valid tools can be created."""
        tool = SampleTool()
        assert tool.name == "sample_tool"
        assert tool.description == "A sample tool for testing"
        assert tool.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_tool_run(self):
        """Test tool execution."""
        tool = SampleTool()
        result = await tool.run(value="test")
        assert result == "result: test"

    @pytest.mark.asyncio
    async def test_tool_execute(self):
        """Test tool execute method."""
        tool = SampleTool()
        result = await tool.execute(value="test")
        assert result == "result: test"

    def test_get_metadata(self):
        """Test metadata extraction."""
        tool = SampleTool()
        metadata = tool.get_metadata()
        assert metadata["name"] == "sample_tool"
        assert metadata["description"] == "A sample tool for testing"
        assert metadata["version"] == "1.0.0"


class TestPluginLoader:
    """Tests for PluginLoader."""

    def setup_method(self):
        """Reset plugin loader before each test."""
        reset_plugin_loader()

    def test_discover_empty_dir(self):
        """Test discovery with empty plugins directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            discovered = loader.discover_plugins()
            assert discovered == []

    def test_discover_nonexistent_dir(self):
        """Test discovery with nonexistent directory."""
        loader = PluginLoader("/nonexistent/path")
        discovered = loader.discover_plugins()
        assert discovered == []

    def test_discover_file_plugin(self):
        """Test discovery of single-file plugins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a plugin file
            plugin_path = Path(tmpdir) / "my_plugin.py"
            plugin_path.write_text("""
from src.plugins import BaseTool

class MyPlugin(BaseTool):
    name = "my_plugin"
    description = "Test plugin"

    async def run(self, **kwargs):
        return "ok"
""")

            loader = PluginLoader(tmpdir)
            discovered = loader.discover_plugins()
            assert "my_plugin" in discovered

    def test_discover_dir_plugin(self):
        """Test discovery of directory plugins with manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory plugin
            plugin_dir = Path(tmpdir) / "custom_tool"
            plugin_dir.mkdir()

            manifest = {
                "name": "custom_tool",
                "version": "2.0.0",
                "description": "A custom tool",
                "entry_point": "main.py",
            }
            (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
            (plugin_dir / "main.py").write_text("""
from src.plugins import BaseTool

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "A custom tool"

    async def run(self, **kwargs):
        return "custom"
""")

            loader = PluginLoader(tmpdir)
            discovered = loader.discover_plugins()
            assert "custom_tool" in discovered

    def test_load_all_returns_dict(self):
        """Test that load_all returns a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            plugins = loader.load_all()
            assert isinstance(plugins, dict)

    def test_get_plugin_returns_none_for_missing(self):
        """Test get_plugin returns None for nonexistent plugin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            loader.load_all()
            assert loader.get_plugin("nonexistent") is None


class TestGlobalPluginLoader:
    """Tests for global plugin loader functions."""

    def setup_method(self):
        """Reset plugin loader before each test."""
        reset_plugin_loader()

    def test_get_plugin_loader_returns_singleton(self):
        """Test that get_plugin_loader returns the same instance."""
        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()
        assert loader1 is loader2

    def test_reset_plugin_loader(self):
        """Test that reset clears the singleton."""
        loader1 = get_plugin_loader()
        reset_plugin_loader()
        loader2 = get_plugin_loader()
        assert loader1 is not loader2
