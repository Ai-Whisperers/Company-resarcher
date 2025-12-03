"""
Event streaming system for real-time agent activity monitoring.

Provides a unified event bus to stream all agent activities (thoughts, tool calls,
logs, errors) to various consumers in real-time.
"""

import asyncio
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from .logger import setup_logger

logger = setup_logger("events")


class EventType(str, Enum):
    """Types of events in the system."""
    # Agent lifecycle
    AGENT_START = "agent.start"
    AGENT_END = "agent.end"
    AGENT_ERROR = "agent.error"

    # Research phases
    RESEARCH_START = "research.start"
    RESEARCH_PROGRESS = "research.progress"
    RESEARCH_COMPLETE = "research.complete"
    RESEARCH_ERROR = "research.error"

    # Tool usage
    TOOL_START = "tool.start"
    TOOL_END = "tool.end"
    TOOL_ERROR = "tool.error"

    # LLM interactions
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    LLM_ERROR = "llm.error"

    # Search activities
    SEARCH_START = "search.start"
    SEARCH_RESULT = "search.result"
    SEARCH_ERROR = "search.error"

    # Content processing
    CONTENT_FETCH = "content.fetch"
    CONTENT_PARSE = "content.parse"
    CONTENT_ANALYZE = "content.analyze"

    # System events
    SYSTEM_LOG = "system.log"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_ERROR = "system.error"

    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """
    Base event class for all system events.

    Attributes:
        type: The event type.
        source: The component that generated the event.
        payload: Event-specific data.
        timestamp: When the event occurred.
        event_id: Unique identifier for the event.
        session_id: Optional session identifier.
        correlation_id: Optional ID for correlating related events.
    """
    type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            type=EventType(data["type"]),
            source=data["source"],
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_id=data.get("event_id", str(uuid4())),
            session_id=data.get("session_id"),
            correlation_id=data.get("correlation_id"),
        )


# Type aliases for subscribers
SyncSubscriber = Callable[[Event], None]
AsyncSubscriber = Callable[[Event], "asyncio.Future[None]"]
EventFilter = Callable[[Event], bool]


@dataclass
class Subscription:
    """Represents a subscription to the event stream."""
    subscriber_id: str
    callback: SyncSubscriber | AsyncSubscriber
    is_async: bool
    filter: Optional[EventFilter] = None
    event_types: Optional[Set[EventType]] = None


