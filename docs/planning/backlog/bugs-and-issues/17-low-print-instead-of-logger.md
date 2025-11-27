# LOW: Print Statements Instead of Logger

## Severity: Low
## File: `src/graph/graph_builder.py`

## Problem

Using `print()` statements instead of the logging system:

```python
async def orchestrator_node(self, state: ResearchState):
    print("--- ORCHESTRATOR ---")
    return {}

async def _run_specialist(self, agent_key: str, ...):
    print(f"--- {agent_key.upper().replace('_', ' ')} ---")

def should_continue(self, state: ResearchState):
    print("--- MAX LOOPS REACHED ---")
    print("--- DECISION: END (Approved) ---")
```

## Impact

- Inconsistent logging across the application
- Cannot control output level (debug/info/warning)
- Cannot redirect output to log files
- Cannot filter or format these messages
- Hard to distinguish from other console output

## Solution

Replace with logger:

```python
from src.core.logger import setup_logger

logger = setup_logger("graph_builder")

class ResearchGraph:
    async def orchestrator_node(self, state: ResearchState):
        logger.info("=== ORCHESTRATOR ===")
        return {}

    async def _run_specialist(self, agent_key: str, ...):
        logger.info(f"=== {agent_key.upper().replace('_', ' ')} ===")

    def should_continue(self, state: ResearchState):
        if state.feedback_loop_count > 2:
            logger.info("Max feedback loops reached")
            return "end"

        if "REJECT" in feedback.upper():
            logger.info("Decision: Loop back for revision")
            return "continue"

        logger.info("Decision: Approved - ending")
        return "end"
```

## Testing

After fix:
1. Run research with different log levels
2. Verify messages appear in log file
3. Verify no more print statements in output
