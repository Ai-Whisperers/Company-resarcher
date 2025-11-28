# Feature: Hierarchical Planning

## Source

- **Repository:** `bytedance/deer-flow`
- **File:** `src/agents/planner.py`

## Description

For complex tasks, a single agent isn't enough. Use a hierarchy: A "Manager" breaks down the task, "Planners" design the steps, and "Executors" do the work.

## Implementation Details

1.  **Roles:**
    - **Manager:** Decomposes high-level goal.
    - **Planner:** Creates a DAG of steps.
    - **Executor:** Runs a specific step.
2.  **Communication:** Structured message passing between layers.

## Code Reference

```python
plan = manager.create_plan(goal)
for step in plan:
    executor.execute(step)
```
