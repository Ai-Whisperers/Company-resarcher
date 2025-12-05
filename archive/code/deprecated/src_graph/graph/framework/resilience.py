from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    """State of the circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation (GR-012).

    Prevents cascading failures by stopping execution when a node
    fails repeatedly.
    """

    failure_threshold: int = 3
    recovery_timeout: float = 60.0  # seconds
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if (
            self.state == CircuitState.CLOSED
            and self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        """Record a success and reset the circuit."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow one trial execution
            return True

        return True
