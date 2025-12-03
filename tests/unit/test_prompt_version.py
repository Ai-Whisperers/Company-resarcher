"""Tests for the prompt versioning system."""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from src.core.prompts.prompt_version import (
    Prompt,
    PromptMetadata,
    PromptStore,
    get_prompt,
    get_prompt_store,
    reset_prompt_store,
    save_prompt,
)


class TestPromptMetadata:
    """Tests for PromptMetadata class."""

    def test_create_metadata(self):
        """Test creating metadata."""
        metadata = PromptMetadata(
            version="v1",
            created_at=datetime.now(),
            author="test_user",
            description="Initial version",
        )
        assert metadata.version == "v1"
        assert metadata.author == "test_user"
        assert metadata.tags == []

    def test_metadata_with_model_config(self):
        """Test metadata with model configuration."""
        metadata = PromptMetadata(
            version="v2",
            created_at=datetime.now(),
            model_config={"temperature": 0.7, "top_p": 0.9},
        )
        assert metadata.model_config["temperature"] == 0.7

    def test_to_dict(self):
        """Test serialization to dict."""
        metadata = PromptMetadata(
            version="v1",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            author="user",
            tags=["research", "company"],
        )
        data = metadata.to_dict()
        assert data["version"] == "v1"
        assert data["author"] == "user"
        assert "research" in data["tags"]

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "version": "v3",
            "created_at": "2024-01-15T10:30:00",
            "author": "admin",
            "description": "Updated prompt",
            "model_config": {"temperature": 0.5},
            "tags": ["test"],
            "parent_version": "v2",
            "content_hash": "abc123",
        }
        metadata = PromptMetadata.from_dict(data)
        assert metadata.version == "v3"
        assert metadata.parent_version == "v2"
        assert metadata.content_hash == "abc123"


class TestPrompt:
    """Tests for Prompt class."""

    def test_create_prompt(self):
        """Test creating a prompt."""
        metadata = PromptMetadata(
            version="v1",
            created_at=datetime.now(),
        )
        prompt = Prompt(
            name="test_prompt",
            content="Hello, {name}!",
            metadata=metadata,
        )
        assert prompt.name == "test_prompt"
        assert "{name}" in prompt.content

    def test_render_prompt(self):
        """Test rendering with variables."""
        metadata = PromptMetadata(version="v1", created_at=datetime.now())
        prompt = Prompt(
            name="greeting",
            content="Hello, {name}! Today is {day}.",
            metadata=metadata,
        )
        rendered = prompt.render(name="Alice", day="Monday")
        assert rendered == "Hello, Alice! Today is Monday."

    def test_to_dict(self):
        """Test serialization."""
        metadata = PromptMetadata(version="v1", created_at=datetime.now())
        prompt = Prompt(name="test", content="content", metadata=metadata)
        data = prompt.to_dict()
        assert data["name"] == "test"
        assert data["content"] == "content"
        assert "metadata" in data

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "name": "loaded",
            "content": "Loaded content",
            "metadata": {
                "version": "v2",
                "created_at": "2024-01-01T00:00:00",
            },
        }
        prompt = Prompt.from_dict(data)
        assert prompt.name == "loaded"
        assert prompt.metadata.version == "v2"


