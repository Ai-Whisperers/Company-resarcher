"""
Interactive Research Mode - User prompting and confirmation during research.

This module provides interactive capabilities for the research pipeline:
- User confirmation for expensive operations
- Research direction adjustments mid-flow
- Progress callbacks for UI integration
- Interactive prompts for ambiguous situations

Usage:
    from src.core.interactive import InteractiveSession, ProgressCallback

    # Create interactive session
    session = InteractiveSession(enabled=True)

    # Get user confirmation
    if await session.confirm("Proceed with deep research?"):
        # Continue with operation
        pass

    # Progress callback
    callback = ProgressCallback()
    callback.on_stage_start("market", "Researching market intelligence...")
"""

import asyncio
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from ..core.logger import setup_logger

logger = setup_logger("interactive")


class ProgressStage(str, Enum):
    """Research progress stages."""
    INITIALIZING = "initializing"
    SEARCH = "search"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    GENERATE = "generate"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ProgressEvent:
    """Progress event with stage information."""
    stage: str
    progress: int  # 0-100
    message: str
    phase: Optional[str] = None  # e.g., "market", "financial"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "phase": self.phase,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ProgressCallback(ABC):
    """Abstract base class for progress callbacks."""

    @abstractmethod
    async def on_progress(self, event: ProgressEvent) -> None:
        """Called when progress is made."""
        pass

    @abstractmethod
    async def on_stage_start(self, stage: str, message: str) -> None:
        """Called when a new stage starts."""
        pass

    @abstractmethod
    async def on_stage_complete(self, stage: str, message: str) -> None:
        """Called when a stage completes."""
        pass

    @abstractmethod
    async def on_error(self, error: str, stage: Optional[str] = None) -> None:
        """Called when an error occurs."""
        pass


