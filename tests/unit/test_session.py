"""Tests for the session management system."""

import pytest
import tempfile
from pathlib import Path

from src.core.session.session import (
    Session,
    SessionManager,
    SessionCheckpoint,
    SessionMetadata,
    get_session_manager,
    reset_session_manager,
)


class TestSession:
    """Tests for Session class."""

    def test_create_session(self):
        """Test creating a session."""
        session = Session(
            session_id="test-123",
            company_name="Test Corp",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            current_phase="init",
        )
        assert session.session_id == "test-123"
        assert session.company_name == "Test Corp"
        assert session.current_phase == "init"
        assert not session.is_complete

    def test_add_checkpoint(self):
        """Test adding checkpoints."""
        session = Session(
            session_id="test-123",
            company_name="Test Corp",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            current_phase="init",
        )

        state = {"company_name": "Test Corp", "current_wave": "gathering"}
        checkpoint = session.add_checkpoint(state, "gathering")

        assert checkpoint.phase == "gathering"
        assert checkpoint.step_number == 1
        assert session.current_phase == "gathering"
        assert len(session.checkpoints) == 1

    def test_get_latest_checkpoint(self):
        """Test getting latest checkpoint."""
        session = Session(
            session_id="test-123",
            company_name="Test Corp",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            current_phase="init",
        )

        assert session.get_latest_checkpoint() is None

        session.add_checkpoint({"phase": "1"}, "phase1")
        session.add_checkpoint({"phase": "2"}, "phase2")

        latest = session.get_latest_checkpoint()
        assert latest is not None
        assert latest.phase == "phase2"
        assert latest.step_number == 2

    def test_serialization(self):
        """Test session serialization."""
        session = Session(
            session_id="test-123",
            company_name="Test Corp",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            current_phase="init",
        )
        session.add_checkpoint({"test": "data"}, "phase1")

        data = session.to_dict()
        restored = Session.from_dict(data)

        assert restored.session_id == session.session_id
        assert restored.company_name == session.company_name
        assert len(restored.checkpoints) == 1

    def test_get_metadata(self):
        """Test getting session metadata."""
        session = Session(
            session_id="test-123",
            company_name="Test Corp",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            current_phase="gathering",
        )
        session.add_checkpoint({}, "gathering")

        metadata = session.get_metadata()
        assert metadata.session_id == "test-123"
        assert metadata.company_name == "Test Corp"
        assert metadata.checkpoints_count == 1


class TestSessionManager:
    """Tests for SessionManager class."""

    def setup_method(self):
        """Reset session manager before each test."""
        reset_session_manager()

    def test_create_session(self):
        """Test creating a new session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            session = manager.create_session("Test Company")

            assert session.company_name == "Test Company"
            assert session.current_phase == "init"
            assert Path(tmpdir, f"{session.session_id}.json").exists()

    def test_save_and_load_session(self):
        """Test saving and loading a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            session = manager.create_session("Test Company")
            session.add_checkpoint({"test": "data"}, "phase1")
            manager.save_session(session)

            # Load in new manager instance
            manager2 = SessionManager(sessions_dir=tmpdir)
            loaded = manager2.load_session(session.session_id)

            assert loaded is not None
            assert loaded.session_id == session.session_id
            assert len(loaded.checkpoints) == 1

    def test_checkpoint(self):
        """Test creating checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir, checkpoint_interval=1)
            manager.create_session("Test Company")

            cp = manager.checkpoint({"state": "value"}, "gathering")
            assert cp is not None
            assert cp.phase == "gathering"

    def test_checkpoint_interval(self):
        """Test checkpoint interval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir, checkpoint_interval=3)
            manager.create_session("Test Company")

            # First two should not create checkpoints
            assert manager.checkpoint({"step": 1}) is None
            assert manager.checkpoint({"step": 2}) is None

            # Third should create checkpoint
            cp = manager.checkpoint({"step": 3})
            assert cp is not None

    def test_resume(self):
        """Test resuming a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            session = manager.create_session("Test Company")

            # Add some progress
            manager.checkpoint({"company_name": "Test", "current_wave": "gathering"}, force=True)
            manager.checkpoint({"company_name": "Test", "current_wave": "thinking"}, force=True)

            # Resume
            state = manager.resume(session.session_id)
            assert state is not None
            assert state["current_wave"] == "thinking"

    def test_list_sessions(self):
        """Test listing sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            manager.create_session("Company A")
            manager.create_session("Company B")
            manager.create_session("Another Company")

            sessions = manager.list_sessions()
            assert len(sessions) == 3

            # Filter by company
            filtered = manager.list_sessions(company_filter="Company")
            assert len(filtered) == 3  # All match

            filtered = manager.list_sessions(company_filter="another")
            assert len(filtered) == 1

    def test_delete_session(self):
        """Test deleting a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            session = manager.create_session("Test Company")
            session_id = session.session_id

            assert manager.delete_session(session_id) is True
            assert not Path(tmpdir, f"{session_id}.json").exists()

            # Should return False for nonexistent
            assert manager.delete_session("nonexistent") is False

    def test_mark_complete(self):
        """Test marking session as complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            session = manager.create_session("Test Company")

            manager.mark_complete()

            # Reload and verify
            loaded = manager.load_session(session.session_id)
            assert loaded is not None
            assert loaded.is_complete is True
            assert loaded.current_phase == "complete"

    def test_mark_error(self):
        """Test marking session as error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(sessions_dir=tmpdir)
            session = manager.create_session("Test Company")

            manager.mark_error("Something went wrong")

            loaded = manager.load_session(session.session_id)
            assert loaded is not None
            assert loaded.error == "Something went wrong"
            assert loaded.current_phase == "error"


class TestGlobalSessionManager:
    """Tests for global session manager functions."""

    def setup_method(self):
        """Reset session manager before each test."""
        reset_session_manager()

    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = get_session_manager(sessions_dir=tmpdir)
            manager2 = get_session_manager()
            assert manager1 is manager2

    def test_reset_session_manager(self):
        """Test resetting the singleton."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = get_session_manager(sessions_dir=tmpdir)
            reset_session_manager()
            manager2 = get_session_manager(sessions_dir=tmpdir)
            assert manager1 is not manager2
