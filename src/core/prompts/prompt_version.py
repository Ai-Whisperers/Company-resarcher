"""
Prompt versioning system for managing and tracking prompts.

Provides storage, versioning, and retrieval of prompts with metadata.
"""

import hashlib
import json
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..logging import setup_logger

logger = setup_logger("prompt_version")


@dataclass
class PromptMetadata:
    """Metadata for a prompt version."""

    version: str
    created_at: datetime
    author: Optional[str] = None
    description: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None  # temperature, top_p, etc.
    tags: List[str] = field(default_factory=list)
    parent_version: Optional[str] = None  # For tracking lineage
    content_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "description": self.description,
            "model_config": self.model_config,
            "tags": self.tags,
            "parent_version": self.parent_version,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptMetadata":
        """Create from dictionary."""
        return cls(
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            author=data.get("author"),
            description=data.get("description"),
            model_config=data.get("model_config"),
            tags=data.get("tags", []),
            parent_version=data.get("parent_version"),
            content_hash=data.get("content_hash"),
        )


@dataclass
class Prompt:
    """A versioned prompt."""

    name: str
    content: str
    metadata: PromptMetadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            content=data["content"],
            metadata=PromptMetadata.from_dict(data["metadata"]),
        )

    def render(self, **kwargs) -> str:
        """Render the prompt with variable substitution."""
        content = self.content
        for key, value in kwargs.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content


