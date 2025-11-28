"""Tests for the event streaming system."""

import pytest
from datetime import datetime, timedelta

from src.core.events import (
    Event,
    EventType,
    EventStream,
    get_event_stream,
    reset_event_stream,
    emit_agent_start,
    emit_error,
)


class TestEvent:
    """Tests for Event class."""

    def test_create_event(self):
        """Test creating an event."""
        event = Event(
            type=EventType.AGENT_START,
            source="test_agent",
            payload={"message": "Starting"},
        )
        assert event.type == EventType.AGENT_START
        assert event.source == "test_agent"
        assert event.payload["message"] == "Starting"
        assert event.event_id is not None

    def test_event_to_dict(self):
        """Test event serialization."""
        event = Event(
            type=EventType.RESEARCH_PROGRESS,
            source="researcher",
            payload={"progress": 0.5},
        )
        data = event.to_dict()

        assert data["type"] == "research.progress"
        assert data["source"] == "researcher"
        assert data["payload"]["progress"] == 0.5
        assert "timestamp" in data
        assert "event_id" in data

    def test_event_to_json(self):
        """Test JSON serialization."""
        event = Event(
            type=EventType.TOOL_START,
            source="browser",
        )
        json_str = event.to_json()
        assert "tool.start" in json_str
        assert "browser" in json_str

    def test_event_from_dict(self):
        """Test creating event from dict."""
        data = {
            "type": "agent.end",
            "source": "test",
            "payload": {"result": "success"},
            "timestamp": datetime.now().isoformat(),
        }
        event = Event.from_dict(data)

        assert event.type == EventType.AGENT_END
        assert event.source == "test"
        assert event.payload["result"] == "success"


class TestEventStream:
    """Tests for EventStream class."""

    def setup_method(self):
        """Reset event stream before each test."""
        reset_event_stream()

    def test_subscribe_and_publish(self):
        """Test subscribing and receiving events."""
        stream = EventStream()
        received = []

        def on_event(event):
            received.append(event)

        stream.subscribe(on_event)

        event = Event(type=EventType.SYSTEM_LOG, source="test")
        stream.publish(event)

        assert len(received) == 1
        assert received[0].type == EventType.SYSTEM_LOG

    def test_unsubscribe(self):
        """Test unsubscribing."""
        stream = EventStream()
        received = []

        def on_event(event):
            received.append(event)

        sub_id = stream.subscribe(on_event)
        stream.emit(EventType.SYSTEM_LOG, "test")
        assert len(received) == 1

        stream.unsubscribe(sub_id)
        stream.emit(EventType.SYSTEM_LOG, "test")
        assert len(received) == 1  # No new events

    def test_filter_by_event_type(self):
        """Test filtering by event type."""
        stream = EventStream()
        received = []

        def on_event(event):
            received.append(event)

        stream.subscribe(on_event, event_types=[EventType.AGENT_START])

        stream.emit(EventType.AGENT_START, "test")
        stream.emit(EventType.AGENT_END, "test")
        stream.emit(EventType.SYSTEM_LOG, "test")

        assert len(received) == 1
        assert received[0].type == EventType.AGENT_START

    def test_custom_filter(self):
        """Test custom filter function."""
        stream = EventStream()
        received = []

        def on_event(event):
            received.append(event)

        def filter_important(event):
            return event.payload.get("important", False)

        stream.subscribe(on_event, filter_fn=filter_important)

        stream.emit(EventType.SYSTEM_LOG, "test", {"important": True})
        stream.emit(EventType.SYSTEM_LOG, "test", {"important": False})
        stream.emit(EventType.SYSTEM_LOG, "test", {})

        assert len(received) == 1

    def test_emit_returns_event(self):
        """Test that emit returns the created event."""
        stream = EventStream()
        event = stream.emit(EventType.TOOL_START, "browser", {"url": "http://example.com"})

        assert event.type == EventType.TOOL_START
        assert event.payload["url"] == "http://example.com"

    def test_history(self):
        """Test event history."""
        stream = EventStream(enable_history=True, max_history=10)

        for i in range(5):
            stream.emit(EventType.SYSTEM_LOG, "test", {"index": i})

        history = stream.get_history()
        assert len(history) == 5

    def test_history_limit(self):
        """Test history is bounded."""
        stream = EventStream(max_history=5)

        for i in range(10):
            stream.emit(EventType.SYSTEM_LOG, "test", {"index": i})

        history = stream.get_history()
        assert len(history) == 5

    def test_history_filter_by_type(self):
        """Test filtering history by type."""
        stream = EventStream()
        stream.emit(EventType.AGENT_START, "test")
        stream.emit(EventType.SYSTEM_LOG, "test")
        stream.emit(EventType.AGENT_END, "test")

        history = stream.get_history(event_types=[EventType.AGENT_START, EventType.AGENT_END])
        assert len(history) == 2

    def test_history_filter_by_time(self):
        """Test filtering history by time."""
        stream = EventStream()

        # Emit an event
        stream.emit(EventType.SYSTEM_LOG, "test")

        # Get history since a time in the past
        past = datetime.now() - timedelta(hours=1)
        history = stream.get_history(since=past)
        assert len(history) == 1

        # Get history since the future
        future = datetime.now() + timedelta(hours=1)
        history = stream.get_history(since=future)
        assert len(history) == 0

    def test_session_id(self):
        """Test session ID is applied to events."""
        stream = EventStream()
        stream.set_session("session-123")

        event = stream.emit(EventType.SYSTEM_LOG, "test")
        assert event.session_id == "session-123"

    def test_clear_history(self):
        """Test clearing history."""
        stream = EventStream()
        stream.emit(EventType.SYSTEM_LOG, "test")
        stream.emit(EventType.SYSTEM_LOG, "test")

        assert len(stream.get_history()) == 2

        stream.clear_history()
        assert len(stream.get_history()) == 0

    def test_subscriber_count(self):
        """Test getting subscriber count."""
        stream = EventStream()
        assert stream.get_subscriber_count() == 0

        sub1 = stream.subscribe(lambda e: None)
        sub2 = stream.subscribe(lambda e: None)
        assert stream.get_subscriber_count() == 2

        stream.unsubscribe(sub1)
        assert stream.get_subscriber_count() == 1


class TestGlobalEventStream:
    """Tests for global event stream functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_event_stream()

    def test_get_event_stream_singleton(self):
        """Test singleton behavior."""
        stream1 = get_event_stream()
        stream2 = get_event_stream()
        assert stream1 is stream2

    def test_reset_event_stream(self):
        """Test resetting the singleton."""
        stream1 = get_event_stream()
        stream1.emit(EventType.SYSTEM_LOG, "test")

        reset_event_stream()
        stream2 = get_event_stream()
        assert len(stream2.get_history()) == 0


class TestConvenienceFunctions:
    """Tests for convenience emit functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_event_stream()

    def test_emit_agent_start(self):
        """Test emit_agent_start."""
        received = []
        get_event_stream().subscribe(lambda e: received.append(e))

        emit_agent_start("test_agent", {"task": "research"})

        assert len(received) == 1
        assert received[0].type == EventType.AGENT_START

    def test_emit_error(self):
        """Test emit_error."""
        received = []
        get_event_stream().subscribe(lambda e: received.append(e))

        emit_error("test_component", "Something went wrong", {"code": 500})

        assert len(received) == 1
        assert received[0].type == EventType.SYSTEM_ERROR
        assert received[0].payload["error"] == "Something went wrong"
