# Feature: Event Stream

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/events/stream.py`

## Description

A unified event bus to stream all agent activities (thoughts, tool calls, logs, errors) to the UI or other consumers in real-time.

## Implementation Details

1.  **Event Class:** Base `Event` class with `type`, `timestamp`, `source`, `payload`.
2.  **Stream:** A central `EventStream` object that components can `subscribe` to.
3.  **WebSocket:** Bridge the event stream to a WebSocket server for the frontend.

## Code Reference

```python
class EventStream:
    def add_event(self, event):
        for subscriber in self.subscribers:
            subscriber.notify(event)
```
