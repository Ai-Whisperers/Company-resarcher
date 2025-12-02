"""
Local-first synchronization for agent data.

Provides mechanisms to sync data between devices without a central server.
Uses simple file-based sync with conflict resolution.
"""

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import get_settings
from .logger import setup_logger

logger = setup_logger("local_sync")


class ConflictResolution(str, Enum):
    """Strategies for resolving sync conflicts."""

    LAST_WRITE_WINS = "last_write_wins"  # Most recent timestamp wins
    FIRST_WRITE_WINS = "first_write_wins"  # Keep the first version
    MERGE = "merge"  # Attempt to merge (for compatible types)
    MANUAL = "manual"  # Require manual resolution
    KEEP_BOTH = "keep_both"  # Keep both versions


class SyncStatus(str, Enum):
    """Status of a sync operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CONFLICT = "conflict"
    FAILED = "failed"


@dataclass
class SyncItem:
    """An item to be synchronized."""

    item_id: str
    data_type: str  # e.g., "session", "settings", "research"
    content: Dict[str, Any]
    version: int = 1
    checksum: str = ""
    modified_at: datetime = field(default_factory=datetime.now)
    device_id: str = ""
    deleted: bool = False

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Compute content checksum."""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_id": self.item_id,
            "data_type": self.data_type,
            "content": self.content,
            "version": self.version,
            "checksum": self.checksum,
            "modified_at": self.modified_at.isoformat(),
            "device_id": self.device_id,
            "deleted": self.deleted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncItem":
        """Create from dictionary."""
        return cls(
            item_id=data["item_id"],
            data_type=data["data_type"],
            content=data["content"],
            version=data.get("version", 1),
            checksum=data.get("checksum", ""),
            modified_at=datetime.fromisoformat(data["modified_at"]),
            device_id=data.get("device_id", ""),
            deleted=data.get("deleted", False),
        )


@dataclass
class SyncConflict:
    """Represents a sync conflict."""

    item_id: str
    local_item: SyncItem
    remote_item: SyncItem
    resolved: bool = False
    resolution: Optional[SyncItem] = None

    def resolve_last_write_wins(self) -> SyncItem:
        """Resolve using last write wins."""
        if self.local_item.modified_at >= self.remote_item.modified_at:
            self.resolution = self.local_item
        else:
            self.resolution = self.remote_item
        self.resolved = True
        return self.resolution

    def resolve_first_write_wins(self) -> SyncItem:
        """Resolve using first write wins."""
        if self.local_item.modified_at <= self.remote_item.modified_at:
            self.resolution = self.local_item
        else:
            self.resolution = self.remote_item
        self.resolved = True
        return self.resolution


