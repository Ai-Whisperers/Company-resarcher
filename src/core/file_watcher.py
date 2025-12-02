"""
File system watcher for monitoring workspace changes.

Notifies agents when files are created, modified, or deleted.
"""

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .config import get_settings
from .events import EventType, get_event_stream
from .logger import setup_logger

logger = setup_logger("file_watcher")


class FileEventType(str, Enum):
    """Types of file system events."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """A file system event."""

    event_type: FileEventType
    path: Path
    timestamp: datetime = field(default_factory=datetime.now)
    is_directory: bool = False
    old_path: Optional[Path] = None  # For move events

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "path": str(self.path),
            "timestamp": self.timestamp.isoformat(),
            "is_directory": self.is_directory,
            "old_path": str(self.old_path) if self.old_path else None,
        }


# Callback type for file events
FileEventCallback = Callable[[FileEvent], Awaitable[None]]
SyncFileEventCallback = Callable[[FileEvent], None]


class FileWatcher:
    """
    Watches a directory for file system changes.

    Uses polling-based approach for cross-platform compatibility.
    For production, consider using watchdog library.
    """

    def __init__(
        self,
        watch_path: Optional[Path] = None,
        poll_interval: float = 1.0,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        recursive: bool = True,
    ):
        """
        Initialize the file watcher.

        Args:
            watch_path: Directory to watch.
            poll_interval: Seconds between polls.
            patterns: Glob patterns to include (e.g., ["*.py", "*.md"]).
            ignore_patterns: Glob patterns to exclude (e.g., ["*.pyc", "__pycache__"]).
            recursive: Watch subdirectories.
        """
        if watch_path is None:
            settings = get_settings()
            watch_path = settings.BASE_DIR
        self.watch_path = Path(watch_path)
        self.poll_interval = poll_interval
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns or [
            "*.pyc",
            "__pycache__",
            ".git",
            ".env",
            "*.log",
            ".DS_Store",
            "node_modules",
            "*.tmp",
        ]
        self.recursive = recursive

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: List[FileEventCallback] = []
        self._sync_callbacks: List[SyncFileEventCallback] = []
        self._file_states: Dict[str, float] = {}  # path -> mtime
        self._lock = threading.Lock()
        self._event_history: List[FileEvent] = []
        self._max_history = 100

    def _should_watch_file(self, path: Path) -> bool:
        """Check if file matches watch patterns."""
        path_str = str(path)

        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in path_str or path.match(pattern):
                return False

        # Check include patterns
        if self.patterns:
            return any(path.match(pattern) for pattern in self.patterns)

        return True

    def _scan_directory(self) -> Dict[str, float]:
        """Scan directory and return file states."""
        states = {}

        if not self.watch_path.exists():
            return states

        try:
            if self.recursive:
                paths = self.watch_path.rglob("*")
            else:
                paths = self.watch_path.glob("*")

            for path in paths:
                if path.is_file() and self._should_watch_file(path):
                    try:
                        states[str(path)] = path.stat().st_mtime
                    except (OSError, FileNotFoundError):
                        pass

        except Exception as e:
            logger.error(f"Error scanning directory: {e}")

        return states

    def _detect_changes(
        self, old_states: Dict[str, float], new_states: Dict[str, float]
    ) -> List[FileEvent]:
        """Detect changes between two scans."""
        events = []

        old_paths = set(old_states.keys())
        new_paths = set(new_states.keys())

        # Deleted files
        for path in old_paths - new_paths:
            events.append(
                FileEvent(
                    event_type=FileEventType.DELETED,
                    path=Path(path),
                )
            )

        # New files
        for path in new_paths - old_paths:
            events.append(
                FileEvent(
                    event_type=FileEventType.CREATED,
                    path=Path(path),
                )
            )

        # Modified files
        for path in old_paths & new_paths:
            if old_states[path] != new_states[path]:
                events.append(
                    FileEvent(
                        event_type=FileEventType.MODIFIED,
                        path=Path(path),
                    )
                )

        return events

    async def _poll_loop(self):
        """Main polling loop."""
        logger.info(f"Starting file watcher on {self.watch_path}")

        # Initial scan
        self._file_states = self._scan_directory()

        while self._running:
            try:
                await asyncio.sleep(self.poll_interval)

                if not self._running:
                    break

                # Scan for changes
                new_states = self._scan_directory()
                events = self._detect_changes(self._file_states, new_states)
                self._file_states = new_states

                # Process events
                for event in events:
                    await self._handle_event(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")

        logger.info("File watcher stopped")

    async def _handle_event(self, event: FileEvent):
        """Handle a file event."""
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

        # Emit to event stream
        event_stream = get_event_stream()
        event_stream.emit(
            EventType.SYSTEM_LOG,
            "file_watcher",
            {
                "action": "file_changed",
                **event.to_dict(),
            },
        )

        logger.debug(f"File {event.event_type.value}: {event.path}")

        # Call async callbacks
        for callback in self._callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"File event callback error: {e}")

        # Call sync callbacks
        for callback in self._sync_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Sync file event callback error: {e}")

    def start(self):
        """Start watching in background."""
        if self._running:
            return

        self._running = True

        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._poll_loop())
        except RuntimeError:
            # No running loop - create one in a thread
            def run_in_thread():
                asyncio.run(self._poll_loop())

            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()

    async def start_async(self):
        """Start watching asynchronously."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def subscribe(self, callback: FileEventCallback):
        """Subscribe to file events (async callback)."""
        self._callbacks.append(callback)

    def subscribe_sync(self, callback: SyncFileEventCallback):
        """Subscribe to file events (sync callback)."""
        self._sync_callbacks.append(callback)

    def unsubscribe(self, callback: FileEventCallback):
        """Unsubscribe from file events."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_history(
        self,
        limit: int = 50,
        event_types: Optional[List[FileEventType]] = None,
    ) -> List[FileEvent]:
        """Get event history."""
        with self._lock:
            history = list(self._event_history)

        if event_types:
            history = [e for e in history if e.event_type in event_types]

        return history[-limit:]

    def is_watching(self) -> bool:
        """Check if watcher is active."""
        return self._running


# Global file watcher
_file_watcher: Optional[FileWatcher] = None
_watcher_lock = threading.Lock()


def get_file_watcher(
    watch_path: Optional[Path] = None,
    **kwargs,
) -> FileWatcher:
    """Get or create the global file watcher."""
    global _file_watcher
    if _file_watcher is None:
        with _watcher_lock:
            if _file_watcher is None:
                _file_watcher = FileWatcher(watch_path, **kwargs)
    return _file_watcher


def reset_file_watcher():
    """Reset the global file watcher."""
    global _file_watcher
    with _watcher_lock:
        if _file_watcher:
            _file_watcher.stop()
        _file_watcher = None


# Convenience function to format events for agents
def format_file_event_message(event: FileEvent) -> str:
    """Format a file event as a message for agents."""
    action_map = {
        FileEventType.CREATED: "created",
        FileEventType.MODIFIED: "modified",
        FileEventType.DELETED: "deleted",
        FileEventType.MOVED: "moved",
    }

    action = action_map.get(event.event_type, "changed")
    path = event.path.name  # Just filename for brevity

    if event.event_type == FileEventType.MOVED and event.old_path:
        return f"File '{event.old_path.name}' was moved to '{path}'"

    return f"File '{path}' was {action}"
