"""Tests for the file system watcher."""

import asyncio
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

from src.core.file_watcher import (
    FileEvent,
    FileEventType,
    FileWatcher,
    format_file_event_message,
    get_file_watcher,
    reset_file_watcher,
)


class TestFileEvent:
    """Tests for FileEvent class."""

    def test_create_event(self):
        """Test creating a file event."""
        event = FileEvent(
            event_type=FileEventType.CREATED,
            path=Path("/test/file.txt"),
        )
        assert event.event_type == FileEventType.CREATED
        assert event.path == Path("/test/file.txt")
        assert event.timestamp is not None
        assert event.is_directory is False

    def test_event_with_old_path(self):
        """Test move event with old path."""
        event = FileEvent(
            event_type=FileEventType.MOVED,
            path=Path("/test/new.txt"),
            old_path=Path("/test/old.txt"),
        )
        assert event.old_path == Path("/test/old.txt")

    def test_to_dict(self):
        """Test serialization to dict."""
        event = FileEvent(
            event_type=FileEventType.MODIFIED,
            path=Path("/test/file.py"),
            is_directory=False,
        )
        data = event.to_dict()
        assert data["event_type"] == "modified"
        assert "/test/file.py" in data["path"]
        assert "timestamp" in data


class TestFileEventType:
    """Tests for FileEventType enum."""

    def test_all_types_exist(self):
        """Test all expected types are defined."""
        expected = ["created", "modified", "deleted", "moved"]
        actual = [t.value for t in FileEventType]
        assert set(actual) == set(expected)