class SyncStore:
    """
    Local file-based sync store.

    Stores sync items in a structured directory.
    """

    def __init__(self, base_path: Optional[Path] = None, device_id: Optional[str] = None):
        """
        Initialize the sync store.

        Args:
            base_path: Base directory for sync data.
            device_id: Unique identifier for this device.
        """
        if base_path is None:
            settings = get_settings()
            base_path = settings.BASE_DIR / ".sync"
        self.base_path = Path(base_path)
        self.device_id = device_id or self._generate_device_id()
        self._lock = threading.Lock()
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure sync directories exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "items").mkdir(exist_ok=True)
        (self.base_path / "pending").mkdir(exist_ok=True)
        (self.base_path / "conflicts").mkdir(exist_ok=True)

    def _generate_device_id(self) -> str:
        """Generate a unique device ID."""
        device_file = self.base_path / "device_id"
        if device_file.exists():
            return device_file.read_text().strip()

        import uuid
        device_id = str(uuid.uuid4())[:8]
        self._ensure_directory()
        device_file.write_text(device_id)
        return device_id

    def _get_item_path(self, item_id: str) -> Path:
        """Get the path for an item."""
        return self.base_path / "items" / f"{item_id}.json"

    def save(self, item: SyncItem) -> SyncItem:
        """
        Save an item to the store.

        Args:
            item: Item to save.

        Returns:
            The saved item with updated metadata.
        """
        with self._lock:
            item.device_id = self.device_id
            item.modified_at = datetime.now()
            item.checksum = item._compute_checksum()

            # Check for existing item
            existing = self.get(item.item_id)
            if existing:
                item.version = existing.version + 1

            # Save to file
            item_path = self._get_item_path(item.item_id)
            item_path.write_text(
                json.dumps(item.to_dict(), indent=2),
                encoding="utf-8",
            )

            # Add to pending sync
            self._add_to_pending(item)

            logger.debug(f"Saved item {item.item_id} v{item.version}")
            return item

    def get(self, item_id: str) -> Optional[SyncItem]:
        """
        Get an item from the store.

        Args:
            item_id: ID of the item to get.

        Returns:
            The item or None if not found.
        """
        item_path = self._get_item_path(item_id)
        if not item_path.exists():
            return None

        try:
            with open(item_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SyncItem.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load item {item_id}: {e}")
            return None

    def delete(self, item_id: str) -> bool:
        """
        Mark an item as deleted (soft delete for sync).

        Args:
            item_id: ID of the item to delete.

        Returns:
            True if successful.
        """
        item = self.get(item_id)
        if not item:
            return False

        item.deleted = True
        self.save(item)
        return True

    def list_items(
        self,
        data_type: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[SyncItem]:
        """
        List items in the store.

        Args:
            data_type: Filter by data type.
            include_deleted: Include soft-deleted items.

        Returns:
            List of items.
        """
        items = []
        items_dir = self.base_path / "items"

        if not items_dir.exists():
            return items

        for item_file in items_dir.glob("*.json"):
            try:
                with open(item_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                item = SyncItem.from_dict(data)

                if data_type and item.data_type != data_type:
                    continue
                if not include_deleted and item.deleted:
                    continue

                items.append(item)
            except Exception as e:
                logger.error(f"Failed to load {item_file}: {e}")

        return items

    def _add_to_pending(self, item: SyncItem):
        """Add an item to pending sync queue."""
        pending_path = self.base_path / "pending" / f"{item.item_id}.json"
        pending_path.write_text(
            json.dumps(item.to_dict(), indent=2),
            encoding="utf-8",
        )

    def get_pending_items(self) -> List[SyncItem]:
        """Get items pending sync."""
        items = []
        pending_dir = self.base_path / "pending"

        for item_file in pending_dir.glob("*.json"):
            try:
                with open(item_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items.append(SyncItem.from_dict(data))
            except Exception as e:
                logger.error(f"Failed to load pending {item_file}: {e}")

        return items

    def clear_pending(self, item_id: str):
        """Clear an item from pending."""
        pending_path = self.base_path / "pending" / f"{item_id}.json"
        if pending_path.exists():
            pending_path.unlink()


class SyncManager:
    """
    Manages synchronization between local store and remote sources.

    Supports multiple sync targets (folder, cloud storage, etc.).
    """

    def __init__(
        self,
        local_store: Optional[SyncStore] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
    ):
        """
        Initialize the sync manager.

        Args:
            local_store: Local sync store.
            conflict_resolution: Default conflict resolution strategy.
        """
        self.local_store = local_store or SyncStore()
        self.conflict_resolution = conflict_resolution
        self._sync_targets: Dict[str, Path] = {}
        self._conflicts: List[SyncConflict] = []
        self._lock = threading.Lock()

    def add_sync_target(self, name: str, path: Path):
        """
        Add a sync target (folder to sync with).

        Args:
            name: Name for the target.
            path: Path to the sync folder.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self._sync_targets[name] = path
        logger.info(f"Added sync target '{name}': {path}")

    def remove_sync_target(self, name: str):
        """Remove a sync target."""
        self._sync_targets.pop(name, None)

    def sync(self, target_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform synchronization.

        Args:
            target_name: Specific target to sync (all if None).

        Returns:
            Sync results summary.
        """
        results = {
            "synced": 0,
            "conflicts": 0,
            "errors": 0,
            "targets": [],
        }

        targets = (
            {target_name: self._sync_targets[target_name]}
            if target_name and target_name in self._sync_targets
            else self._sync_targets
        )

        for name, target_path in targets.items():
            target_result = self._sync_with_target(name, target_path)
            results["synced"] += target_result["synced"]
            results["conflicts"] += target_result["conflicts"]
            results["errors"] += target_result["errors"]
            results["targets"].append({"name": name, **target_result})

        return results

    def _sync_with_target(self, name: str, target_path: Path) -> Dict[str, Any]:
        """Sync with a specific target."""
        result = {"synced": 0, "conflicts": 0, "errors": 0}

        with self._lock:
            # Ensure target has items directory
            target_items = target_path / "items"
            target_items.mkdir(parents=True, exist_ok=True)

            # Get local and remote items
            local_items = {i.item_id: i for i in self.local_store.list_items(include_deleted=True)}
            remote_items = self._load_remote_items(target_items)

            # Find items to sync
            all_ids = set(local_items.keys()) | set(remote_items.keys())

            for item_id in all_ids:
                local = local_items.get(item_id)
                remote = remote_items.get(item_id)

                try:
                    if local and not remote:
                        # Push local to remote
                        self._write_remote_item(target_items, local)
                        result["synced"] += 1

                    elif remote and not local:
                        # Pull remote to local
                        self.local_store.save(remote)
                        self.local_store.clear_pending(item_id)
                        result["synced"] += 1

                    elif local and remote:
                        # Both exist - check for conflict
                        if local.checksum != remote.checksum:
                            if local.version == remote.version:
                                # True conflict
                                conflict = SyncConflict(
                                    item_id=item_id,
                                    local_item=local,
                                    remote_item=remote,
                                )
                                resolved = self._resolve_conflict(conflict)
                                self._write_remote_item(target_items, resolved)
                                self.local_store.save(resolved)
                                self.local_store.clear_pending(item_id)
                                result["conflicts"] += 1
                            elif local.version > remote.version:
                                # Local is newer
                                self._write_remote_item(target_items, local)
                                result["synced"] += 1
                            else:
                                # Remote is newer
                                self.local_store.save(remote)
                                self.local_store.clear_pending(item_id)
                                result["synced"] += 1

                except Exception as e:
                    logger.error(f"Sync error for {item_id}: {e}")
                    result["errors"] += 1

        logger.info(f"Synced with '{name}': {result}")
        return result

    def _load_remote_items(self, target_items: Path) -> Dict[str, SyncItem]:
        """Load items from remote target."""
        items = {}
        for item_file in target_items.glob("*.json"):
            try:
                with open(item_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                item = SyncItem.from_dict(data)
                items[item.item_id] = item
            except Exception as e:
                logger.error(f"Failed to load remote {item_file}: {e}")
        return items

    def _write_remote_item(self, target_items: Path, item: SyncItem):
        """Write an item to remote target."""
        item_path = target_items / f"{item.item_id}.json"
        item_path.write_text(
            json.dumps(item.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _resolve_conflict(self, conflict: SyncConflict) -> SyncItem:
        """Resolve a sync conflict."""
        self._conflicts.append(conflict)

        if self.conflict_resolution == ConflictResolution.LAST_WRITE_WINS:
            return conflict.resolve_last_write_wins()
        elif self.conflict_resolution == ConflictResolution.FIRST_WRITE_WINS:
            return conflict.resolve_first_write_wins()
        else:
            # Default to last write wins
            return conflict.resolve_last_write_wins()

    def get_conflicts(self) -> List[SyncConflict]:
        """Get unresolved conflicts."""
        return [c for c in self._conflicts if not c.resolved]

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        pending = self.local_store.get_pending_items()
        return {
            "device_id": self.local_store.device_id,
            "pending_count": len(pending),
            "targets": list(self._sync_targets.keys()),
            "conflict_count": len(self.get_conflicts()),
        }


# Global sync manager
_sync_manager: Optional[SyncManager] = None
_manager_lock = threading.Lock()


def get_sync_manager() -> SyncManager:
    """Get or create the global sync manager."""
    global _sync_manager
    if _sync_manager is None:
        with _manager_lock:
            if _sync_manager is None:
                _sync_manager = SyncManager()
    return _sync_manager


def reset_sync_manager():
    """Reset the global sync manager."""
    global _sync_manager
    with _manager_lock:
        _sync_manager = None
