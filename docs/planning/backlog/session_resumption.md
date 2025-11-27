# Feature: Session Resumption

## Source

- **Repository:** `OpenHands/OpenHands`
- **File:** `openhands/storage/files.py`

## Description

Long-running research tasks can crash or be interrupted. We need to save the agent's state (chat history, working memory, file state) to disk so it can be resumed later.

## Implementation Details

1.  **State Serialization:** Pickle or JSON dump the agent's `memory` and `history`.
2.  **Checkpointing:** Save state after every step or every N steps.
3.  **ID System:** Assign a unique `session_id` to each run.
4.  **Resume:** `python main.py --resume <session_id>` loads the state and continues.

## Code Reference

```python
def save_checkpoint(session_id, state):
    with open(f"sessions/{session_id}.json", "w") as f:
        json.dump(state, f)

def load_checkpoint(session_id):
    return json.load(open(f"sessions/{session_id}.json"))
```