class TestFileWatcher:
    """Tests for FileWatcher class."""

    def setup_method(self):
        """Create temp directory for tests."""
        reset_file_watcher()
        self.temp_dir = tempfile.mkdtemp()
        self.watch_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup temp directory."""
        reset_file_watcher()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_watcher(self):
        """Test creating a file watcher."""
        watcher = FileWatcher(self.watch_path)
        assert watcher.watch_path == self.watch_path
        assert not watcher.is_watching()

    def test_default_ignore_patterns(self):
        """Test default ignore patterns."""
        watcher = FileWatcher(self.watch_path)
        assert "*.pyc" in watcher.ignore_patterns
        assert "__pycache__" in watcher.ignore_patterns
        assert ".git" in watcher.ignore_patterns

    def test_custom_patterns(self):
        """Test custom patterns."""
        watcher = FileWatcher(
            self.watch_path,
            patterns=["*.py", "*.md"],
            ignore_patterns=["test_*.py"],
        )
        assert "*.py" in watcher.patterns
        assert "test_*.py" in watcher.ignore_patterns

    def test_should_watch_file_basic(self):
        """Test file filtering with no patterns."""
        watcher = FileWatcher(self.watch_path, ignore_patterns=[])

        assert watcher._should_watch_file(Path("file.py")) is True
        assert watcher._should_watch_file(Path("file.txt")) is True

    def test_should_watch_file_with_patterns(self):
        """Test file filtering with include patterns."""
        watcher = FileWatcher(
            self.watch_path,
            patterns=["*.py"],
            ignore_patterns=[],
        )

        assert watcher._should_watch_file(Path("file.py")) is True
        assert watcher._should_watch_file(Path("file.txt")) is False

    def test_should_watch_file_with_ignore(self):
        """Test file filtering with ignore patterns."""
        watcher = FileWatcher(
            self.watch_path,
            ignore_patterns=["*.pyc", "*.log"],
        )

        assert watcher._should_watch_file(Path("file.py")) is True
        assert watcher._should_watch_file(Path("file.pyc")) is False
        assert watcher._should_watch_file(Path("debug.log")) is False

    def test_scan_directory(self):
        """Test directory scanning."""
        # Create some files
        (self.watch_path / "file1.txt").write_text("content1")
        (self.watch_path / "file2.py").write_text("content2")

        watcher = FileWatcher(self.watch_path, ignore_patterns=[])
        states = watcher._scan_directory()

        assert len(states) >= 2
        assert any("file1.txt" in path for path in states)
        assert any("file2.py" in path for path in states)

    def test_detect_changes_created(self):
        """Test detecting created files."""
        watcher = FileWatcher(self.watch_path)

        old_states = {}
        new_states = {"/test/new_file.txt": 12345.0}

        events = watcher._detect_changes(old_states, new_states)

        assert len(events) == 1
        assert events[0].event_type == FileEventType.CREATED

    def test_detect_changes_deleted(self):
        """Test detecting deleted files."""
        watcher = FileWatcher(self.watch_path)

        old_states = {"/test/deleted.txt": 12345.0}
        new_states = {}

        events = watcher._detect_changes(old_states, new_states)

        assert len(events) == 1
        assert events[0].event_type == FileEventType.DELETED

    def test_detect_changes_modified(self):
        """Test detecting modified files."""
        watcher = FileWatcher(self.watch_path)

        old_states = {"/test/file.txt": 12345.0}
        new_states = {"/test/file.txt": 12346.0}  # Different mtime

        events = watcher._detect_changes(old_states, new_states)

        assert len(events) == 1
        assert events[0].event_type == FileEventType.MODIFIED

    def test_detect_changes_no_change(self):
        """Test no changes detected."""
        watcher = FileWatcher(self.watch_path)

        states = {"/test/file.txt": 12345.0}

        events = watcher._detect_changes(states, states.copy())

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_subscribe_callback(self):
        """Test subscribing to events."""
        watcher = FileWatcher(self.watch_path, poll_interval=0.1)
        received_events = []

        async def on_event(event):
            received_events.append(event)

        watcher.subscribe(on_event)

        # Start watcher
        await watcher.start_async()

        # Create a file
        (self.watch_path / "new_file.txt").write_text("content")

        # Wait for detection
        await asyncio.sleep(0.3)

        watcher.stop()

        assert len(received_events) >= 1
        assert any(e.event_type == FileEventType.CREATED for e in received_events)

    @pytest.mark.asyncio
    async def test_stop_watcher(self):
        """Test stopping the watcher."""
        watcher = FileWatcher(self.watch_path, poll_interval=0.1)

        await watcher.start_async()
        assert watcher.is_watching()

        watcher.stop()
        await asyncio.sleep(0.2)  # Give time for task to cancel

        assert not watcher.is_watching()

    def test_get_history(self):
        """Test getting event history."""
        watcher = FileWatcher(self.watch_path)

        # Add some events to history manually
        for i in range(5):
            event = FileEvent(
                event_type=FileEventType.MODIFIED if i % 2 == 0 else FileEventType.CREATED,
                path=Path(f"/test/file{i}.txt"),
            )
            watcher._event_history.append(event)

        history = watcher.get_history()
        assert len(history) == 5

        modified_only = watcher.get_history(event_types=[FileEventType.MODIFIED])
        assert len(modified_only) == 3

    def test_get_history_limit(self):
        """Test history limit."""
        watcher = FileWatcher(self.watch_path)

        for i in range(10):
            event = FileEvent(
                event_type=FileEventType.CREATED,
                path=Path(f"/test/file{i}.txt"),
            )
            watcher._event_history.append(event)

        history = watcher.get_history(limit=3)
        assert len(history) == 3


class TestFormatEventMessage:
    """Tests for format_file_event_message function."""

    def test_format_created(self):
        """Test formatting created event."""
        event = FileEvent(
            event_type=FileEventType.CREATED,
            path=Path("/test/new_file.txt"),
        )
        message = format_file_event_message(event)
        assert "new_file.txt" in message
        assert "created" in message

    def test_format_modified(self):
        """Test formatting modified event."""
        event = FileEvent(
            event_type=FileEventType.MODIFIED,
            path=Path("/test/changed.py"),
        )
        message = format_file_event_message(event)
        assert "changed.py" in message
        assert "modified" in message

    def test_format_deleted(self):
        """Test formatting deleted event."""
        event = FileEvent(
            event_type=FileEventType.DELETED,
            path=Path("/test/removed.txt"),
        )
        message = format_file_event_message(event)
        assert "removed.txt" in message
        assert "deleted" in message

    def test_format_moved(self):
        """Test formatting moved event."""
        event = FileEvent(
            event_type=FileEventType.MOVED,
            path=Path("/test/new_name.txt"),
            old_path=Path("/test/old_name.txt"),
        )
        message = format_file_event_message(event)
        assert "old_name.txt" in message
        assert "new_name.txt" in message
        assert "moved" in message


class TestGlobalWatcher:
    """Tests for global watcher functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_file_watcher()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup."""
        reset_file_watcher()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_file_watcher_singleton(self):
        """Test singleton behavior."""
        watcher1 = get_file_watcher(Path(self.temp_dir))
        watcher2 = get_file_watcher()
        assert watcher1 is watcher2

    def test_reset_file_watcher(self):
        """Test resetting the singleton."""
        watcher1 = get_file_watcher(Path(self.temp_dir))
        reset_file_watcher()
        watcher2 = get_file_watcher(Path(self.temp_dir))
        assert watcher1 is not watcher2
