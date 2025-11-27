import docker
import logging
import os
import tarfile
import io
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)


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

    def copy_to_container(self, content: str, path: str):
        """
        Copy string content to a file inside the container.
        """
        if not self.container:
            raise RuntimeError("Sandbox is not running.")

        try:
            # Create a tar archive in memory
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                data = content.encode("utf-8")
                tarinfo = tarfile.TarInfo(name=os.path.basename(path))
                tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))

            tar_stream.seek(0)

            # Put archive into container
            dirname = os.path.dirname(path)
            if not dirname:
                dirname = "/"  # Default to root if no dir specified

            # Ensure directory exists
            self.execute(f"mkdir -p {dirname}")

            self.container.put_archive(path=dirname, data=tar_stream)
            logger.info(f"Copied content to {path}")
        except Exception as e:
            logger.error(f"Failed to copy file to container: {e}")
            raise

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
