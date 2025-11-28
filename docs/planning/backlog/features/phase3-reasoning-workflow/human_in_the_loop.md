# Feature: Human-in-the-Loop

## Source

- **Repository:** `bytedance/deer-flow`
- **File:** `src/graph/nodes/human_node.py`

## Description

Sometimes the agent needs approval before taking a critical action (e.g., sending an email, executing a trade).

## Implementation Details

1.  **Approval Node:** A specific node type in the graph that halts execution.
2.  **Notification:** Send a request to the user (via CLI, Email, or UI).
3.  **Resume:** Wait for a signal (API call) to proceed or abort.

## Code Reference

```python
def human_approval(state):
    notify_user("Approve action?")
    return Command(interrupt=True)
```
