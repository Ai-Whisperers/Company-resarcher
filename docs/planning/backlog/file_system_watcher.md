# Feature: File System Watcher

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/runtime/utils/observer.py`

## Description

The agent should know when files change (e.g., if a tool writes a file, or if the user edits a file externally).

## Implementation Details

1.  **Watchdog:** Use `watchdog` library to monitor the workspace directory.
2.  **Event Trigger:** When a file is modified/created/deleted, trigger an event.
3.  **Agent Notification:** Inject a system message: "File 'report.md' was modified."

## Code Reference

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        agent.notify(f"File modified: {event.src_path}")
```
