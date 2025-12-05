from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue (GR-008)."""

    node_name: str
    state_snapshot: Dict[str, Any]
    error: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0


class DeadLetterQueue:
    """
    Dead letter queue for failed node executions (GR-008).

    Stores failed executions for later inspection or manual replay.
    """

    def __init__(self, max_size: int = 100):
        self._queue: List[DeadLetterEntry] = []
        self._max_size = max_size

    def add(
        self,
        node_name: str,
        state_snapshot: Dict[str, Any],
        error: str,
        retry_count: int,
    ) -> None:
        """Add a failed execution to the queue."""
        if len(self._queue) >= self._max_size:
            self._queue.pop(0)  # Remove oldest

        entry = DeadLetterEntry(
            node_name=node_name,
            state_snapshot=state_snapshot,
            error=error,
            retry_count=retry_count,
        )
        self._queue.append(entry)

    def get_all(self) -> List[DeadLetterEntry]:
        """Get all entries."""
        return self._queue.copy()

    def clear(self) -> None:
        """Clear the queue."""
        self._queue.clear()

    def size(self) -> int:
        """Get current queue size."""
        return len(self._queue)
