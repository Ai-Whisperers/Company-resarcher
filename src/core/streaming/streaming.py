"""
Streaming Results Support (IMP-009).

Provides real-time progress updates for long-running research tasks.
Supports callbacks, async generators, and event-based updates.

Usage:
    from src.core.streaming.streaming import StreamingContext, StreamEvent

    async def research_with_streaming(urls, callback):
        async with StreamingContext(callback=callback) as stream:
            for url in urls:
                result = await fetch(url)
                await stream.emit(StreamEvent(
                    type="page_complete",
                    data={"url": url, "success": True},
                    progress=stream.progress,
                ))
                yield result

    # Or using async generator
    async for event in streaming_fetch(urls):
        print(f"Progress: {event.progress:.0%}")
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Union
import json

from ..logging import setup_logger

logger = setup_logger("streaming")


class EventType(str, Enum):
    """Types of streaming events."""

    # Progress events
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    # Task-specific events
    PAGE_STARTED = "page_started"
    PAGE_COMPLETE = "page_complete"
    PAGE_FAILED = "page_failed"
    PAGE_SKIPPED = "page_skipped"

    # Research events
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETE = "phase_complete"
    SOURCE_FOUND = "source_found"
    ANALYSIS_UPDATE = "analysis_update"

    # Warnings and info
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class StreamEvent:
    """An event emitted during streaming."""

    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "message": self.message,
            "progress": round(self.progress, 3),
            "timestamp": self.timestamp.isoformat(),
            "task_id": self.task_id,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        """Create from dictionary."""
        return cls(
            type=EventType(data["type"]),
            data=data.get("data", {}),
            message=data.get("message"),
            progress=data.get("progress", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.now(),
            task_id=data.get("task_id"),
        )


# Type for callback functions
StreamCallback = Callable[[StreamEvent], None]
AsyncStreamCallback = Callable[[StreamEvent], Awaitable[None]]


@dataclass
class StreamingProgress:
    """Track progress for a streaming operation."""

    total: int
    completed: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.completed - self.failed - self.skipped)

    @property
    def progress(self) -> float:
        if self.total == 0:
            return 1.0
        return (self.completed + self.failed + self.skipped) / self.total

    @property
    def success_rate(self) -> float:
        processed = self.completed + self.failed
        if processed == 0:
            return 1.0
        return self.completed / processed


class StreamingContext:
    """
    Context manager for streaming operations.

    Manages event emission, progress tracking, and callbacks.

    Usage:
        async with StreamingContext(total=10, callback=my_callback) as stream:
            for item in items:
                result = await process(item)
                stream.completed += 1
                await stream.emit_progress()
    """

    def __init__(
        self,
        total: int = 0,
        task_id: Optional[str] = None,
        callback: Optional[Union[StreamCallback, AsyncStreamCallback]] = None,
        buffer_events: bool = False,
    ):
        """
        Initialize streaming context.

        Args:
            total: Total number of items to process
            task_id: Unique identifier for this task
            callback: Function to call for each event
            buffer_events: If True, store events for later retrieval
        """
        self.progress = StreamingProgress(total=total)
        self.task_id = task_id or f"task_{id(self)}"
        self.callback = callback
        self.buffer_events = buffer_events
        self._events: List[StreamEvent] = []
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._cancelled = False

    async def __aenter__(self) -> "StreamingContext":
        """Enter context and emit start event."""
        self._started_at = datetime.now()
        await self.emit(StreamEvent(
            type=EventType.STARTED,
            message=f"Starting task with {self.progress.total} items",
            task_id=self.task_id,
        ))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and emit completion event."""
        self._completed_at = datetime.now()

        if self._cancelled:
            await self.emit(StreamEvent(
                type=EventType.CANCELLED,
                message="Task was cancelled",
                progress=self.progress.progress,
                task_id=self.task_id,
            ))
        elif exc_type is not None:
            await self.emit(StreamEvent(
                type=EventType.FAILED,
                message=f"Task failed: {exc_val}",
                progress=self.progress.progress,
                data={"error": str(exc_val)},
                task_id=self.task_id,
            ))
        else:
            await self.emit(StreamEvent(
                type=EventType.COMPLETED,
                message=f"Completed {self.progress.completed}/{self.progress.total} items",
                progress=1.0,
                data={
                    "completed": self.progress.completed,
                    "failed": self.progress.failed,
                    "skipped": self.progress.skipped,
                    "success_rate": self.progress.success_rate,
                },
                task_id=self.task_id,
            ))

    async def emit(self, event: StreamEvent) -> None:
        """
        Emit an event.

        Args:
            event: The event to emit
        """
        # Set task_id if not already set
        if event.task_id is None:
            event.task_id = self.task_id

        # Buffer if enabled
        if self.buffer_events:
            self._events.append(event)

        # Call callback if provided
        if self.callback:
            try:
                result = self.callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Stream callback error: {e}")

        # Log significant events
        if event.type in (EventType.STARTED, EventType.COMPLETED, EventType.FAILED):
            logger.info(f"[{self.task_id}] {event.type.value}: {event.message}")

    async def emit_progress(self, message: Optional[str] = None) -> None:
        """Emit a progress update event."""
        await self.emit(StreamEvent(
            type=EventType.PROGRESS,
            message=message or f"Progress: {self.progress.completed}/{self.progress.total}",
            progress=self.progress.progress,
            data={
                "completed": self.progress.completed,
                "remaining": self.progress.remaining,
            },
            task_id=self.task_id,
        ))

    async def emit_page_complete(
        self,
        url: str,
        success: bool,
        data: Optional[Dict] = None,
    ) -> None:
        """Emit a page completion event."""
        if success:
            self.progress.completed += 1
            event_type = EventType.PAGE_COMPLETE
        else:
            self.progress.failed += 1
            event_type = EventType.PAGE_FAILED

        await self.emit(StreamEvent(
            type=event_type,
            message=f"{'Fetched' if success else 'Failed'}: {url}",
            progress=self.progress.progress,
            data={"url": url, "success": success, **(data or {})},
            task_id=self.task_id,
        ))

    def cancel(self) -> None:
        """Mark the task as cancelled."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self._cancelled

    @property
    def events(self) -> List[StreamEvent]:
        """Get buffered events (if buffering enabled)."""
        return self._events.copy()

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self._started_at is None:
            return 0.0
        end = self._completed_at or datetime.now()
        return (end - self._started_at).total_seconds()


async def streaming_fetch(
    urls: List[str],
    fetch_func: Callable,
    max_concurrent: int = 5,
) -> AsyncIterator[StreamEvent]:
    """
    Async generator for streaming fetch operations.

    Yields events as URLs are processed.

    Args:
        urls: List of URLs to fetch
        fetch_func: Async function to fetch a single URL
        max_concurrent: Maximum concurrent fetches

    Yields:
        StreamEvent for each progress update
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    progress = StreamingProgress(total=len(urls))

    yield StreamEvent(
        type=EventType.STARTED,
        message=f"Starting fetch of {len(urls)} URLs",
        data={"total": len(urls)},
    )

    async def fetch_one(url: str) -> tuple:
        async with semaphore:
            try:
                result = await fetch_func(url)
                return url, True, result
            except Exception as e:
                return url, False, str(e)

    # Create all tasks
    tasks = [asyncio.create_task(fetch_one(url)) for url in urls]

    # Process as they complete
    for coro in asyncio.as_completed(tasks):
        url, success, result = await coro

        if success:
            progress.completed += 1
            event_type = EventType.PAGE_COMPLETE
        else:
            progress.failed += 1
            event_type = EventType.PAGE_FAILED

        yield StreamEvent(
            type=event_type,
            message=url,
            progress=progress.progress,
            data={"url": url, "success": success, "result": result if success else None},
        )

    yield StreamEvent(
        type=EventType.COMPLETED,
        message=f"Completed {progress.completed}/{progress.total}",
        progress=1.0,
        data={
            "completed": progress.completed,
            "failed": progress.failed,
            "success_rate": progress.success_rate,
        },
    )


class SSEFormatter:
    """Format events for Server-Sent Events (SSE) streaming."""

    @staticmethod
    def format(event: StreamEvent) -> str:
        """Format event as SSE message."""
        lines = []
        lines.append(f"event: {event.type.value}")
        lines.append(f"data: {event.to_json()}")
        lines.append("")  # Empty line to end message
        return "\n".join(lines) + "\n"

    @staticmethod
    async def stream_events(
        events: AsyncIterator[StreamEvent],
    ) -> AsyncIterator[str]:
        """Convert event stream to SSE format."""
        async for event in events:
            yield SSEFormatter.format(event)


__all__ = [
    "StreamEvent",
    "EventType",
    "StreamingContext",
    "StreamingProgress",
    "StreamCallback",
    "AsyncStreamCallback",
    "streaming_fetch",
    "SSEFormatter",
]
