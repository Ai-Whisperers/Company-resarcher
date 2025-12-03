"""Tests for Agent-Computer Interface."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path

from src.core.agents.agent_computer_interface import (
    Action,
    ActionResult,
    ActionStatus,
    ActionType,
    AgentComputerInterface,
    CommandExecutor,
    DirectoryExecutor,
    EnvironmentExecutor,
    FileExecutor,
    ProcessExecutor,
    get_aci,
    reset_aci,
)


class TestAction:
    """Tests for Action class."""

    def test_create_action(self):
        """Test creating an action."""
        action = Action(
            action_type=ActionType.CMD_RUN,
            args={"command": "echo hello"},
        )

        assert action.action_type == ActionType.CMD_RUN
        assert action.action_id is not None

    def test_to_dict(self):
        """Test serialization."""
        action = Action(
            action_type=ActionType.FILE_READ,
            args={"path": "/test/file.txt"},
            timeout_seconds=60.0,
        )
        data = action.to_dict()

        assert data["action_type"] == "file_read"
        assert data["args"]["path"] == "/test/file.txt"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "action_type": "file_write",
            "args": {"path": "/test.txt", "content": "hello"},
        }
        action = Action.from_dict(data)

        assert action.action_type == ActionType.FILE_WRITE
        assert action.args["content"] == "hello"


class TestActionResult:
    """Tests for ActionResult class."""

    def test_create_result(self):
        """Test creating a result."""
        result = ActionResult(
            action_id="test_1",
            status=ActionStatus.COMPLETED,
            output="success",
        )

        assert result.action_id == "test_1"
        assert result.success is True

    def test_failed_result(self):
        """Test failed result."""
        result = ActionResult(
            action_id="test_2",
            status=ActionStatus.FAILED,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"

    def test_to_dict(self):
        """Test serialization."""
        result = ActionResult(
            action_id="test_3",
            status=ActionStatus.COMPLETED,
            output="data",
            exit_code=0,
        )
        data = result.to_dict()

        assert data["status"] == "completed"
        assert data["success"] is True


class TestCommandExecutor:
    """Tests for CommandExecutor class."""

    def setup_method(self):
        """Create executor."""
        self.executor = CommandExecutor()

    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing a simple command."""
        action = Action(
            action_type=ActionType.CMD_RUN,
            args={"command": "echo hello"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_execute_blocked_command(self):
        """Test blocked command."""
        action = Action(
            action_type=ActionType.CMD_RUN,
            args={"command": "rm -rf /"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.FAILED
        assert "Blocked" in result.error

    @pytest.mark.asyncio
    async def test_command_timeout(self):
        """Test command timeout."""
        action = Action(
            action_type=ActionType.CMD_RUN,
            args={"command": "ping -n 100 127.0.0.1" if os.name == 'nt' else "sleep 100"},
            timeout_seconds=0.1,
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.TIMEOUT


class TestFileExecutor:
    """Tests for FileExecutor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = FileExecutor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_read_file(self):
        """Test reading a file."""
        path = Path(self.temp_dir) / "test.txt"
        path.write_text("Hello World")

        action = Action(
            action_type=ActionType.FILE_READ,
            args={"path": str(path)},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert result.output == "Hello World"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading nonexistent file."""
        action = Action(
            action_type=ActionType.FILE_READ,
            args={"path": "/nonexistent/file.txt"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.FAILED

    @pytest.mark.asyncio
    async def test_write_file(self):
        """Test writing a file."""
        path = Path(self.temp_dir) / "output.txt"

        action = Action(
            action_type=ActionType.FILE_WRITE,
            args={"path": str(path), "content": "New content"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert path.read_text() == "New content"

    @pytest.mark.asyncio
    async def test_edit_file(self):
        """Test editing a file."""
        path = Path(self.temp_dir) / "edit.txt"
        path.write_text("Hello World")

        action = Action(
            action_type=ActionType.FILE_EDIT,
            args={"path": str(path), "old": "World", "new": "Universe"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert path.read_text() == "Hello Universe"

    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test deleting a file."""
        path = Path(self.temp_dir) / "delete.txt"
        path.write_text("To delete")

        action = Action(
            action_type=ActionType.FILE_DELETE,
            args={"path": str(path)},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert not path.exists()

    @pytest.mark.asyncio
    async def test_copy_file(self):
        """Test copying a file."""
        src = Path(self.temp_dir) / "source.txt"
        dst = Path(self.temp_dir) / "dest.txt"
        src.write_text("Copy me")

        action = Action(
            action_type=ActionType.FILE_COPY,
            args={"source": str(src), "destination": str(dst)},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert dst.read_text() == "Copy me"

    @pytest.mark.asyncio
    async def test_move_file(self):
        """Test moving a file."""
        src = Path(self.temp_dir) / "move_src.txt"
        dst = Path(self.temp_dir) / "move_dst.txt"
        src.write_text("Move me")

        action = Action(
            action_type=ActionType.FILE_MOVE,
            args={"source": str(src), "destination": str(dst)},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert not src.exists()
        assert dst.read_text() == "Move me"


class TestDirectoryExecutor:
    """Tests for DirectoryExecutor class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = DirectoryExecutor()

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_create_dir(self):
        """Test creating a directory."""
        path = Path(self.temp_dir) / "new_dir"

        action = Action(
            action_type=ActionType.DIR_CREATE,
            args={"path": str(path)},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert path.is_dir()

    @pytest.mark.asyncio
    async def test_list_dir(self):
        """Test listing a directory."""
        (Path(self.temp_dir) / "file1.txt").write_text("1")
        (Path(self.temp_dir) / "file2.txt").write_text("2")
        (Path(self.temp_dir) / "subdir").mkdir()

        action = Action(
            action_type=ActionType.DIR_LIST,
            args={"path": self.temp_dir},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert len(result.output) == 3

    @pytest.mark.asyncio
    async def test_delete_dir(self):
        """Test deleting a directory."""
        path = Path(self.temp_dir) / "to_delete"
        path.mkdir()

        action = Action(
            action_type=ActionType.DIR_DELETE,
            args={"path": str(path)},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert not path.exists()

    @pytest.mark.asyncio
    async def test_delete_dir_recursive(self):
        """Test deleting a directory recursively."""
        path = Path(self.temp_dir) / "to_delete_recursive"
        path.mkdir()
        (path / "file.txt").write_text("content")

        action = Action(
            action_type=ActionType.DIR_DELETE,
            args={"path": str(path), "recursive": True},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert not path.exists()


class TestEnvironmentExecutor:
    """Tests for EnvironmentExecutor class."""

    def setup_method(self):
        """Create executor."""
        self.executor = EnvironmentExecutor()

    @pytest.mark.asyncio
    async def test_get_env(self):
        """Test getting an environment variable."""
        os.environ["TEST_VAR"] = "test_value"

        action = Action(
            action_type=ActionType.ENV_GET,
            args={"name": "TEST_VAR"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert result.output == "test_value"

        del os.environ["TEST_VAR"]

    @pytest.mark.asyncio
    async def test_get_all_env(self):
        """Test getting all environment variables."""
        action = Action(
            action_type=ActionType.ENV_GET,
            args={},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert isinstance(result.output, dict)

    @pytest.mark.asyncio
    async def test_set_env(self):
        """Test setting an environment variable."""
        action = Action(
            action_type=ActionType.ENV_SET,
            args={"name": "NEW_VAR", "value": "new_value"},
        )

        result = await self.executor.execute(action)

        assert result.status == ActionStatus.COMPLETED
        assert os.environ.get("NEW_VAR") == "new_value"

        del os.environ["NEW_VAR"]


class TestAgentComputerInterface:
    """Tests for AgentComputerInterface class."""

    def setup_method(self):
        """Create temp directory and ACI."""
        self.temp_dir = tempfile.mkdtemp()
        self.aci = AgentComputerInterface(working_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_run_command(self):
        """Test running a command."""
        result = await self.aci.run("echo hello")

        assert result.success
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_read_file(self):
        """Test reading a file."""
        path = Path(self.temp_dir) / "read.txt"
        path.write_text("content")

        result = await self.aci.read_file(str(path))

        assert result.success
        assert result.output == "content"

    @pytest.mark.asyncio
    async def test_write_file(self):
        """Test writing a file."""
        path = Path(self.temp_dir) / "write.txt"

        result = await self.aci.write_file(str(path), "new content")

        assert result.success
        assert path.read_text() == "new content"

    @pytest.mark.asyncio
    async def test_edit_file(self):
        """Test editing a file."""
        path = Path(self.temp_dir) / "edit.txt"
        path.write_text("old text")

        result = await self.aci.edit_file(str(path), "old", "new")

        assert result.success
        assert path.read_text() == "new text"

    @pytest.mark.asyncio
    async def test_list_dir(self):
        """Test listing a directory."""
        (Path(self.temp_dir) / "file.txt").write_text("x")

        result = await self.aci.list_dir(self.temp_dir)

        assert result.success
        assert len(result.output) >= 1

    @pytest.mark.asyncio
    async def test_create_dir(self):
        """Test creating a directory."""
        path = Path(self.temp_dir) / "new"

        result = await self.aci.create_dir(str(path))

        assert result.success
        assert path.is_dir()

    @pytest.mark.asyncio
    async def test_get_history(self):
        """Test action history."""
        await self.aci.run("echo test")
        history = self.aci.get_history()

        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing history."""
        await self.aci.run("echo test")
        self.aci.clear_history()

        assert len(self.aci.get_history()) == 0

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting statistics."""
        await self.aci.run("echo test1")
        await self.aci.run("echo test2")

        stats = self.aci.get_statistics()

        assert stats["total_actions"] == 2
        assert stats["successful"] == 2


class TestACISandboxMode:
    """Tests for ACI in sandbox mode."""

    def setup_method(self):
        """Create temp directory and sandboxed ACI."""
        self.temp_dir = tempfile.mkdtemp()
        self.aci = AgentComputerInterface(
            working_dir=self.temp_dir,
            sandbox_mode=True,
        )

    def teardown_method(self):
        """Cleanup."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_sandbox_allows_internal_paths(self):
        """Test sandbox allows paths within working dir."""
        path = Path(self.temp_dir) / "internal.txt"

        result = await self.aci.write_file(str(path), "content")

        assert result.success

    @pytest.mark.asyncio
    async def test_sandbox_blocks_external_paths(self):
        """Test sandbox blocks paths outside working dir."""
        # This would try to write outside sandbox
        # The executor should reject it
        path = "/tmp/external.txt" if os.name != 'nt' else "C:\\temp\\external.txt"

        result = await self.aci.write_file(path, "content")

        # Should fail due to path validation
        assert result.status == ActionStatus.FAILED


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_aci()

    def teardown_method(self):
        """Reset after each test."""
        reset_aci()

    def test_get_aci_singleton(self):
        """Test singleton behavior."""
        aci1 = get_aci()
        aci2 = get_aci()
        assert aci1 is aci2

    def test_reset_aci(self):
        """Test resetting singleton."""
        aci1 = get_aci()
        reset_aci()
        aci2 = get_aci()
        assert aci1 is not aci2


class TestActionTypeEnum:
    """Tests for ActionType enum."""

    def test_all_action_types(self):
        """Test all action types."""
        types = [
            ActionType.CMD_RUN,
            ActionType.FILE_READ,
            ActionType.FILE_WRITE,
            ActionType.FILE_EDIT,
            ActionType.FILE_DELETE,
            ActionType.FILE_MOVE,
            ActionType.FILE_COPY,
            ActionType.DIR_CREATE,
            ActionType.DIR_LIST,
            ActionType.DIR_DELETE,
            ActionType.PROCESS_LIST,
            ActionType.PROCESS_KILL,
            ActionType.ENV_GET,
            ActionType.ENV_SET,
            ActionType.HTTP_REQUEST,
        ]
        assert len(types) == len(ActionType)

    def test_action_type_values(self):
        """Test action type values."""
        assert ActionType.CMD_RUN.value == "cmd_run"
        assert ActionType.FILE_READ.value == "file_read"
