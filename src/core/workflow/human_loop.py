"""
Human-in-the-loop system for agent approval workflows.

Provides mechanisms to pause execution and wait for human approval
before taking critical actions.
"""

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ..config import get_settings
from ..logging.events import EventType, get_event_stream
from ..logging import setup_logger

logger = setup_logger("human_loop")


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalType(str, Enum):
    """Types of actions requiring approval."""

    CRITICAL_ACTION = "critical_action"  # High-risk operations
    DATA_MODIFICATION = "data_modification"  # Changes to data
    EXTERNAL_REQUEST = "external_request"  # External API calls
    REPORT_PUBLISH = "report_publish"  # Publishing reports
    COST_THRESHOLD = "cost_threshold"  # Cost limit exceeded
    CUSTOM = "custom"  # User-defined approval points


@dataclass
class ApprovalRequest:
    """A request for human approval."""

    request_id: str
    action_type: ApprovalType
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolver: Optional[str] = None  # Who approved/rejected
    rejection_reason: Optional[str] = None
    timeout_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "action_type": self.action_type.value,
            "description": self.description,
            "context": self.context,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolver": self.resolver,
            "rejection_reason": self.rejection_reason,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRequest":
        """Create from dictionary."""
        return cls(
            request_id=data["request_id"],
            action_type=ApprovalType(data["action_type"]),
            description=data["description"],
            context=data.get("context", {}),
            status=ApprovalStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            resolved_at=(
                datetime.fromisoformat(data["resolved_at"])
                if data.get("resolved_at")
                else None
            ),
            resolver=data.get("resolver"),
            rejection_reason=data.get("rejection_reason"),
            timeout_seconds=data.get("timeout_seconds"),
        )


# Callback types
ApprovalCallback = Callable[[ApprovalRequest], Awaitable[ApprovalStatus]]
NotificationCallback = Callable[[ApprovalRequest], Awaitable[None]]


