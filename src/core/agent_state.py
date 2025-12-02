"""
Agent State Management - DEBT-004

Formal state management for agents with:
- Explicit state tracking
- Pause/resume capability
- State persistence
- Transition logging
"""

import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from uuid import uuid4

from pydantic import BaseModel, Field

from .logger import setup_logger

logger = setup_logger("agent_state")


# =============================================================================
# State Types
# =============================================================================


class AgentStatus(str, Enum):
    """Status of an agent."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Role of a message in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """A message in the agent's conversation history."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None


class StateTransition(BaseModel):
    """Record of a state transition."""

    from_status: AgentStatus
    to_status: AgentStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    reason: Optional[str] = None
    step_number: int = 0


# =============================================================================
# Agent State
# =============================================================================


class AgentState(BaseModel):
    """
    Complete state of an agent execution.

    Tracks:
    - Execution status and progress
    - Conversation history
    - Variables and context
    - State transitions
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str = Field(default="unnamed")
    created_at: datetime = Field(default_factory=datetime.now)

    # Status
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    current_step: int = Field(default=0)
    max_steps: int = Field(default=100)

    # Conversation
    messages: List[Message] = Field(default_factory=list)
    system_prompt: Optional[str] = None

    # Variables and context
    variables: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    # Progress tracking
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_task: Optional[str] = None

    # Results
    result: Optional[Any] = None
    error: Optional[str] = None

    # History
    transitions: List[StateTransition] = Field(default_factory=list)

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.now)

    # ==========================================================================
    # Status Management
    # ==========================================================================

    def transition_to(self, new_status: AgentStatus, reason: Optional[str] = None) -> None:
        """Transition to a new status with logging."""
        old_status = self.status

        transition = StateTransition(
            from_status=old_status,
            to_status=new_status,
            reason=reason,
            step_number=self.current_step,
        )
        self.transitions.append(transition)

        self.status = new_status
        self.last_updated = datetime.now()

        if new_status == AgentStatus.RUNNING and not self.started_at:
            self.started_at = datetime.now()
        elif new_status in (AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.CANCELLED):
            self.completed_at = datetime.now()

        logger.info(f"Agent {self.id} transitioned: {old_status.value} -> {new_status.value}")

    def start(self, task: Optional[str] = None) -> None:
        """Start the agent execution."""
        self.transition_to(AgentStatus.RUNNING, reason="Started")
        if task:
            self.current_task = task

    def pause(self, reason: Optional[str] = None) -> None:
        """Pause the agent execution."""
        if self.status == AgentStatus.RUNNING:
            self.transition_to(AgentStatus.PAUSED, reason=reason or "Paused by request")

    def resume(self) -> None:
        """Resume a paused agent."""
        if self.status == AgentStatus.PAUSED:
            self.transition_to(AgentStatus.RUNNING, reason="Resumed")

    def complete(self, result: Any = None) -> None:
        """Mark the agent as completed."""
        self.result = result
        self.progress_percent = 100.0
        self.transition_to(AgentStatus.COMPLETED, reason="Completed successfully")

    def fail(self, error: str) -> None:
        """Mark the agent as failed."""
        self.error = error
        self.transition_to(AgentStatus.FAILED, reason=f"Failed: {error}")

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the agent execution."""
        self.transition_to(AgentStatus.CANCELLED, reason=reason or "Cancelled by request")

    # ==========================================================================
    # Message Management
    # ==========================================================================

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> Message:
        """Add a message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            tool_call_id=tool_call_id,
            tool_name=tool_name,
        )
        self.messages.append(message)
        self.last_updated = datetime.now()
        return message

    def add_system_message(self, content: str) -> Message:
        """Add a system message."""
        return self.add_message(MessageRole.SYSTEM, content)

    def add_user_message(self, content: str) -> Message:
        """Add a user message."""
        return self.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str) -> Message:
        """Add an assistant message."""
        return self.add_message(MessageRole.ASSISTANT, content)

    def add_tool_message(
        self,
        content: str,
        tool_call_id: str,
        tool_name: str,
    ) -> Message:
        """Add a tool result message."""
        return self.add_message(
            MessageRole.TOOL,
            content,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
        )

    def get_conversation_for_llm(self) -> List[Dict[str, str]]:
        """Get conversation in format suitable for LLM APIs."""
        messages = []
        for msg in self.messages:
            message_dict = {"role": msg.role.value, "content": msg.content}
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            if msg.tool_name:
                message_dict["name"] = msg.tool_name
            messages.append(message_dict)
        return messages

    # ==========================================================================
    # Variable Management
    # ==========================================================================

    def set_variable(self, key: str, value: Any) -> None:
        """Set a variable in the state."""
        self.variables[key] = value
        self.last_updated = datetime.now()

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a variable from the state."""
        return self.variables.get(key, default)

    def update_variables(self, updates: Dict[str, Any]) -> None:
        """Update multiple variables at once."""
        self.variables.update(updates)
        self.last_updated = datetime.now()

    # ==========================================================================
    # Progress Tracking
    # ==========================================================================

    def advance_step(self, task: Optional[str] = None) -> None:
        """Advance to the next step."""
        self.current_step += 1
        if task:
            self.current_task = task
        self.progress_percent = min(100.0, (self.current_step / self.max_steps) * 100)
        self.last_updated = datetime.now()

    def set_progress(self, percent: float, task: Optional[str] = None) -> None:
        """Set progress percentage directly."""
        self.progress_percent = max(0.0, min(100.0, percent))
        if task:
            self.current_task = task
        self.last_updated = datetime.now()

    # ==========================================================================
    # Persistence
    # ==========================================================================

    def to_json(self, indent: int = 2) -> str:
        """Serialize state to JSON."""
        return self.model_dump_json(indent=indent)

    def save(self, path: str) -> None:
        """Save state to a JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_json())
        logger.debug(f"Saved agent state to {path}")

    @classmethod
    def load(cls, path: str) -> "AgentState":
        """Load state from a JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"State file not found: {path}")
        data = json.loads(file_path.read_text())
        return cls(**data)

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def get_duration_seconds(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent state."""
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "progress": f"{self.progress_percent:.1f}%",
            "current_task": self.current_task,
            "step": f"{self.current_step}/{self.max_steps}",
            "messages_count": len(self.messages),
            "duration_seconds": self.get_duration_seconds(),
            "error": self.error,
        }


# =============================================================================
# State Manager
# =============================================================================


class StateManager:
    """
    Manages multiple agent states with persistence.

    Features:
    - Store and retrieve agent states
    - Automatic persistence
    - State cleanup
    """

    def __init__(self, storage_path: str = "data/agent_states"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._states: Dict[str, AgentState] = {}
        self._lock = asyncio.Lock()

    async def create_state(self, agent_name: str, **kwargs) -> AgentState:
        """Create a new agent state."""
        async with self._lock:
            state = AgentState(agent_name=agent_name, **kwargs)
            self._states[state.id] = state
            return state

    async def get_state(self, state_id: str) -> Optional[AgentState]:
        """Get an agent state by ID."""
        # Try in-memory first
        if state_id in self._states:
            return self._states[state_id]

        # Try loading from disk
        state_file = self.storage_path / f"{state_id}.json"
        if state_file.exists():
            state = AgentState.load(str(state_file))
            self._states[state_id] = state
            return state

        return None

    async def save_state(self, state: AgentState) -> None:
        """Save an agent state to disk."""
        async with self._lock:
            self._states[state.id] = state
            state_file = self.storage_path / f"{state.id}.json"
            state.save(str(state_file))

    async def delete_state(self, state_id: str) -> bool:
        """Delete an agent state."""
        async with self._lock:
            if state_id in self._states:
                del self._states[state_id]

            state_file = self.storage_path / f"{state_id}.json"
            if state_file.exists():
                state_file.unlink()
                return True
            return False

    async def list_states(
        self,
        status: Optional[AgentStatus] = None,
        agent_name: Optional[str] = None,
    ) -> List[AgentState]:
        """List agent states with optional filtering."""
        states = list(self._states.values())

        # Also load from disk
        for state_file in self.storage_path.glob("*.json"):
            state_id = state_file.stem
            if state_id not in self._states:
                try:
                    state = AgentState.load(str(state_file))
                    self._states[state_id] = state
                    states.append(state)
                except Exception as e:
                    logger.warning(f"Failed to load state file {state_file}: {e}")

        # Apply filters
        if status:
            states = [s for s in states if s.status == status]
        if agent_name:
            states = [s for s in states if s.agent_name == agent_name]

        return states

    async def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed states."""
        cutoff = datetime.now()
        deleted = 0

        async with self._lock:
            for state_id, state in list(self._states.items()):
                if state.status in (AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.CANCELLED):
                    if state.completed_at:
                        age_hours = (cutoff - state.completed_at).total_seconds() / 3600
                        if age_hours > max_age_hours:
                            del self._states[state_id]
                            state_file = self.storage_path / f"{state_id}.json"
                            if state_file.exists():
                                state_file.unlink()
                            deleted += 1

        logger.info(f"Cleaned up {deleted} old agent states")
        return deleted


# =============================================================================
# Global State Manager
# =============================================================================


_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
