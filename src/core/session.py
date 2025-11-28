"""
Session management for research tasks.

Enables saving and resuming long-running research sessions.
Addresses session_resumption feature from the roadmap.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import setup_logger
from .config import get_settings

logger = setup_logger("session")

# Default sessions directory
DEFAULT_SESSIONS_DIR = os.getenv("SESSIONS_DIR", "sessions")


@dataclass
class SessionMetadata:
    """Metadata for a saved session."""

    session_id: str
    company_name: str
    created_at: str
    updated_at: str
    current_phase: str
    checkpoints_count: int
    is_complete: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "company_name": self.company_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_phase": self.current_phase,
            "checkpoints_count": self.checkpoints_count,
            "is_complete": self.is_complete,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMetadata":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            company_name=data["company_name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            current_phase=data["current_phase"],
            checkpoints_count=data.get("checkpoints_count", 0),
            is_complete=data.get("is_complete", False),
            error=data.get("error"),
        )


@dataclass
class SessionCheckpoint:
    """A checkpoint within a session."""

    checkpoint_id: str
    timestamp: str
    phase: str
    state: Dict[str, Any]
    step_number: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp,
            "phase": self.phase,
            "state": self.state,
            "step_number": self.step_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCheckpoint":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            timestamp=data["timestamp"],
            phase=data["phase"],
            state=data["state"],
            step_number=data["step_number"],
        )


@dataclass
class Session:
    """Represents a research session."""

    session_id: str
    company_name: str
    created_at: str
    updated_at: str
    current_phase: str
    checkpoints: List[SessionCheckpoint] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    error: Optional[str] = None

    def get_metadata(self) -> SessionMetadata:
        """Get session metadata."""
        return SessionMetadata(
            session_id=self.session_id,
            company_name=self.company_name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            current_phase=self.current_phase,
            checkpoints_count=len(self.checkpoints),
            is_complete=self.is_complete,
            error=self.error,
        )

    def add_checkpoint(self, state: Dict[str, Any], phase: str) -> SessionCheckpoint:
        """
        Add a new checkpoint.

        Args:
            state: Current state to checkpoint.
            phase: Current phase name.

        Returns:
            The created checkpoint.
        """
        checkpoint = SessionCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            phase=phase,
            state=state,
            step_number=len(self.checkpoints) + 1,
        )
        self.checkpoints.append(checkpoint)
        self.current_phase = phase
        self.updated_at = datetime.now().isoformat()
        return checkpoint

    def get_latest_checkpoint(self) -> Optional[SessionCheckpoint]:
        """Get the most recent checkpoint."""
        if self.checkpoints:
            return self.checkpoints[-1]
        return None

    def get_checkpoint_by_id(self, checkpoint_id: str) -> Optional[SessionCheckpoint]:
        """Get a specific checkpoint by ID."""
        for cp in self.checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "company_name": self.company_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_phase": self.current_phase,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "history": self.history,
            "memory": self.memory,
            "is_complete": self.is_complete,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            company_name=data["company_name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            current_phase=data["current_phase"],
            checkpoints=[
                SessionCheckpoint.from_dict(cp) for cp in data.get("checkpoints", [])
            ],
            history=data.get("history", []),
            memory=data.get("memory", {}),
            is_complete=data.get("is_complete", False),
            error=data.get("error"),
        )


class SessionManager:
    """
    Manages research sessions with persistence.

    Provides:
    - Session creation and loading
    - Automatic checkpointing
    - Session resumption
    """

    def __init__(
        self,
        sessions_dir: Optional[str] = None,
        checkpoint_interval: int = 1,
    ):
        """
        Initialize the session manager.

        Args:
            sessions_dir: Directory to store session files.
            checkpoint_interval: Create checkpoint every N steps (0 = manual only).
        """
        self.sessions_dir = Path(sessions_dir or DEFAULT_SESSIONS_DIR)
        self.checkpoint_interval = checkpoint_interval
        self._current_session: Optional[Session] = None
        self._step_counter: int = 0
        self._lock = threading.Lock()

        # Create sessions directory if it doesn't exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.sessions_dir / f"{session_id}.json"

    def _get_metadata_path(self) -> Path:
        """Get the path to the sessions metadata index."""
        return self.sessions_dir / "index.json"

    def _load_metadata_index(self) -> Dict[str, SessionMetadata]:
        """Load the sessions metadata index."""
        path = self._get_metadata_path()
        if not path.exists():
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                sid: SessionMetadata.from_dict(meta) for sid, meta in data.items()
            }
        except Exception as e:
            logger.warning(f"Failed to load sessions index: {e}")
            return {}

    def _save_metadata_index(self, index: Dict[str, SessionMetadata]) -> None:
        """Save the sessions metadata index."""
        path = self._get_metadata_path()
        data = {sid: meta.to_dict() for sid, meta in index.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def create_session(self, company_name: str) -> Session:
        """
        Create a new research session.

        Args:
            company_name: Name of the company being researched.

        Returns:
            The new session.
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        session = Session(
            session_id=session_id,
            company_name=company_name,
            created_at=now,
            updated_at=now,
            current_phase="init",
        )

        # Save immediately
        self.save_session(session)

        with self._lock:
            self._current_session = session
            self._step_counter = 0

        logger.info(f"Created new session: {session_id} for {company_name}")
        return session

    def save_session(self, session: Session) -> None:
        """
        Save a session to disk.

        Args:
            session: Session to save.
        """
        path = self._get_session_path(session.session_id)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, default=str)

            # Update index
            index = self._load_metadata_index()
            index[session.session_id] = session.get_metadata()
            self._save_metadata_index(index)

            logger.debug(f"Saved session: {session.session_id}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            raise

    def load_session(self, session_id: str) -> Optional[Session]:
        """
        Load a session from disk.

        Args:
            session_id: ID of the session to load.

        Returns:
            The loaded session, or None if not found.
        """
        path = self._get_session_path(session_id)

        if not path.exists():
            logger.warning(f"Session not found: {session_id}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = Session.from_dict(data)

            with self._lock:
                self._current_session = session
                self._step_counter = len(session.checkpoints)

            logger.info(f"Loaded session: {session_id}")
            return session
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def checkpoint(
        self,
        state: Dict[str, Any],
        phase: Optional[str] = None,
        force: bool = False,
    ) -> Optional[SessionCheckpoint]:
        """
        Create a checkpoint of the current state.

        Args:
            state: Current state to checkpoint.
            phase: Current phase (inferred from state if not provided).
            force: Force checkpoint even if interval not reached.

        Returns:
            The checkpoint if created, None otherwise.
        """
        with self._lock:
            if self._current_session is None:
                logger.warning("No active session for checkpointing")
                return None

            self._step_counter += 1

            # Check if we should checkpoint
            if not force and self.checkpoint_interval > 0:
                if self._step_counter % self.checkpoint_interval != 0:
                    return None

            # Determine phase
            if phase is None:
                phase = state.get("current_wave", "unknown")

            # Create checkpoint
            checkpoint = self._current_session.add_checkpoint(state, phase)

            # Save session
            self.save_session(self._current_session)

            logger.info(
                f"Created checkpoint {checkpoint.step_number} for session "
                f"{self._current_session.session_id}"
            )
            return checkpoint

    def get_current_session(self) -> Optional[Session]:
        """Get the current active session."""
        with self._lock:
            return self._current_session

    def resume(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume a session from its latest checkpoint.

        Args:
            session_id: ID of the session to resume.

        Returns:
            The state from the latest checkpoint, or None if not found.
        """
        session = self.load_session(session_id)
        if session is None:
            return None

        checkpoint = session.get_latest_checkpoint()
        if checkpoint is None:
            logger.warning(f"Session {session_id} has no checkpoints")
            # Return initial state
            return {
                "company_name": session.company_name,
                "current_wave": session.current_phase,
            }

        logger.info(
            f"Resuming session {session_id} from checkpoint "
            f"{checkpoint.step_number} (phase: {checkpoint.phase})"
        )
        return checkpoint.state

    def list_sessions(
        self,
        include_complete: bool = True,
        company_filter: Optional[str] = None,
    ) -> List[SessionMetadata]:
        """
        List all available sessions.

        Args:
            include_complete: Include completed sessions.
            company_filter: Filter by company name (case-insensitive).

        Returns:
            List of session metadata.
        """
        index = self._load_metadata_index()
        sessions = list(index.values())

        if not include_complete:
            sessions = [s for s in sessions if not s.is_complete]

        if company_filter:
            filter_lower = company_filter.lower()
            sessions = [
                s for s in sessions if filter_lower in s.company_name.lower()
            ]

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: ID of the session to delete.

        Returns:
            True if deleted, False if not found.
        """
        path = self._get_session_path(session_id)

        if not path.exists():
            return False

        try:
            path.unlink()

            # Update index
            index = self._load_metadata_index()
            if session_id in index:
                del index[session_id]
                self._save_metadata_index(index)

            with self._lock:
                if self._current_session and self._current_session.session_id == session_id:
                    self._current_session = None

            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def mark_complete(self, session_id: Optional[str] = None) -> None:
        """
        Mark a session as complete.

        Args:
            session_id: ID of session to mark (uses current if None).
        """
        with self._lock:
            if session_id:
                session = self.load_session(session_id)
            else:
                session = self._current_session

            if session:
                session.is_complete = True
                session.current_phase = "complete"
                session.updated_at = datetime.now().isoformat()
                self.save_session(session)
                logger.info(f"Marked session {session.session_id} as complete")

    def mark_error(self, error: str, session_id: Optional[str] = None) -> None:
        """
        Mark a session as failed with an error.

        Args:
            error: Error message.
            session_id: ID of session to mark (uses current if None).
        """
        with self._lock:
            if session_id:
                session = self.load_session(session_id)
            else:
                session = self._current_session

            if session:
                session.error = error
                session.current_phase = "error"
                session.updated_at = datetime.now().isoformat()
                self.save_session(session)
                logger.info(f"Marked session {session.session_id} as error: {error}")


# Global session manager singleton
_session_manager: Optional[SessionManager] = None
_session_manager_lock = threading.Lock()


def get_session_manager(
    sessions_dir: Optional[str] = None,
    checkpoint_interval: int = 1,
) -> SessionManager:
    """
    Get or create the global session manager.

    Args:
        sessions_dir: Optional sessions directory.
        checkpoint_interval: Checkpoint interval (only used on first call).

    Returns:
        The global SessionManager instance.
    """
    global _session_manager
    if _session_manager is None:
        with _session_manager_lock:
            if _session_manager is None:
                _session_manager = SessionManager(sessions_dir, checkpoint_interval)
    return _session_manager


def reset_session_manager() -> None:
    """Reset the global session manager."""
    global _session_manager
    with _session_manager_lock:
        _session_manager = None