class ConsoleProgressCallback(ProgressCallback):
    """Progress callback that prints to console."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._current_stage: Optional[str] = None

    async def on_progress(self, event: ProgressEvent) -> None:
        """Print progress to console."""
        if self.verbose:
            bar_length = 30
            filled = int(bar_length * event.progress / 100)
            bar = "=" * filled + "-" * (bar_length - filled)
            phase_str = f"[{event.phase}] " if event.phase else ""
            print(f"\r{phase_str}[{bar}] {event.progress}% - {event.message}", end="", flush=True)
            if event.progress >= 100:
                print()  # New line when complete

    async def on_stage_start(self, stage: str, message: str) -> None:
        """Print stage start to console."""
        self._current_stage = stage
        if self.verbose:
            print(f"\n>>> Starting: {message}")

    async def on_stage_complete(self, stage: str, message: str) -> None:
        """Print stage completion to console."""
        if self.verbose:
            print(f"<<< Completed: {message}")

    async def on_error(self, error: str, stage: Optional[str] = None) -> None:
        """Print error to console."""
        stage_str = f"[{stage}] " if stage else ""
        print(f"\n!!! Error {stage_str}: {error}", file=sys.stderr)


class WebSocketProgressCallback(ProgressCallback):
    """Progress callback that sends events via WebSocket."""

    def __init__(self, send_func: Callable[[Dict[str, Any]], Any]):
        """
        Initialize WebSocket progress callback.

        Args:
            send_func: Async function to send JSON message via WebSocket
        """
        self.send_func = send_func

    async def on_progress(self, event: ProgressEvent) -> None:
        """Send progress event via WebSocket."""
        await self.send_func({
            "type": "progress",
            "data": {
                "stage": event.stage,
                "progress": event.progress,
                "message": event.message,
                "phase": event.phase,
                "timestamp": event.timestamp.isoformat(),
            }
        })

    async def on_stage_start(self, stage: str, message: str) -> None:
        """Send stage start event via WebSocket."""
        await self.send_func({
            "type": "stage_start",
            "data": {
                "stage": stage,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        })

    async def on_stage_complete(self, stage: str, message: str) -> None:
        """Send stage complete event via WebSocket."""
        await self.send_func({
            "type": "stage_complete",
            "data": {
                "stage": stage,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        })

    async def on_error(self, error: str, stage: Optional[str] = None) -> None:
        """Send error event via WebSocket."""
        await self.send_func({
            "type": "error",
            "data": {
                "error": error,
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
            }
        })


class MultiProgressCallback(ProgressCallback):
    """Combines multiple progress callbacks."""

    def __init__(self, callbacks: List[ProgressCallback]):
        self.callbacks = callbacks

    async def on_progress(self, event: ProgressEvent) -> None:
        await asyncio.gather(*[cb.on_progress(event) for cb in self.callbacks])

    async def on_stage_start(self, stage: str, message: str) -> None:
        await asyncio.gather(*[cb.on_stage_start(stage, message) for cb in self.callbacks])

    async def on_stage_complete(self, stage: str, message: str) -> None:
        await asyncio.gather(*[cb.on_stage_complete(stage, message) for cb in self.callbacks])

    async def on_error(self, error: str, stage: Optional[str] = None) -> None:
        await asyncio.gather(*[cb.on_error(error, stage) for cb in self.callbacks])


class InteractiveSession:
    """
    Interactive session for user prompting during research.

    Provides methods for:
    - Confirming expensive operations
    - Adjusting research direction
    - Handling ambiguous situations
    """

    def __init__(
        self,
        enabled: bool = True,
        timeout: float = 30.0,
        default_confirm: bool = True,
        input_func: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize interactive session.

        Args:
            enabled: Whether interactive mode is enabled
            timeout: Timeout for user input in seconds
            default_confirm: Default value if timeout/disabled
            input_func: Custom input function (for testing)
        """
        self.enabled = enabled
        self.timeout = timeout
        self.default_confirm = default_confirm
        self._input_func = input_func or input
        self._history: List[Dict[str, Any]] = []

    @property
    def is_interactive(self) -> bool:
        """Check if session is in interactive mode."""
        return self.enabled and sys.stdin.isatty()

    async def confirm(
        self,
        message: str,
        default: Optional[bool] = None,
        details: Optional[str] = None,
    ) -> bool:
        """
        Ask user for confirmation.

        Args:
            message: Confirmation message
            default: Default value (uses instance default if None)
            details: Additional details to show

        Returns:
            True if confirmed, False otherwise
        """
        if default is None:
            default = self.default_confirm

        if not self.is_interactive:
            logger.debug(f"Non-interactive mode, using default: {default}")
            self._record("confirm", message, default)
            return default

        try:
            if details:
                print(f"\n{details}")

            default_str = "Y/n" if default else "y/N"
            prompt = f"\n{message} [{default_str}]: "

            # Use asyncio for timeout
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self._input_func, prompt),
                timeout=self.timeout
            )

            response = response.strip().lower()

            if not response:
                result = default
            elif response in ("y", "yes", "1", "true"):
                result = True
            elif response in ("n", "no", "0", "false"):
                result = False
            else:
                print(f"Invalid response '{response}', using default: {default}")
                result = default

            self._record("confirm", message, result)
            return result

        except asyncio.TimeoutError:
            print(f"\nTimeout after {self.timeout}s, using default: {default}")
            self._record("confirm", message, default, timeout=True)
            return default
        except EOFError:
            logger.debug("EOF received, using default")
            self._record("confirm", message, default, eof=True)
            return default

    async def choose(
        self,
        message: str,
        options: List[str],
        default: int = 0,
    ) -> int:
        """
        Ask user to choose from options.

        Args:
            message: Choice message
            options: List of options
            default: Default option index

        Returns:
            Index of chosen option
        """
        if not self.is_interactive:
            self._record("choose", message, default)
            return default

        try:
            print(f"\n{message}")
            for i, option in enumerate(options):
                marker = "*" if i == default else " "
                print(f"  {marker} [{i + 1}] {option}")

            prompt = f"Enter choice [1-{len(options)}] (default: {default + 1}): "

            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self._input_func, prompt),
                timeout=self.timeout
            )

            response = response.strip()

            if not response:
                result = default
            else:
                try:
                    idx = int(response) - 1
                    if 0 <= idx < len(options):
                        result = idx
                    else:
                        print(f"Invalid choice, using default: {options[default]}")
                        result = default
                except ValueError:
                    print(f"Invalid input, using default: {options[default]}")
                    result = default

            self._record("choose", message, result, options=options)
            return result

        except asyncio.TimeoutError:
            print(f"\nTimeout, using default: {options[default]}")
            self._record("choose", message, default, options=options, timeout=True)
            return default

    async def get_input(
        self,
        message: str,
        default: str = "",
        validator: Optional[Callable[[str], bool]] = None,
    ) -> str:
        """
        Get text input from user.

        Args:
            message: Input prompt message
            default: Default value
            validator: Optional validation function

        Returns:
            User input or default
        """
        if not self.is_interactive:
            self._record("input", message, default)
            return default

        try:
            default_str = f" [{default}]" if default else ""
            prompt = f"\n{message}{default_str}: "

            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self._input_func, prompt),
                timeout=self.timeout
            )

            response = response.strip()

            if not response:
                result = default
            elif validator and not validator(response):
                print(f"Invalid input, using default: {default}")
                result = default
            else:
                result = response

            self._record("input", message, result)
            return result

        except asyncio.TimeoutError:
            print(f"\nTimeout, using default: {default}")
            self._record("input", message, default, timeout=True)
            return default

    async def confirm_expensive_operation(
        self,
        operation: str,
        estimated_cost: Optional[str] = None,
        estimated_time: Optional[str] = None,
    ) -> bool:
        """
        Confirm an expensive operation with cost/time estimates.

        Args:
            operation: Description of the operation
            estimated_cost: Estimated cost (e.g., "$0.50")
            estimated_time: Estimated time (e.g., "5 minutes")

        Returns:
            True if confirmed
        """
        details_parts = []
        if estimated_cost:
            details_parts.append(f"Estimated cost: {estimated_cost}")
        if estimated_time:
            details_parts.append(f"Estimated time: {estimated_time}")

        details = "\n".join(details_parts) if details_parts else None

        return await self.confirm(
            f"Proceed with {operation}?",
            details=details,
        )

    async def adjust_research_direction(
        self,
        current_phase: str,
        suggestions: List[str],
    ) -> Optional[str]:
        """
        Allow user to adjust research direction.

        Args:
            current_phase: Current research phase
            suggestions: Suggested adjustments

        Returns:
            Selected adjustment or None to continue
        """
        options = suggestions + ["Continue without changes", "Skip this phase"]

        choice = await self.choose(
            f"Adjust research direction for '{current_phase}'?",
            options,
            default=len(suggestions),  # Default: continue without changes
        )

        if choice == len(suggestions):
            return None  # Continue
        elif choice == len(suggestions) + 1:
            return "skip"  # Skip phase
        else:
            return suggestions[choice]

    def _record(self, action: str, message: str, result: Any, **kwargs) -> None:
        """Record interaction for history/debugging."""
        self._history.append({
            "action": action,
            "message": message,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        })

    def get_history(self) -> List[Dict[str, Any]]:
        """Get interaction history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear interaction history."""
        self._history.clear()


