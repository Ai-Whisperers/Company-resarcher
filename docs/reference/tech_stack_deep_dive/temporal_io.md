# Temporal.io Integration Guide

## 1. Use Cases

Temporal provides "Durable Execution" for long-running workflows.

- **Reliability**: If the server crashes, the workflow resumes exactly where it left off.
- **Long Durations**: Research tasks that take days (e.g., "Monitor this company for a week") are trivial in Temporal.
- **Retries**: Sophisticated retry policies for flaky external APIs.

## 2. Implementation Strategy

Temporal is a heavy architectural addition. We should use it only if LangGraph's checkpointing is insufficient.

### When to use Temporal vs. LangGraph

- **LangGraph**: Best for "Agentic" loops, chat sessions, and workflows that fit in a single session or database state.
- **Temporal**: Best for infrastructure-level orchestration, scheduled jobs, and mission-critical business processes that must not fail.

### Hybrid Approach

Use Temporal to trigger and monitor LangGraph runs.

1.  **Temporal Workflow**: "Daily Company Monitor"
2.  **Activity**: "Run Research Agent" (calls our LangGraph code)
3.  **Activity**: "Email Report"

## 3. Integration with Stack

- **Python SDK**: We would use `temporalio` python package.
- **Worker**: We would need to run a separate Temporal Worker process that listens for tasks.