class ApprovalManager:
    """
    Manages human-in-the-loop approval workflows.

    Provides mechanisms to:
    - Request approval for critical actions
    - Wait for human response
    - Handle timeouts and cancellations
    """

    def __init__(
        self,
        default_timeout: int = 300,  # 5 minutes
        auto_approve_in_headless: bool = False,
    ):
        """
        Initialize the approval manager.

        Args:
            default_timeout: Default timeout in seconds for approval requests.
            auto_approve_in_headless: Whether to auto-approve in headless mode.
        """
        self.default_timeout = default_timeout
        self.auto_approve_in_headless = auto_approve_in_headless
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._request_events: Dict[str, asyncio.Event] = {}
        self._approval_callback: Optional[ApprovalCallback] = None
        self._notification_callbacks: List[NotificationCallback] = []
        self._lock = threading.Lock()
        self._history: List[ApprovalRequest] = []
        self._max_history = 100

    def set_approval_callback(self, callback: ApprovalCallback):
        """Set the callback for handling approval requests."""
        self._approval_callback = callback

    def add_notification_callback(self, callback: NotificationCallback):
        """Add a callback for approval notifications."""
        self._notification_callbacks.append(callback)

    async def request_approval(
        self,
        action_type: ApprovalType,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> ApprovalRequest:
        """
        Request human approval for an action.

        Args:
            action_type: Type of action requiring approval.
            description: Human-readable description of the action.
            context: Additional context about the action.
            timeout: Timeout in seconds (uses default if not provided).

        Returns:
            ApprovalRequest with final status after resolution.
        """
        settings = get_settings()

        # Auto-approve in headless mode if configured
        if settings.is_headless and self.auto_approve_in_headless:
            logger.info(f"Auto-approving in headless mode: {description}")
            request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                action_type=action_type,
                description=description,
                context=context or {},
                status=ApprovalStatus.APPROVED,
                resolved_at=datetime.now(),
                resolver="auto_headless",
            )
            self._add_to_history(request)
            return request

        # Create the request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            action_type=action_type,
            description=description,
            context=context or {},
            timeout_seconds=timeout or self.default_timeout,
        )

        # Store pending request
        with self._lock:
            self._pending_requests[request.request_id] = request
            self._request_events[request.request_id] = asyncio.Event()

        # Emit event
        event_stream = get_event_stream()
        event_stream.emit(
            EventType.SYSTEM_LOG,
            "approval_manager",
            {
                "action": "approval_requested",
                "request_id": request.request_id,
                "description": description,
            },
        )

        # Notify callbacks
        await self._notify_callbacks(request)

        # Wait for resolution
        try:
            resolved = await self._wait_for_resolution(request)
            return resolved
        finally:
            # Cleanup
            with self._lock:
                self._pending_requests.pop(request.request_id, None)
                self._request_events.pop(request.request_id, None)

    async def _wait_for_resolution(
        self, request: ApprovalRequest
    ) -> ApprovalRequest:
        """Wait for the request to be resolved."""
        event = self._request_events.get(request.request_id)
        if not event:
            return request

        # If we have a custom approval callback, use it
        if self._approval_callback:
            try:
                status = await asyncio.wait_for(
                    self._approval_callback(request),
                    timeout=request.timeout_seconds,
                )
                request.status = status
                request.resolved_at = datetime.now()
            except asyncio.TimeoutError:
                request.status = ApprovalStatus.TIMEOUT
                request.resolved_at = datetime.now()
                logger.warning(f"Approval request timed out: {request.request_id}")
        else:
            # Wait for external resolution via approve/reject methods
            try:
                await asyncio.wait_for(
                    event.wait(),
                    timeout=request.timeout_seconds,
                )
            except asyncio.TimeoutError:
                request.status = ApprovalStatus.TIMEOUT
                request.resolved_at = datetime.now()
                logger.warning(f"Approval request timed out: {request.request_id}")

        self._add_to_history(request)
        return request

    async def _notify_callbacks(self, request: ApprovalRequest):
        """Notify all registered callbacks about a new request."""
        for callback in self._notification_callbacks:
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")

    def approve(
        self,
        request_id: str,
        resolver: Optional[str] = None,
    ) -> bool:
        """
        Approve a pending request.

        Args:
            request_id: ID of the request to approve.
            resolver: Identifier of who approved.

        Returns:
            True if request was found and approved.
        """
        with self._lock:
            request = self._pending_requests.get(request_id)
            if not request or request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.APPROVED
            request.resolved_at = datetime.now()
            request.resolver = resolver

            event = self._request_events.get(request_id)
            if event:
                event.set()

        logger.info(f"Request approved: {request_id} by {resolver}")
        return True

    def reject(
        self,
        request_id: str,
        reason: Optional[str] = None,
        resolver: Optional[str] = None,
    ) -> bool:
        """
        Reject a pending request.

        Args:
            request_id: ID of the request to reject.
            reason: Reason for rejection.
            resolver: Identifier of who rejected.

        Returns:
            True if request was found and rejected.
        """
        with self._lock:
            request = self._pending_requests.get(request_id)
            if not request or request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.REJECTED
            request.resolved_at = datetime.now()
            request.resolver = resolver
            request.rejection_reason = reason

            event = self._request_events.get(request_id)
            if event:
                event.set()

        logger.info(f"Request rejected: {request_id} - {reason}")
        return True

    def cancel(self, request_id: str) -> bool:
        """Cancel a pending request."""
        with self._lock:
            request = self._pending_requests.get(request_id)
            if not request or request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.CANCELLED
            request.resolved_at = datetime.now()

            event = self._request_events.get(request_id)
            if event:
                event.set()

        logger.info(f"Request cancelled: {request_id}")
        return True

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        with self._lock:
            return [
                r for r in self._pending_requests.values()
                if r.status == ApprovalStatus.PENDING
            ]

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request by ID."""
        with self._lock:
            return self._pending_requests.get(request_id)

    def get_history(
        self,
        limit: int = 50,
        status_filter: Optional[ApprovalStatus] = None,
    ) -> List[ApprovalRequest]:
        """Get approval history."""
        with self._lock:
            history = list(self._history)

        if status_filter:
            history = [r for r in history if r.status == status_filter]

        return history[-limit:]

    def _add_to_history(self, request: ApprovalRequest):
        """Add a resolved request to history."""
        with self._lock:
            self._history.append(request)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]


# Convenience functions for common approval patterns
async def require_approval(
    description: str,
    action_type: ApprovalType = ApprovalType.CRITICAL_ACTION,
    context: Optional[Dict[str, Any]] = None,
    manager: Optional[ApprovalManager] = None,
) -> bool:
    """
    Require approval before proceeding.

    Args:
        description: Description of the action.
        action_type: Type of action.
        context: Additional context.
        manager: Approval manager to use.

    Returns:
        True if approved, False otherwise.
    """
    mgr = manager or get_approval_manager()
    request = await mgr.request_approval(action_type, description, context)
    return request.status == ApprovalStatus.APPROVED


def format_approval_for_cli(request: ApprovalRequest) -> str:
    """Format an approval request for CLI display."""
    lines = [
        f"\n{'='*60}",
        f"APPROVAL REQUIRED",
        f"{'='*60}",
        f"ID: {request.request_id[:8]}...",
        f"Type: {request.action_type.value}",
        f"",
        f"Description:",
        f"  {request.description}",
    ]

    if request.context:
        lines.append("")
        lines.append("Context:")
        for key, value in request.context.items():
            lines.append(f"  {key}: {value}")

    if request.timeout_seconds:
        lines.append("")
        lines.append(f"Timeout: {request.timeout_seconds} seconds")

    lines.extend([
        "",
        "Enter 'y' to approve, 'n' to reject, or 'c' to cancel:",
        f"{'='*60}",
    ])

    return "\n".join(lines)


async def cli_approval_callback(request: ApprovalRequest) -> ApprovalStatus:
    """Default CLI callback for approval requests."""
    import sys

    print(format_approval_for_cli(request))
    sys.stdout.flush()

    try:
        response = input().strip().lower()

        if response in ("y", "yes", "approve"):
            return ApprovalStatus.APPROVED
        elif response in ("n", "no", "reject"):
            return ApprovalStatus.REJECTED
        elif response in ("c", "cancel"):
            return ApprovalStatus.CANCELLED
        else:
            print("Invalid response. Treating as rejection.")
            return ApprovalStatus.REJECTED

    except (EOFError, KeyboardInterrupt):
        return ApprovalStatus.CANCELLED


# Global approval manager
_approval_manager: Optional[ApprovalManager] = None
_manager_lock = threading.Lock()


def get_approval_manager() -> ApprovalManager:
    """Get or create the global approval manager."""
    global _approval_manager
    if _approval_manager is None:
        with _manager_lock:
            if _approval_manager is None:
                _approval_manager = ApprovalManager()
    return _approval_manager


def reset_approval_manager():
    """Reset the global approval manager."""
    global _approval_manager
    with _manager_lock:
        _approval_manager = None
