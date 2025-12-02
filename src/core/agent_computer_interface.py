"""Agent-Computer Interface (ACI) for OS interaction.

This module provides a standardized API for agents to interact with the
operating system through structured actions instead of raw shell commands.

Inspired by OpenHands/OpenHands action execution system.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import subprocess
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions the agent can perform."""

    CMD_RUN = "cmd_run"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    FILE_DELETE = "file_delete"
    FILE_MOVE = "file_move"
    FILE_COPY = "file_copy"
    DIR_CREATE = "dir_create"
    DIR_LIST = "dir_list"
    DIR_DELETE = "dir_delete"
    PROCESS_LIST = "process_list"
    PROCESS_KILL = "process_kill"
    ENV_GET = "env_get"
    ENV_SET = "env_set"
    HTTP_REQUEST = "http_request"


class ActionStatus(str, Enum):
    """Status of an action execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Action:
    """Represents an action to be executed."""

    action_type: ActionType
    args: Dict[str, Any] = field(default_factory=dict)
    action_id: Optional[str] = None
    timeout_seconds: float = 30.0
    working_dir: Optional[str] = None

    def __post_init__(self):
        """Generate action ID if not provided."""
        if self.action_id is None:
            content = f"{self.action_type.value}:{json.dumps(self.args, sort_keys=True)}"
            self.action_id = hashlib.md5(content.encode()).hexdigest()[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "args": self.args,
            "timeout_seconds": self.timeout_seconds,
            "working_dir": self.working_dir,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        """Deserialize from dictionary."""
        return cls(
            action_type=ActionType(data["action_type"]),
            args=data.get("args", {}),
            action_id=data.get("action_id"),
            timeout_seconds=data.get("timeout_seconds", 30.0),
            working_dir=data.get("working_dir"),
        )


@dataclass
class ActionResult:
    """Result of an action execution."""

    action_id: str
    status: ActionStatus
    output: Any = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    @property
    def success(self) -> bool:
        """Check if action was successful."""
        return self.status == ActionStatus.COMPLETED and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "action_id": self.action_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "success": self.success,
        }


class ActionExecutor(ABC):
    """Abstract base class for action executors."""

    @abstractmethod
    async def execute(self, action: Action) -> ActionResult:
        """Execute an action and return the result."""
        pass


class CommandExecutor(ActionExecutor):
    """Executor for shell commands."""

    def __init__(
        self,
        shell: bool = True,
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None,
    ):
        """Initialize executor."""
        self.shell = shell
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or [
            "rm -rf /",
            "format",
            "mkfs",
            ":(){:|:&};:",
        ]

    def _validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate command is safe to execute."""
        for blocked in self.blocked_commands:
            if blocked in command:
                return False, f"Blocked command pattern: {blocked}"

        if self.allowed_commands is not None:
            cmd_name = command.split()[0] if command else ""
            if cmd_name not in self.allowed_commands:
                return False, f"Command not in allowed list: {cmd_name}"

        return True, ""

    async def execute(self, action: Action) -> ActionResult:
        """Execute a shell command."""
        result = ActionResult(
            action_id=action.action_id,
            status=ActionStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        command = action.args.get("command", "")

        valid, error = self._validate_command(command)
        if not valid:
            result.status = ActionStatus.FAILED
            result.error = error
            result.end_time = datetime.utcnow()
            return result

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=action.working_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=action.timeout_seconds,
                )

                result.output = stdout.decode('utf-8', errors='replace')
                result.exit_code = process.returncode

                if process.returncode != 0:
                    result.error = stderr.decode('utf-8', errors='replace')
                    result.status = ActionStatus.FAILED
                else:
                    result.status = ActionStatus.COMPLETED

            except asyncio.TimeoutError:
                process.kill()
                result.status = ActionStatus.TIMEOUT
                result.error = f"Command timed out after {action.timeout_seconds}s"

        except Exception as e:
            result.status = ActionStatus.FAILED
            result.error = str(e)

        result.end_time = datetime.utcnow()
        return result