class ProgressTracker:
    """
    Tracks research progress across multiple phases.

    Calculates overall progress based on phase weights and current stage.
    """

    # Default phase weights (sum to 100)
    DEFAULT_WEIGHTS = {
        "market": 20,
        "financial": 20,
        "competitor": 20,
        "brand": 20,
        "sales": 20,
    }

    # Stage progress within a phase
    STAGE_PROGRESS = {
        ProgressStage.INITIALIZING: 0,
        ProgressStage.SEARCH: 25,
        ProgressStage.EXTRACT: 50,
        ProgressStage.ANALYZE: 75,
        ProgressStage.GENERATE: 90,
        ProgressStage.COMPLETE: 100,
        ProgressStage.FAILED: 100,  # Phase done (even if failed)
    }

    def __init__(
        self,
        phases: List[str],
        weights: Optional[Dict[str, int]] = None,
        callback: Optional[ProgressCallback] = None,
    ):
        """
        Initialize progress tracker.

        Args:
            phases: List of phase names to track
            weights: Custom phase weights (must sum to 100)
            callback: Progress callback for notifications
        """
        self.phases = phases
        self.weights = weights or {p: 100 // len(phases) for p in phases}
        self.callback = callback

        self._phase_progress: Dict[str, int] = {p: 0 for p in phases}
        self._phase_stage: Dict[str, ProgressStage] = {
            p: ProgressStage.INITIALIZING for p in phases
        }
        self._started = False
        self._completed = False

    @property
    def overall_progress(self) -> int:
        """Calculate overall progress (0-100)."""
        total = 0
        for phase in self.phases:
            phase_weight = self.weights.get(phase, 0)
            phase_progress = self._phase_progress.get(phase, 0)
            total += (phase_weight * phase_progress) / 100
        return int(total)

    async def start(self) -> None:
        """Start progress tracking."""
        self._started = True
        if self.callback:
            await self.callback.on_stage_start("research", "Starting research...")
            await self.callback.on_progress(ProgressEvent(
                stage="initializing",
                progress=0,
                message="Initializing research pipeline...",
            ))

    async def update_phase(
        self,
        phase: str,
        stage: Union[ProgressStage, str],
        message: str = "",
    ) -> None:
        """
        Update progress for a phase.

        Args:
            phase: Phase name
            stage: Current stage in the phase
            message: Progress message
        """
        if isinstance(stage, str):
            stage = ProgressStage(stage)

        self._phase_stage[phase] = stage
        self._phase_progress[phase] = self.STAGE_PROGRESS.get(stage, 0)

        if self.callback:
            await self.callback.on_progress(ProgressEvent(
                stage=stage.value,
                progress=self.overall_progress,
                message=message or f"{phase}: {stage.value}",
                phase=phase,
            ))

    async def phase_start(self, phase: str) -> None:
        """Mark a phase as started."""
        await self.update_phase(phase, ProgressStage.INITIALIZING, f"Starting {phase} research...")
        if self.callback:
            await self.callback.on_stage_start(phase, f"Starting {phase} research...")

    async def phase_complete(self, phase: str, success: bool = True) -> None:
        """Mark a phase as completed."""
        stage = ProgressStage.COMPLETE if success else ProgressStage.FAILED
        status = "completed" if success else "failed"
        await self.update_phase(phase, stage, f"{phase.title()} research {status}")
        if self.callback:
            await self.callback.on_stage_complete(phase, f"{phase.title()} research {status}")

    async def complete(self) -> None:
        """Mark all research as completed."""
        self._completed = True
        if self.callback:
            await self.callback.on_progress(ProgressEvent(
                stage="complete",
                progress=100,
                message="Research completed",
            ))
            await self.callback.on_stage_complete("research", "Research completed successfully")

    async def fail(self, error: str, phase: Optional[str] = None) -> None:
        """Mark research as failed."""
        self._completed = True
        if self.callback:
            await self.callback.on_error(error, phase)

    def get_status(self) -> Dict[str, Any]:
        """Get current progress status."""
        return {
            "overall_progress": self.overall_progress,
            "started": self._started,
            "completed": self._completed,
            "phases": {
                phase: {
                    "progress": self._phase_progress[phase],
                    "stage": self._phase_stage[phase].value,
                }
                for phase in self.phases
            },
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_interactive_session(enabled: Optional[bool] = None) -> InteractiveSession:
    """
    Create an interactive session based on configuration.

    Args:
        enabled: Override enabled setting (uses config if None)

    Returns:
        InteractiveSession instance
    """
    from ..core.config import get_settings

    settings = get_settings()

    if enabled is None:
        enabled = settings.is_interactive

    return InteractiveSession(enabled=enabled)


def create_progress_tracker(
    phases: Optional[List[str]] = None,
    callback: Optional[ProgressCallback] = None,
    console: bool = False,
) -> ProgressTracker:
    """
    Create a progress tracker.

    Args:
        phases: Phases to track (defaults to standard 5)
        callback: Progress callback
        console: Add console callback if True

    Returns:
        ProgressTracker instance
    """
    if phases is None:
        phases = ["market", "financial", "competitor", "brand", "sales"]

    callbacks = []
    if callback:
        callbacks.append(callback)
    if console:
        callbacks.append(ConsoleProgressCallback())

    combined_callback = MultiProgressCallback(callbacks) if callbacks else None

    return ProgressTracker(phases=phases, callback=combined_callback)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ProgressStage",
    # Data Classes
    "ProgressEvent",
    # Abstract Classes
    "ProgressCallback",
    # Callback Implementations
    "ConsoleProgressCallback",
    "WebSocketProgressCallback",
    "MultiProgressCallback",
    # Session Classes
    "InteractiveSession",
    "ProgressTracker",
    # Factory Functions
    "create_interactive_session",
    "create_progress_tracker",
]