class EventStream:
    """
    Central event bus for streaming agent activities.

    Components can publish events and subscribers can receive them in real-time.
    Supports both sync and async subscribers, filtering, and replay.
    """

    def __init__(
        self,
        max_history: int = 1000,
        enable_history: bool = True,
    ):
        """
        Initialize the event stream.

        Args:
            max_history: Maximum events to keep in history.
            enable_history: Whether to keep event history.
        """
        self._subscriptions: Dict[str, Subscription] = {}
        self._history: List[Event] = []
        self._max_history = max_history
        self._enable_history = enable_history
        self._lock = threading.Lock()
        self._current_session_id: Optional[str] = None

    def set_session(self, session_id: str):
        """Set the current session ID for all events."""
        self._current_session_id = session_id

    def subscribe(
        self,
        callback: SyncSubscriber | AsyncSubscriber,
        event_types: Optional[List[EventType]] = None,
        filter_fn: Optional[EventFilter] = None,
        is_async: bool = False,
    ) -> str:
        """
        Subscribe to events.

        Args:
            callback: Function to call when events occur.
            event_types: Optional list of event types to filter.
            filter_fn: Optional custom filter function.
            is_async: Whether the callback is async.

        Returns:
            Subscriber ID for unsubscribing.
        """
        subscriber_id = str(uuid4())
        subscription = Subscription(
            subscriber_id=subscriber_id,
            callback=callback,
            is_async=is_async,
            filter=filter_fn,
            event_types=set(event_types) if event_types else None,
        )

        with self._lock:
            self._subscriptions[subscriber_id] = subscription

        logger.debug(f"Added subscriber {subscriber_id}")
        return subscriber_id

    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscriber_id: ID returned from subscribe().

        Returns:
            True if subscriber was found and removed.
        """
        with self._lock:
            if subscriber_id in self._subscriptions:
                del self._subscriptions[subscriber_id]
                logger.debug(f"Removed subscriber {subscriber_id}")
                return True
        return False

    def publish(self, event: Event):
        """
        Publish an event to all subscribers.

        Args:
            event: The event to publish.
        """
        # Set session ID if not already set
        if event.session_id is None and self._current_session_id:
            event.session_id = self._current_session_id

        # Add to history
        if self._enable_history:
            with self._lock:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]

        # Notify subscribers
        with self._lock:
            subscriptions = list(self._subscriptions.values())

        for sub in subscriptions:
            # Check event type filter
            if sub.event_types and event.type not in sub.event_types:
                continue

            # Check custom filter
            if sub.filter and not sub.filter(event):
                continue

            try:
                if sub.is_async:
                    # Schedule async callback
                    try:
                        loop = asyncio.get_running_loop()
                        asyncio.create_task(sub.callback(event))
                    except RuntimeError:
                        # No running loop
                        pass
                else:
                    sub.callback(event)
            except Exception as e:
                logger.error(f"Error in subscriber {sub.subscriber_id}: {e}")

    def emit(
        self,
        event_type: EventType,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Convenience method to create and publish an event.

        Args:
            event_type: The type of event.
            source: The component emitting the event.
            payload: Event data.
            correlation_id: Optional correlation ID.

        Returns:
            The created event.
        """
        event = Event(
            type=event_type,
            source=source,
            payload=payload or {},
            correlation_id=correlation_id,
        )
        self.publish(event)
        return event

    def get_history(
        self,
        event_types: Optional[List[EventType]] = None,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_types: Filter by event types.
            limit: Maximum events to return.
            since: Only return events after this time.

        Returns:
            List of events.
        """
        with self._lock:
            events = list(self._history)

        # Filter by type
        if event_types:
            types_set = set(event_types)
            events = [e for e in events if e.type in types_set]

        # Filter by time
        if since:
            events = [e for e in events if e.timestamp > since]

        # Limit and return most recent
        return events[-limit:]

    def clear_history(self):
        """Clear event history."""
        with self._lock:
            self._history.clear()

    def get_subscriber_count(self) -> int:
        """Get the number of active subscribers."""
        with self._lock:
            return len(self._subscriptions)


# Global event stream instance
_event_stream: Optional[EventStream] = None
_event_stream_lock = threading.Lock()


def get_event_stream() -> EventStream:
    """Get or create the global event stream."""
    global _event_stream
    if _event_stream is None:
        with _event_stream_lock:
            if _event_stream is None:
                _event_stream = EventStream()
    return _event_stream


def reset_event_stream():
    """Reset the global event stream."""
    global _event_stream
    with _event_stream_lock:
        if _event_stream:
            _event_stream.clear_history()
        _event_stream = None


# Convenience functions for common event types
def emit_agent_start(source: str, payload: Optional[Dict] = None):
    """Emit agent start event."""
    get_event_stream().emit(EventType.AGENT_START, source, payload)


def emit_agent_end(source: str, payload: Optional[Dict] = None):
    """Emit agent end event."""
    get_event_stream().emit(EventType.AGENT_END, source, payload)


def emit_research_progress(source: str, message: str, progress: float = 0.0):
    """Emit research progress event."""
    get_event_stream().emit(
        EventType.RESEARCH_PROGRESS,
        source,
        {"message": message, "progress": progress},
    )


def emit_tool_call(source: str, tool_name: str, args: Optional[Dict] = None):
    """Emit tool start event."""
    get_event_stream().emit(
        EventType.TOOL_START,
        source,
        {"tool": tool_name, "args": args or {}},
    )


def emit_error(source: str, error: str, details: Optional[Dict] = None):
    """Emit error event."""
    payload = {"error": error}
    if details:
        payload["details"] = details
    get_event_stream().emit(EventType.SYSTEM_ERROR, source, payload)