class PromptStore:
    """
    Manages prompt storage and versioning.

    Supports file-based storage with JSON metadata.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the prompt store.

        Args:
            base_path: Base directory for prompt storage.
        """
        if base_path is None:
            settings = get_settings()
            base_path = settings.BASE_DIR / "prompts"
        self.base_path = Path(base_path)
        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, Prompt]] = {}  # name -> version -> Prompt

    def _ensure_directory(self):
        """Ensure the prompts directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_prompt_dir(self, name: str) -> Path:
        """Get the directory for a prompt."""
        # Sanitize name for filesystem
        safe_name = re.sub(r"[^\w\-]", "_", name)
        return self.base_path / safe_name

    def _compute_hash(self, content: str) -> str:
        """Compute content hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _generate_version(self, existing_versions: List[str]) -> str:
        """Generate the next version number."""
        if not existing_versions:
            return "v1"

        # Extract version numbers
        numbers = []
        for v in existing_versions:
            match = re.match(r"v(\d+)", v)
            if match:
                numbers.append(int(match.group(1)))

        next_num = max(numbers, default=0) + 1
        return f"v{next_num}"

    def save(
        self,
        name: str,
        content: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        version: Optional[str] = None,
    ) -> Prompt:
        """
        Save a new prompt version.

        Args:
            name: Prompt name/identifier.
            content: Prompt content.
            author: Author of this version.
            description: Description of changes.
            model_config: Model configuration.
            tags: Tags for categorization.
            version: Explicit version (auto-generated if not provided).

        Returns:
            The saved Prompt.
        """
        self._ensure_directory()
        prompt_dir = self._get_prompt_dir(name)
        prompt_dir.mkdir(parents=True, exist_ok=True)

        with self._lock:
            # Get existing versions
            existing = self.list_versions(name)

            # Generate version if not provided
            if version is None:
                version = self._generate_version(existing)

            # Get parent version
            parent_version = existing[-1] if existing else None

            # Create metadata
            metadata = PromptMetadata(
                version=version,
                created_at=datetime.now(),
                author=author,
                description=description,
                model_config=model_config,
                tags=tags or [],
                parent_version=parent_version,
                content_hash=self._compute_hash(content),
            )

            # Create prompt
            prompt = Prompt(name=name, content=content, metadata=metadata)

            # Save to filesystem
            version_dir = prompt_dir / version
            version_dir.mkdir(parents=True, exist_ok=True)

            # Save content
            content_file = version_dir / "prompt.txt"
            content_file.write_text(content, encoding="utf-8")

            # Save metadata
            metadata_file = version_dir / "metadata.json"
            metadata_file.write_text(
                json.dumps(metadata.to_dict(), indent=2),
                encoding="utf-8",
            )

            # Update cache
            if name not in self._cache:
                self._cache[name] = {}
            self._cache[name][version] = prompt

            # Update latest symlink/marker
            latest_file = prompt_dir / "latest.txt"
            latest_file.write_text(version, encoding="utf-8")

            logger.info(f"Saved prompt '{name}' version {version}")
            return prompt

    def get(
        self,
        name: str,
        version: str = "latest",
    ) -> Optional[Prompt]:
        """
        Get a prompt by name and version.

        Args:
            name: Prompt name.
            version: Version string or "latest".

        Returns:
            Prompt if found, None otherwise.
        """
        prompt_dir = self._get_prompt_dir(name)

        if not prompt_dir.exists():
            return None

        # Resolve "latest"
        if version == "latest":
            latest_file = prompt_dir / "latest.txt"
            if latest_file.exists():
                version = latest_file.read_text(encoding="utf-8").strip()
            else:
                # Fall back to highest version
                versions = self.list_versions(name)
                if not versions:
                    return None
                version = versions[-1]

        # Check cache
        with self._lock:
            if name in self._cache and version in self._cache[name]:
                return self._cache[name][version]

        # Load from filesystem
        version_dir = prompt_dir / version
        if not version_dir.exists():
            return None

        try:
            content_file = version_dir / "prompt.txt"
            metadata_file = version_dir / "metadata.json"

            content = content_file.read_text(encoding="utf-8")

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)

            metadata = PromptMetadata.from_dict(metadata_dict)
            prompt = Prompt(name=name, content=content, metadata=metadata)

            # Update cache
            with self._lock:
                if name not in self._cache:
                    self._cache[name] = {}
                self._cache[name][version] = prompt

            return prompt

        except Exception as e:
            logger.error(f"Failed to load prompt '{name}' v{version}: {e}")
            return None

    def list_versions(self, name: str) -> List[str]:
        """List all versions of a prompt."""
        prompt_dir = self._get_prompt_dir(name)

        if not prompt_dir.exists():
            return []

        versions = []
        for item in prompt_dir.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                versions.append(item.name)

        # Sort by version number
        versions.sort(key=lambda v: int(re.sub(r"\D", "", v) or 0))
        return versions

    def list_prompts(self) -> List[str]:
        """List all prompt names."""
        self._ensure_directory()

        prompts = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                prompts.append(item.name)

        return sorted(prompts)

    def delete_version(self, name: str, version: str) -> bool:
        """Delete a specific version."""
        prompt_dir = self._get_prompt_dir(name)
        version_dir = prompt_dir / version

        if not version_dir.exists():
            return False

        try:
            import shutil
            shutil.rmtree(version_dir)

            # Update cache
            with self._lock:
                if name in self._cache:
                    self._cache[name].pop(version, None)

            # Update latest if needed
            latest_file = prompt_dir / "latest.txt"
            if latest_file.exists():
                current_latest = latest_file.read_text(encoding="utf-8").strip()
                if current_latest == version:
                    versions = self.list_versions(name)
                    if versions:
                        latest_file.write_text(versions[-1], encoding="utf-8")

            logger.info(f"Deleted prompt '{name}' version {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete prompt '{name}' v{version}: {e}")
            return False

    def diff(
        self,
        name: str,
        version1: str,
        version2: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two versions of a prompt.

        Args:
            name: Prompt name.
            version1: First version.
            version2: Second version.

        Returns:
            Dict with diff information.
        """
        prompt1 = self.get(name, version1)
        prompt2 = self.get(name, version2)

        if not prompt1 or not prompt2:
            return None

        # Simple line-by-line diff
        lines1 = prompt1.content.splitlines()
        lines2 = prompt2.content.splitlines()

        added = []
        removed = []

        # Very basic diff
        for line in lines2:
            if line not in lines1:
                added.append(line)

        for line in lines1:
            if line not in lines2:
                removed.append(line)

        return {
            "version1": version1,
            "version2": version2,
            "added_lines": len(added),
            "removed_lines": len(removed),
            "added": added[:10],  # Show first 10
            "removed": removed[:10],
            "content_changed": prompt1.metadata.content_hash != prompt2.metadata.content_hash,
        }

    def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
    ) -> List[Prompt]:
        """
        Search prompts by content or tags.

        Args:
            query: Search query for content.
            tags: Filter by tags.

        Returns:
            List of matching prompts (latest versions).
        """
        results = []

        for name in self.list_prompts():
            prompt = self.get(name, "latest")
            if not prompt:
                continue

            # Check content match
            if query and query.lower() not in prompt.content.lower():
                continue

            # Check tags
            if tags:
                if not any(tag in prompt.metadata.tags for tag in tags):
                    continue

            results.append(prompt)

        return results


# Global prompt store
_prompt_store: Optional[PromptStore] = None
_store_lock = threading.Lock()


def get_prompt_store(base_path: Optional[Path] = None) -> PromptStore:
    """Get or create the global prompt store."""
    global _prompt_store
    if _prompt_store is None:
        with _store_lock:
            if _prompt_store is None:
                _prompt_store = PromptStore(base_path)
    return _prompt_store


def reset_prompt_store():
    """Reset the global prompt store."""
    global _prompt_store
    with _store_lock:
        _prompt_store = None


# Convenience functions
def get_prompt(name: str, version: str = "latest") -> Optional[Prompt]:
    """Get a prompt from the global store."""
    return get_prompt_store().get(name, version)


def save_prompt(
    name: str,
    content: str,
    **kwargs,
) -> Prompt:
    """Save a prompt to the global store."""
    return get_prompt_store().save(name, content, **kwargs)
