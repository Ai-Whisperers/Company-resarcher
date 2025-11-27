# Feature: Docker Sandboxing

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/runtime/impl/docker/docker_runtime.py`

## Description

Execute all agent-generated code (Python, Shell) inside ephemeral Docker containers to prevent damage to the host system.

## Implementation Details

1.  **Docker Client:** Use `docker-py` to manage containers.
2.  **Container Lifecycle:**
    - Start a container (e.g., `python:3.10-slim`) for each session.
    - Mount a workspace volume to persist files.
    - Clean up (stop/remove) container after session ends.
3.  **Execution:**
    - Use `container.exec_run(cmd)` to run commands.
    - Capture `stdout` and `stderr`.
4.  **Security:**
    - Limit network access (optional).
    - Limit resource usage (CPU/RAM).
    - Never run as root inside the container (create a `user`).

## Code Reference

```python
import docker
client = docker.from_env()
container = client.containers.run(
    "python:3.10",
    detach=True,
    volumes={workspace_path: {'bind': '/workspace', 'mode': 'rw'}}
)
exec_log = container.exec_run("python script.py")
```