class TestPromptStore:
    """Tests for PromptStore class."""

    def setup_method(self):
        """Create temp directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = PromptStore(Path(self.temp_dir))

    def teardown_method(self):
        """Cleanup temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_get_prompt(self):
        """Test saving and retrieving a prompt."""
        prompt = self.store.save(
            name="research_prompt",
            content="Research {company} thoroughly.",
            author="test_user",
            description="Initial research prompt",
        )

        assert prompt.name == "research_prompt"
        assert prompt.metadata.version == "v1"

        # Retrieve it
        loaded = self.store.get("research_prompt")
        assert loaded is not None
        assert loaded.content == "Research {company} thoroughly."

    def test_save_multiple_versions(self):
        """Test saving multiple versions."""
        self.store.save(
            name="versioned",
            content="Version 1 content",
            description="First version",
        )
        self.store.save(
            name="versioned",
            content="Version 2 content",
            description="Second version",
        )
        self.store.save(
            name="versioned",
            content="Version 3 content",
            description="Third version",
        )

        versions = self.store.list_versions("versioned")
        assert len(versions) == 3
        assert "v1" in versions
        assert "v2" in versions
        assert "v3" in versions

    def test_get_specific_version(self):
        """Test getting a specific version."""
        self.store.save(name="multi", content="V1")
        self.store.save(name="multi", content="V2")
        self.store.save(name="multi", content="V3")

        v1 = self.store.get("multi", "v1")
        v2 = self.store.get("multi", "v2")
        latest = self.store.get("multi", "latest")

        assert v1.content == "V1"
        assert v2.content == "V2"
        assert latest.content == "V3"

    def test_get_latest(self):
        """Test getting latest version."""
        self.store.save(name="latest_test", content="Original")
        self.store.save(name="latest_test", content="Updated")

        prompt = self.store.get("latest_test")
        assert prompt.content == "Updated"

    def test_list_prompts(self):
        """Test listing all prompts."""
        self.store.save(name="prompt_a", content="A")
        self.store.save(name="prompt_b", content="B")
        self.store.save(name="prompt_c", content="C")

        prompts = self.store.list_prompts()
        assert len(prompts) == 3
        assert "prompt_a" in prompts

    def test_delete_version(self):
        """Test deleting a version."""
        self.store.save(name="deletable", content="V1")
        self.store.save(name="deletable", content="V2")

        success = self.store.delete_version("deletable", "v1")
        assert success is True

        versions = self.store.list_versions("deletable")
        assert "v1" not in versions
        assert "v2" in versions

    def test_delete_nonexistent_version(self):
        """Test deleting nonexistent version."""
        success = self.store.delete_version("nonexistent", "v99")
        assert success is False

    def test_diff_versions(self):
        """Test comparing versions."""
        self.store.save(name="diff_test", content="Line 1\nLine 2")
        self.store.save(name="diff_test", content="Line 1\nLine 2\nLine 3")

        diff = self.store.diff("diff_test", "v1", "v2")

        assert diff is not None
        assert diff["content_changed"] is True
        assert diff["added_lines"] == 1

    def test_search_by_content(self):
        """Test searching prompts by content."""
        self.store.save(name="company_prompt", content="Research the company")
        self.store.save(name="market_prompt", content="Analyze the market")
        self.store.save(name="tech_prompt", content="Review technology")

        results = self.store.search("company")
        assert len(results) == 1
        assert results[0].name == "company_prompt"

    def test_search_by_tags(self):
        """Test searching prompts by tags."""
        self.store.save(
            name="tagged_1",
            content="Content 1",
            tags=["research", "finance"],
        )
        self.store.save(
            name="tagged_2",
            content="Content 2",
            tags=["tech", "analysis"],
        )
        self.store.save(
            name="tagged_3",
            content="Content 3",
            tags=["research", "tech"],
        )

        results = self.store.search("", tags=["research"])
        assert len(results) == 2

    def test_get_nonexistent_prompt(self):
        """Test getting nonexistent prompt returns None."""
        result = self.store.get("does_not_exist")
        assert result is None

    def test_explicit_version(self):
        """Test saving with explicit version."""
        prompt = self.store.save(
            name="explicit_version",
            content="Content",
            version="v10",
        )
        assert prompt.metadata.version == "v10"

    def test_parent_version_tracking(self):
        """Test parent version is tracked."""
        self.store.save(name="lineage", content="V1")
        prompt = self.store.save(name="lineage", content="V2")

        assert prompt.metadata.parent_version == "v1"

    def test_content_hash(self):
        """Test content hash is computed."""
        prompt = self.store.save(name="hashed", content="Test content")
        assert prompt.metadata.content_hash is not None
        assert len(prompt.metadata.content_hash) == 16


class TestGlobalStore:
    """Tests for global store functions."""

    def setup_method(self):
        """Reset and use temp directory."""
        reset_prompt_store()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup."""
        reset_prompt_store()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_prompt_store_singleton(self):
        """Test singleton behavior."""
        store1 = get_prompt_store(Path(self.temp_dir))
        store2 = get_prompt_store()
        assert store1 is store2

    def test_convenience_functions(self):
        """Test save_prompt and get_prompt functions."""
        # Reset and initialize with temp path
        reset_prompt_store()
        store = get_prompt_store(Path(self.temp_dir))

        saved = save_prompt("convenience_test", "Test content")
        assert saved.name == "convenience_test"

        loaded = get_prompt("convenience_test")
        assert loaded is not None
        assert loaded.content == "Test content"
