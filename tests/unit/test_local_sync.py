"""Tests for the local-first synchronization system."""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from src.core.local_sync import (
    ConflictResolution,
    SyncConflict,
    SyncItem,
    SyncManager,
    SyncStore,
    get_sync_manager,
    reset_sync_manager,
)


class TestSyncItem:
    """Tests for SyncItem class."""

    def test_create_item(self):
        """Test creating a sync item."""
        item = SyncItem(
            item_id="item_1",
            data_type="session",
            content={"name": "Test Session"},
        )
        assert item.item_id == "item_1"
        assert item.data_type == "session"
        assert item.version == 1
        assert item.checksum  # Should be computed

    def test_checksum_changes_with_content(self):
        """Test checksum changes when content changes."""
        item1 = SyncItem(
            item_id="item_1",
            data_type="test",
            content={"value": 1},
        )
        item2 = SyncItem(
            item_id="item_1",
            data_type="test",
            content={"value": 2},
        )
        assert item1.checksum != item2.checksum

    def test_to_dict(self):
        """Test serialization."""
        item = SyncItem(
            item_id="item_1",
            data_type="settings",
            content={"theme": "dark"},
            version=3,
        )
        data = item.to_dict()
        assert data["item_id"] == "item_1"
        assert data["version"] == 3
        assert data["content"]["theme"] == "dark"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "item_id": "item_2",
            "data_type": "research",
            "content": {"company": "Apple"},
            "version": 2,
            "checksum": "abc123",
            "modified_at": "2024-01-01T12:00:00",
            "device_id": "device_1",
            "deleted": False,
        }
        item = SyncItem.from_dict(data)
        assert item.item_id == "item_2"
        assert item.version == 2
        assert item.device_id == "device_1"


class TestSyncConflict:
    """Tests for SyncConflict class."""

    def test_resolve_last_write_wins(self):
        """Test last write wins resolution."""
        local = SyncItem(
            item_id="item_1",
            data_type="test",
            content={"local": True},
            modified_at=datetime.now(),
        )
        remote = SyncItem(
            item_id="item_1",
            data_type="test",
            content={"remote": True},
            modified_at=datetime.now() - timedelta(hours=1),
        )

        conflict = SyncConflict(
            item_id="item_1",
            local_item=local,
            remote_item=remote,
        )

        resolved = conflict.resolve_last_write_wins()
        assert resolved == local
        assert conflict.resolved

    def test_resolve_first_write_wins(self):
        """Test first write wins resolution."""
        local = SyncItem(
            item_id="item_1",
            data_type="test",
            content={"local": True},
            modified_at=datetime.now(),
        )
        remote = SyncItem(
            item_id="item_1",
            data_type="test",
            content={"remote": True},
            modified_at=datetime.now() - timedelta(hours=1),
        )

        conflict = SyncConflict(
            item_id="item_1",
            local_item=local,
            remote_item=remote,
        )

        resolved = conflict.resolve_first_write_wins()
        assert resolved == remote


class TestSyncStore:
    """Tests for SyncStore class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = SyncStore(Path(self.temp_dir))

    def teardown_method(self):
        """Cleanup temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_get(self):
        """Test saving and retrieving an item."""
        item = SyncItem(
            item_id="test_1",
            data_type="session",
            content={"name": "Test"},
        )
        saved = self.store.save(item)

        assert saved.device_id == self.store.device_id
        assert saved.version == 1

        loaded = self.store.get("test_1")
        assert loaded is not None
        assert loaded.content["name"] == "Test"

    def test_version_increment(self):
        """Test version increments on update."""
        item = SyncItem(
            item_id="versioned",
            data_type="test",
            content={"v": 1},
        )
        self.store.save(item)

        item.content = {"v": 2}
        saved = self.store.save(item)

        assert saved.version == 2

    def test_delete_soft(self):
        """Test soft delete."""
        item = SyncItem(
            item_id="deletable",
            data_type="test",
            content={"data": "test"},
        )
        self.store.save(item)

        success = self.store.delete("deletable")
        assert success

        loaded = self.store.get("deletable")
        assert loaded.deleted

    def test_list_items(self):
        """Test listing items."""
        for i in range(3):
            self.store.save(SyncItem(
                item_id=f"item_{i}",
                data_type="test",
                content={"index": i},
            ))

        items = self.store.list_items()
        assert len(items) == 3

    def test_list_items_by_type(self):
        """Test filtering by type."""
        self.store.save(SyncItem(
            item_id="session_1",
            data_type="session",
            content={},
        ))
        self.store.save(SyncItem(
            item_id="settings_1",
            data_type="settings",
            content={},
        ))

        sessions = self.store.list_items(data_type="session")
        assert len(sessions) == 1
        assert sessions[0].data_type == "session"

    def test_list_items_exclude_deleted(self):
        """Test excluding deleted items."""
        self.store.save(SyncItem(
            item_id="active",
            data_type="test",
            content={},
        ))
        self.store.save(SyncItem(
            item_id="deleted",
            data_type="test",
            content={},
        ))
        self.store.delete("deleted")

        items = self.store.list_items(include_deleted=False)
        assert len(items) == 1

        items = self.store.list_items(include_deleted=True)
        assert len(items) == 2

    def test_pending_items(self):
        """Test pending items tracking."""
        item = SyncItem(
            item_id="pending_test",
            data_type="test",
            content={},
        )
        self.store.save(item)

        pending = self.store.get_pending_items()
        assert len(pending) == 1

        self.store.clear_pending("pending_test")
        pending = self.store.get_pending_items()
        assert len(pending) == 0

    def test_device_id_persistence(self):
        """Test device ID is persisted."""
        device_id = self.store.device_id

        # Create new store with same path
        new_store = SyncStore(Path(self.temp_dir))
        assert new_store.device_id == device_id


