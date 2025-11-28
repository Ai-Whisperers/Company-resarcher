"""Tests for the human-in-the-loop approval system."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.core.human_loop import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalType,
    format_approval_for_cli,
    get_approval_manager,
    require_approval,
    reset_approval_manager,
)


class TestApprovalRequest:
    """Tests for ApprovalRequest class."""

    def test_create_request(self):
        """Test creating an approval request."""
        request = ApprovalRequest(
            request_id="test-123",
            action_type=ApprovalType.CRITICAL_ACTION,
            description="Delete all data",
        )
        assert request.request_id == "test-123"
        assert request.action_type == ApprovalType.CRITICAL_ACTION
        assert request.status == ApprovalStatus.PENDING
        assert request.created_at is not None

    def test_request_with_context(self):
        """Test request with context."""
        request = ApprovalRequest(
            request_id="test-456",
            action_type=ApprovalType.DATA_MODIFICATION,
            description="Update records",
            context={"table": "users", "count": 100},
        )
        assert request.context["table"] == "users"
        assert request.context["count"] == 100

    def test_to_dict(self):
        """Test serialization to dict."""
        request = ApprovalRequest(
            request_id="test-789",
            action_type=ApprovalType.EXTERNAL_REQUEST,
            description="Call external API",
            status=ApprovalStatus.APPROVED,
            resolver="admin",
        )
        data = request.to_dict()
        assert data["request_id"] == "test-789"
        assert data["action_type"] == "external_request"
        assert data["status"] == "approved"
        assert data["resolver"] == "admin"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "request_id": "test-abc",
            "action_type": "report_publish",
            "description": "Publish report",
            "status": "rejected",
            "created_at": "2024-01-01T12:00:00",
            "rejection_reason": "Not ready",
        }
        request = ApprovalRequest.from_dict(data)
        assert request.request_id == "test-abc"
        assert request.action_type == ApprovalType.REPORT_PUBLISH
        assert request.status == ApprovalStatus.REJECTED
        assert request.rejection_reason == "Not ready"


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_all_statuses_exist(self):
        """Test all expected statuses are defined."""
        expected = ["pending", "approved", "rejected", "timeout", "cancelled"]
        actual = [s.value for s in ApprovalStatus]
        assert set(actual) == set(expected)


class TestApprovalType:
    """Tests for ApprovalType enum."""

    def test_all_types_exist(self):
        """Test all expected types are defined."""
        expected = [
            "critical_action",
            "data_modification",
            "external_request",
            "report_publish",
            "cost_threshold",
            "custom",
        ]
        actual = [t.value for t in ApprovalType]
        assert set(actual) == set(expected)


class TestApprovalManager:
    """Tests for ApprovalManager class."""

    def setup_method(self):
        """Reset manager before each test."""
        reset_approval_manager()

    @pytest.mark.asyncio
    async def test_request_approval_with_callback(self):
        """Test requesting approval with callback."""
        manager = ApprovalManager()

        async def auto_approve(request):
            return ApprovalStatus.APPROVED

        manager.set_approval_callback(auto_approve)

        request = await manager.request_approval(
            ApprovalType.CRITICAL_ACTION,
            "Test action",
        )

        assert request.status == ApprovalStatus.APPROVED
        assert request.resolved_at is not None

    @pytest.mark.asyncio
    async def test_request_approval_rejection(self):
        """Test rejection via callback."""
        manager = ApprovalManager()

        async def auto_reject(request):
            return ApprovalStatus.REJECTED

        manager.set_approval_callback(auto_reject)

        request = await manager.request_approval(
            ApprovalType.DATA_MODIFICATION,
            "Dangerous operation",
        )

        assert request.status == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_request_approval_timeout(self):
        """Test timeout handling."""
        manager = ApprovalManager(default_timeout=1)

        async def slow_callback(request):
            await asyncio.sleep(5)
            return ApprovalStatus.APPROVED

        manager.set_approval_callback(slow_callback)

        request = await manager.request_approval(
            ApprovalType.EXTERNAL_REQUEST,
            "Slow operation",
            timeout=1,
        )

        assert request.status == ApprovalStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_approve_manually(self):
        """Test manual approval."""
        manager = ApprovalManager()

        # Start approval request in background
        async def request_task():
            return await manager.request_approval(
                ApprovalType.REPORT_PUBLISH,
                "Publish report",
                timeout=10,
            )

        task = asyncio.create_task(request_task())

        # Wait a bit for request to be created
        await asyncio.sleep(0.1)

        # Get pending and approve
        pending = manager.get_pending_requests()
        assert len(pending) == 1

        success = manager.approve(pending[0].request_id, resolver="tester")
        assert success is True

        # Wait for task to complete
        request = await task
        assert request.status == ApprovalStatus.APPROVED
        assert request.resolver == "tester"

    @pytest.mark.asyncio
    async def test_reject_manually(self):
        """Test manual rejection."""
        manager = ApprovalManager()

        async def request_task():
            return await manager.request_approval(
                ApprovalType.COST_THRESHOLD,
                "Budget exceeded",
                timeout=10,
            )

        task = asyncio.create_task(request_task())
        await asyncio.sleep(0.1)

        pending = manager.get_pending_requests()
        success = manager.reject(
            pending[0].request_id,
            reason="Budget not approved",
            resolver="finance",
        )
        assert success is True

        request = await task
        assert request.status == ApprovalStatus.REJECTED
        assert request.rejection_reason == "Budget not approved"

    @pytest.mark.asyncio
    async def test_cancel_request(self):
        """Test cancellation."""
        manager = ApprovalManager()

        async def request_task():
            return await manager.request_approval(
                ApprovalType.CUSTOM,
                "Custom action",
                timeout=10,
            )

        task = asyncio.create_task(request_task())
        await asyncio.sleep(0.1)

        pending = manager.get_pending_requests()
        success = manager.cancel(pending[0].request_id)
        assert success is True

        request = await task
        assert request.status == ApprovalStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_auto_approve_headless(self):
        """Test auto-approval in headless mode."""
        manager = ApprovalManager(auto_approve_in_headless=True)

        with patch("src.core.human_loop.get_settings") as mock_settings:
            mock_settings.return_value.is_headless = True

            request = await manager.request_approval(
                ApprovalType.CRITICAL_ACTION,
                "Auto-approved action",
            )

        assert request.status == ApprovalStatus.APPROVED
        assert request.resolver == "auto_headless"

    @pytest.mark.asyncio
    async def test_notification_callbacks(self):
        """Test notification callbacks are called."""
        manager = ApprovalManager()
        notifications = []

        async def on_notify(request):
            notifications.append(request)

        manager.add_notification_callback(on_notify)

        async def auto_approve(request):
            return ApprovalStatus.APPROVED

        manager.set_approval_callback(auto_approve)

        await manager.request_approval(
            ApprovalType.EXTERNAL_REQUEST,
            "Test notification",
        )

        assert len(notifications) == 1
        assert notifications[0].description == "Test notification"

    def test_get_history(self):
        """Test getting approval history."""
        manager = ApprovalManager()

        # Add some history entries directly
        for i in range(5):
            request = ApprovalRequest(
                request_id=f"test-{i}",
                action_type=ApprovalType.CUSTOM,
                description=f"Action {i}",
                status=ApprovalStatus.APPROVED if i % 2 == 0 else ApprovalStatus.REJECTED,
            )
            manager._add_to_history(request)

        history = manager.get_history()
        assert len(history) == 5

        approved_only = manager.get_history(status_filter=ApprovalStatus.APPROVED)
        assert len(approved_only) == 3

    def test_approve_nonexistent_request(self):
        """Test approving nonexistent request returns False."""
        manager = ApprovalManager()
        assert manager.approve("nonexistent") is False

    def test_reject_nonexistent_request(self):
        """Test rejecting nonexistent request returns False."""
        manager = ApprovalManager()
        assert manager.reject("nonexistent") is False


class TestRequireApproval:
    """Tests for require_approval convenience function."""

    def setup_method(self):
        """Reset before each test."""
        reset_approval_manager()

    @pytest.mark.asyncio
    async def test_require_approval_approved(self):
        """Test require_approval returns True when approved."""
        manager = ApprovalManager()

        async def auto_approve(request):
            return ApprovalStatus.APPROVED

        manager.set_approval_callback(auto_approve)

        result = await require_approval(
            "Test action",
            manager=manager,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_require_approval_rejected(self):
        """Test require_approval returns False when rejected."""
        manager = ApprovalManager()

        async def auto_reject(request):
            return ApprovalStatus.REJECTED

        manager.set_approval_callback(auto_reject)

        result = await require_approval(
            "Test action",
            manager=manager,
        )

        assert result is False


class TestCLIFormatting:
    """Tests for CLI formatting functions."""

    def test_format_basic_request(self):
        """Test formatting basic request."""
        request = ApprovalRequest(
            request_id="test-format-123",
            action_type=ApprovalType.CRITICAL_ACTION,
            description="Delete all data",
        )
        formatted = format_approval_for_cli(request)
        assert "APPROVAL REQUIRED" in formatted
        assert "Delete all data" in formatted
        assert "critical_action" in formatted

    def test_format_request_with_context(self):
        """Test formatting request with context."""
        request = ApprovalRequest(
            request_id="test-ctx-456",
            action_type=ApprovalType.DATA_MODIFICATION,
            description="Update records",
            context={"table": "users", "affected_rows": 1000},
        )
        formatted = format_approval_for_cli(request)
        assert "Context:" in formatted
        assert "users" in formatted
        assert "1000" in formatted

    def test_format_request_with_timeout(self):
        """Test formatting request with timeout."""
        request = ApprovalRequest(
            request_id="test-timeout-789",
            action_type=ApprovalType.EXTERNAL_REQUEST,
            description="API call",
            timeout_seconds=60,
        )
        formatted = format_approval_for_cli(request)
        assert "Timeout: 60 seconds" in formatted


class TestGlobalManager:
    """Tests for global manager functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_approval_manager()

    def test_get_approval_manager_singleton(self):
        """Test singleton behavior."""
        mgr1 = get_approval_manager()
        mgr2 = get_approval_manager()
        assert mgr1 is mgr2

    def test_reset_approval_manager(self):
        """Test resetting the singleton."""
        mgr1 = get_approval_manager()
        reset_approval_manager()
        mgr2 = get_approval_manager()
        assert mgr1 is not mgr2
