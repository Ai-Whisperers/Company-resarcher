import docker
import logging
import os
import re
import tarfile
import io
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# Pattern to detect dangerous shell characters in commands
DANGEROUS_CHARS_PATTERN = re.compile(r'[;&|$`\n\\]')

# Allowed characters for path components (alphanumeric, dash, underscore, dot, slash)
SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_.\-/]+$')


class DockerSandbox:
    """
    Manages ephemeral Docker containers for safe code execution.
    """

    def __init__(self, image: str = "python:3.10-slim", timeout: int = 60):
        self.image = image
        self.timeout = timeout
        self.client = docker.from_env()
        self.container = None

    def start(self):
        """Start the sandbox container."""
        try:
            logger.info(f"Starting sandbox container with image: {self.image}")
            self.container = self.client.containers.run(
                self.image,
                detach=True,
                tty=True,
                # Keep the container alive
                command="tail -f /dev/null",
                # Basic security limits
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU
                network_disabled=False,  # Allow network for now (pip install etc), maybe restrict later
            )
            logger.info(f"Sandbox started: {self.container.id[:10]}")
        except Exception as e:
            logger.error(f"Failed to start sandbox: {e}")
            raise

    def stop(self):
        """Stop and remove the sandbox container."""
        if self.container:
            try:
                logger.info(f"Stopping sandbox: {self.container.id[:10]}")
                self.container.stop()
                self.container.remove()
                self.container = None
            except Exception as e:
                logger.error(f"Error stopping sandbox: {e}")

    def execute(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command inside the sandbox.
        Returns: (exit_code, stdout, stderr)
        """
        if not self.container:
            raise RuntimeError("Sandbox is not running. Call start() first.")

        try:
            logger.info(f"Executing in sandbox: {command}")
            exec_result = self.container.exec_run(
                command, demux=True  # Separate stdout and stderr
            )

            exit_code = exec_result.exit_code
            stdout = (
                exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
            )
            stderr = (
                exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
            )

            return exit_code, stdout, stderr
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return -1, "", str(e)

    def _validate_path(self, path: str) -> str:
        """
        Validate and sanitize a path for use inside the container.
        Prevents path traversal and command injection attacks.

        Args:
            path: The path to validate

        Returns:
            The validated path

        Raises:
            ValueError: If the path contains dangerous characters or traversal attempts
        """
        if not path:
            raise ValueError("Path cannot be empty")

        # Check for dangerous characters that could enable injection
        if DANGEROUS_CHARS_PATTERN.search(path):
            raise ValueError(f"Path contains dangerous characters: {path}")

        # Check path only contains safe characters
        if not SAFE_PATH_PATTERN.match(path):
            raise ValueError(f"Path contains invalid characters: {path}")

        # Normalize the path and check for traversal attempts
        normalized = os.path.normpath(path)

        # Check for path traversal (.. components that escape)
        if normalized.startswith('..') or '/..' in normalized:
            raise ValueError(f"Path traversal detected: {path}")

        # Ensure path is absolute or make it absolute within /workspace
        if not normalized.startswith('/'):
            normalized = f"/workspace/{normalized}"

        return normalized

    def copy_to_container(self, content: str, path: str):
        """
        Copy string content to a file inside the container.

        Args:
            content: The string content to copy
            path: The destination path inside the container (will be validated)

        Raises:
            RuntimeError: If sandbox is not running
            ValueError: If path is invalid or contains dangerous characters
        """
        if not self.container:
            raise RuntimeError("Sandbox is not running.")

        # Validate and sanitize the path
        safe_path = self._validate_path(path)

        try:
            # Create a tar archive in memory
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                data = content.encode("utf-8")
                tarinfo = tarfile.TarInfo(name=os.path.basename(safe_path))
                tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))

            tar_stream.seek(0)

            # Put archive into container
            dirname = os.path.dirname(safe_path)
            if not dirname:
                dirname = "/"  # Default to root if no dir specified

            # Ensure directory exists using list form (no shell injection)
            self.container.exec_run(["mkdir", "-p", dirname])

            self.container.put_archive(path=dirname, data=tar_stream)
            logger.info(f"Copied content to {safe_path}")
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to copy file to container: {e}")
            raise

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
