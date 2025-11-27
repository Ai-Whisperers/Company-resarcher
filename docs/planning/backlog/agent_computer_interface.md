# Feature: Agent-Computer Interface (ACI)

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/runtime/action_execution_server.py`

## Description

A standardized API for the agent to interact with the OS. Instead of raw shell commands, provide structured tools for file manipulation, command execution, and editor actions.

## Implementation Details

1.  **Schema:** Define a JSON schema for actions.
    - `CmdRun(command: str)`
    - `FileRead(path: str)`
    - `FileWrite(path: str, content: str)`
    - `FileEdit(path: str, diff: str)`
2.  **Server:** Run a small HTTP/WebSocket server inside the sandbox to handle these requests.
3.  **Client:** The agent sends JSON payloads to the server.

## Code Reference

```python
class Action(BaseModel):
    action: str
    args: Dict[str, Any]

def execute_action(action: Action):
    if action.action == "run":
        return subprocess.run(action.args['command'], shell=True)
```