class FileExecutor(ActionExecutor):
    """Executor for file operations."""

    def __init__(
        self,
        base_path: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """Initialize executor."""
        self.base_path = Path(base_path) if base_path else None
        self.max_file_size = max_file_size

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate path."""
        resolved = Path(path).resolve()

        if self.base_path:
            base = self.base_path.resolve()
            if not str(resolved).startswith(str(base)):
                raise ValueError(f"Path {path} is outside allowed directory")

        return resolved

    async def execute(self, action: Action) -> ActionResult:
        """Execute a file operation."""
        result = ActionResult(
            action_id=action.action_id,
            status=ActionStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        try:
            if action.action_type == ActionType.FILE_READ:
                result.output = await self._read_file(action.args)
            elif action.action_type == ActionType.FILE_WRITE:
                result.output = await self._write_file(action.args)
            elif action.action_type == ActionType.FILE_EDIT:
                result.output = await self._edit_file(action.args)
            elif action.action_type == ActionType.FILE_DELETE:
                result.output = await self._delete_file(action.args)
            elif action.action_type == ActionType.FILE_MOVE:
                result.output = await self._move_file(action.args)
            elif action.action_type == ActionType.FILE_COPY:
                result.output = await self._copy_file(action.args)
            else:
                raise ValueError(f"Unknown file action: {action.action_type}")

            result.status = ActionStatus.COMPLETED

        except Exception as e:
            result.status = ActionStatus.FAILED
            result.error = str(e)

        result.end_time = datetime.utcnow()
        return result

    async def _read_file(self, args: Dict[str, Any]) -> str:
        """Read file contents."""
        path = self._resolve_path(args["path"])

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.stat().st_size > self.max_file_size:
            raise ValueError(f"File too large: {path.stat().st_size} bytes")

        return path.read_text(encoding=args.get("encoding", "utf-8"))

    async def _write_file(self, args: Dict[str, Any]) -> str:
        """Write file contents."""
        path = self._resolve_path(args["path"])
        content = args["content"]

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=args.get("encoding", "utf-8"))

        return f"Written {len(content)} bytes to {path}"

    async def _edit_file(self, args: Dict[str, Any]) -> str:
        """Edit file with diff/replacements."""
        path = self._resolve_path(args["path"])

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text()

        if "old" in args and "new" in args:
            old = args["old"]
            new = args["new"]
            if old not in content:
                raise ValueError(f"Old text not found in file")
            content = content.replace(old, new, 1)
        elif "diff" in args:
            content = self._apply_diff(content, args["diff"])
        else:
            raise ValueError("Edit requires 'old'/'new' or 'diff'")

        path.write_text(content)
        return f"Edited {path}"

    def _apply_diff(self, content: str, diff: str) -> str:
        """Apply a unified diff to content."""
        lines = content.split('\n')

        for line in diff.split('\n'):
            if line.startswith('-') and not line.startswith('---'):
                old_line = line[1:]
                if old_line in lines:
                    lines.remove(old_line)
            elif line.startswith('+') and not line.startswith('+++'):
                new_line = line[1:]
                lines.append(new_line)

        return '\n'.join(lines)

    async def _delete_file(self, args: Dict[str, Any]) -> str:
        """Delete a file."""
        path = self._resolve_path(args["path"])

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        path.unlink()
        return f"Deleted {path}"

    async def _move_file(self, args: Dict[str, Any]) -> str:
        """Move a file."""
        src = self._resolve_path(args["source"])
        dst = self._resolve_path(args["destination"])

        shutil.move(str(src), str(dst))
        return f"Moved {src} to {dst}"

    async def _copy_file(self, args: Dict[str, Any]) -> str:
        """Copy a file."""
        src = self._resolve_path(args["source"])
        dst = self._resolve_path(args["destination"])

        shutil.copy2(str(src), str(dst))
        return f"Copied {src} to {dst}"


class DirectoryExecutor(ActionExecutor):
    """Executor for directory operations."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize executor."""
        self.base_path = Path(base_path) if base_path else None

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate path."""
        resolved = Path(path).resolve()

        if self.base_path:
            base = self.base_path.resolve()
            if not str(resolved).startswith(str(base)):
                raise ValueError(f"Path {path} is outside allowed directory")

        return resolved

    async def execute(self, action: Action) -> ActionResult:
        """Execute a directory operation."""
        result = ActionResult(
            action_id=action.action_id,
            status=ActionStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        try:
            if action.action_type == ActionType.DIR_CREATE:
                result.output = await self._create_dir(action.args)
            elif action.action_type == ActionType.DIR_LIST:
                result.output = await self._list_dir(action.args)
            elif action.action_type == ActionType.DIR_DELETE:
                result.output = await self._delete_dir(action.args)
            else:
                raise ValueError(f"Unknown directory action: {action.action_type}")

            result.status = ActionStatus.COMPLETED

        except Exception as e:
            result.status = ActionStatus.FAILED
            result.error = str(e)

        result.end_time = datetime.utcnow()
        return result

    async def _create_dir(self, args: Dict[str, Any]) -> str:
        """Create a directory."""
        path = self._resolve_path(args["path"])
        path.mkdir(parents=args.get("parents", True), exist_ok=args.get("exist_ok", True))
        return f"Created directory {path}"

    async def _list_dir(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List directory contents."""
        path = self._resolve_path(args["path"])

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        entries = []
        for entry in path.iterdir():
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        return sorted(entries, key=lambda e: (not e["is_dir"], e["name"]))

    async def _delete_dir(self, args: Dict[str, Any]) -> str:
        """Delete a directory."""
        path = self._resolve_path(args["path"])

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if args.get("recursive", False):
            shutil.rmtree(str(path))
        else:
            path.rmdir()

        return f"Deleted directory {path}"


class ProcessExecutor(ActionExecutor):
    """Executor for process operations."""

    async def execute(self, action: Action) -> ActionResult:
        """Execute a process operation."""
        result = ActionResult(
            action_id=action.action_id,
            status=ActionStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        try:
            if action.action_type == ActionType.PROCESS_LIST:
                result.output = await self._list_processes(action.args)
            elif action.action_type == ActionType.PROCESS_KILL:
                result.output = await self._kill_process(action.args)
            else:
                raise ValueError(f"Unknown process action: {action.action_type}")

            result.status = ActionStatus.COMPLETED

        except Exception as e:
            result.status = ActionStatus.FAILED
            result.error = str(e)

        result.end_time = datetime.utcnow()
        return result

    async def _list_processes(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List running processes."""
        try:
            import psutil

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "status": info['status'],
                        "memory_percent": round(info['memory_percent'], 2),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return processes

        except ImportError:
            if os.name == 'nt':
                output = subprocess.check_output(['tasklist'], text=True)
            else:
                output = subprocess.check_output(['ps', 'aux'], text=True)
            return [{"raw": output}]

    async def _kill_process(self, args: Dict[str, Any]) -> str:
        """Kill a process by PID."""
        pid = args["pid"]
        signal_name = args.get("signal", "TERM")

        try:
            import psutil
            proc = psutil.Process(pid)
            if signal_name == "KILL":
                proc.kill()
            else:
                proc.terminate()
            return f"Terminated process {pid}"
        except ImportError:
            os.kill(pid, 9 if signal_name == "KILL" else 15)
            return f"Sent signal to process {pid}"


class EnvironmentExecutor(ActionExecutor):
    """Executor for environment variable operations."""

    async def execute(self, action: Action) -> ActionResult:
        """Execute an environment operation."""
        result = ActionResult(
            action_id=action.action_id,
            status=ActionStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        try:
            if action.action_type == ActionType.ENV_GET:
                var_name = action.args.get("name")
                if var_name:
                    result.output = os.environ.get(var_name)
                else:
                    result.output = dict(os.environ)
            elif action.action_type == ActionType.ENV_SET:
                var_name = action.args["name"]
                var_value = action.args["value"]
                os.environ[var_name] = var_value
                result.output = f"Set {var_name}={var_value}"
            else:
                raise ValueError(f"Unknown env action: {action.action_type}")

            result.status = ActionStatus.COMPLETED

        except Exception as e:
            result.status = ActionStatus.FAILED
            result.error = str(e)

        result.end_time = datetime.utcnow()
        return result


class AgentComputerInterface:
    """Main interface for agent-computer interaction."""

    def __init__(
        self,
        working_dir: Optional[str] = None,
        sandbox_mode: bool = False,
    ):
        """Initialize ACI."""
        self.working_dir = working_dir or os.getcwd()
        self.sandbox_mode = sandbox_mode

        base_path = working_dir if sandbox_mode else None

        self.executors: Dict[ActionType, ActionExecutor] = {
            ActionType.CMD_RUN: CommandExecutor(),
            ActionType.FILE_READ: FileExecutor(base_path),
            ActionType.FILE_WRITE: FileExecutor(base_path),
            ActionType.FILE_EDIT: FileExecutor(base_path),
            ActionType.FILE_DELETE: FileExecutor(base_path),
            ActionType.FILE_MOVE: FileExecutor(base_path),
            ActionType.FILE_COPY: FileExecutor(base_path),
            ActionType.DIR_CREATE: DirectoryExecutor(base_path),
            ActionType.DIR_LIST: DirectoryExecutor(base_path),
            ActionType.DIR_DELETE: DirectoryExecutor(base_path),
            ActionType.PROCESS_LIST: ProcessExecutor(),
            ActionType.PROCESS_KILL: ProcessExecutor(),
            ActionType.ENV_GET: EnvironmentExecutor(),
            ActionType.ENV_SET: EnvironmentExecutor(),
        }

        self._history: List[Tuple[Action, ActionResult]] = []
        self._lock = threading.Lock()

    async def execute(self, action: Action) -> ActionResult:
        """Execute an action."""
        if action.working_dir is None:
            action.working_dir = self.working_dir

        executor = self.executors.get(action.action_type)
        if executor is None:
            return ActionResult(
                action_id=action.action_id,
                status=ActionStatus.FAILED,
                error=f"No executor for action type: {action.action_type}",
            )

        result = await executor.execute(action)

        with self._lock:
            self._history.append((action, result))

        return result

    async def run(self, command: str, timeout: float = 30.0) -> ActionResult:
        """Convenience method to run a command."""
        action = Action(
            action_type=ActionType.CMD_RUN,
            args={"command": command},
            timeout_seconds=timeout,
        )
        return await self.execute(action)

    async def read_file(self, path: str) -> ActionResult:
        """Convenience method to read a file."""
        action = Action(
            action_type=ActionType.FILE_READ,
            args={"path": path},
        )
        return await self.execute(action)

    async def write_file(self, path: str, content: str) -> ActionResult:
        """Convenience method to write a file."""
        action = Action(
            action_type=ActionType.FILE_WRITE,
            args={"path": path, "content": content},
        )
        return await self.execute(action)

    async def edit_file(
        self,
        path: str,
        old: str,
        new: str,
    ) -> ActionResult:
        """Convenience method to edit a file."""
        action = Action(
            action_type=ActionType.FILE_EDIT,
            args={"path": path, "old": old, "new": new},
        )
        return await self.execute(action)

    async def list_dir(self, path: str) -> ActionResult:
        """Convenience method to list a directory."""
        action = Action(
            action_type=ActionType.DIR_LIST,
            args={"path": path},
        )
        return await self.execute(action)

    async def create_dir(self, path: str) -> ActionResult:
        """Convenience method to create a directory."""
        action = Action(
            action_type=ActionType.DIR_CREATE,
            args={"path": path},
        )
        return await self.execute(action)

    def get_history(self) -> List[Tuple[Action, ActionResult]]:
        """Get action history."""
        with self._lock:
            return self._history.copy()

    def clear_history(self) -> None:
        """Clear action history."""
        with self._lock:
            self._history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about executed actions."""
        with self._lock:
            total = len(self._history)
            successful = sum(1 for _, r in self._history if r.success)
            failed = total - successful

            by_type: Dict[str, int] = {}
            for action, _ in self._history:
                key = action.action_type.value
                by_type[key] = by_type.get(key, 0) + 1

            avg_duration = 0.0
            if total > 0:
                avg_duration = sum(r.duration_ms for _, r in self._history) / total

            return {
                "total_actions": total,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / total if total > 0 else 0,
                "by_type": by_type,
                "avg_duration_ms": avg_duration,
            }


class ACIServer:
    """HTTP/WebSocket server for ACI."""

    def __init__(
        self,
        aci: AgentComputerInterface,
        host: str = "127.0.0.1",
        port: int = 8080,
    ):
        """Initialize server."""
        self.aci = aci
        self.host = host
        self.port = port
        self._running = False

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming request."""
        try:
            action = Action.from_dict(request_data)
            result = await self.aci.execute(action)
            return result.to_dict()
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }

    def start(self) -> None:
        """Start the server (placeholder)."""
        self._running = True
        logger.info(f"ACI Server started on {self.host}:{self.port}")

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
        logger.info("ACI Server stopped")


_aci_instance: Optional[AgentComputerInterface] = None
_aci_lock = threading.Lock()


def get_aci(
    working_dir: Optional[str] = None,
    sandbox_mode: bool = False,
) -> AgentComputerInterface:
    """Get singleton ACI instance."""
    global _aci_instance

    with _aci_lock:
        if _aci_instance is None:
            _aci_instance = AgentComputerInterface(working_dir, sandbox_mode)
        return _aci_instance


def reset_aci() -> None:
    """Reset singleton ACI instance."""
    global _aci_instance

    with _aci_lock:
        _aci_instance = None