class TestSyncManager:
    """Tests for SyncManager class."""

    def setup_method(self):
        """Create temp directories."""
        reset_sync_manager()
        self.local_dir = tempfile.mkdtemp()
        self.remote_dir = tempfile.mkdtemp()
        self.local_store = SyncStore(Path(self.local_dir))
        self.manager = SyncManager(local_store=self.local_store)

    def teardown_method(self):
        """Cleanup."""
        reset_sync_manager()
        shutil.rmtree(self.local_dir, ignore_errors=True)
        shutil.rmtree(self.remote_dir, ignore_errors=True)

    def test_add_sync_target(self):
        """Test adding a sync target."""
        self.manager.add_sync_target("backup", Path(self.remote_dir))
        assert "backup" in self.manager._sync_targets

    def test_sync_local_to_remote(self):
        """Test syncing local item to remote."""
        # Add local item
        item = SyncItem(
            item_id="sync_test",
            data_type="test",
            content={"data": "local"},
        )
        self.local_store.save(item)

        # Add sync target and sync
        self.manager.add_sync_target("remote", Path(self.remote_dir))
        result = self.manager.sync()

        assert result["synced"] >= 1

        # Verify item exists in remote
        remote_file = Path(self.remote_dir) / "items" / "sync_test.json"
        assert remote_file.exists()

    def test_sync_remote_to_local(self):
        """Test syncing remote item to local."""
        # Create remote item directly
        remote_items = Path(self.remote_dir) / "items"
        remote_items.mkdir(parents=True, exist_ok=True)

        import json
        remote_item = SyncItem(
            item_id="remote_only",
            data_type="test",
            content={"data": "remote"},
            device_id="other_device",
        )
        (remote_items / "remote_only.json").write_text(
            json.dumps(remote_item.to_dict())
        )

        # Sync
        self.manager.add_sync_target("remote", Path(self.remote_dir))
        result = self.manager.sync()

        assert result["synced"] >= 1

        # Verify item exists locally
        local_item = self.local_store.get("remote_only")
        assert local_item is not None

    def test_sync_conflict_resolution(self):
        """Test conflict resolution during sync."""
        import json

        # Create local item
        local_item = SyncItem(
            item_id="conflict_test",
            data_type="test",
            content={"value": "local"},
            version=1,
        )
        self.local_store.save(local_item)

        # Create conflicting remote item
        remote_items = Path(self.remote_dir) / "items"
        remote_items.mkdir(parents=True, exist_ok=True)

        remote_item = SyncItem(
            item_id="conflict_test",
            data_type="test",
            content={"value": "remote"},
            version=1,
            modified_at=datetime.now() + timedelta(hours=1),  # Newer
            device_id="other_device",
        )
        (remote_items / "conflict_test.json").write_text(
            json.dumps(remote_item.to_dict())
        )

        # Sync with last write wins
        self.manager.add_sync_target("remote", Path(self.remote_dir))
        result = self.manager.sync()

        assert result["conflicts"] >= 1

    def test_get_sync_status(self):
        """Test getting sync status."""
        self.manager.add_sync_target("backup", Path(self.remote_dir))

        status = self.manager.get_sync_status()

        assert "device_id" in status
        assert "pending_count" in status
        assert "backup" in status["targets"]


class TestGlobalSyncManager:
    """Tests for global sync manager functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_sync_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_sync_manager()

    def test_get_sync_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_sync_manager()
        m2 = get_sync_manager()
        assert m1 is m2

    def test_reset_sync_manager(self):
        """Test resetting the singleton."""
        m1 = get_sync_manager()
        reset_sync_manager()
        m2 = get_sync_manager()
        assert m1 is not m2
