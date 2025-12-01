# Pipeline Module Documentation

This module implements the **Pipeline Architecture**, which replaces the legacy LangGraph-based orchestrator. It provides a robust, testable, and linear execution flow for research tasks.

## 1. Core Pipeline (`src/pipeline/pipeline.py`)

The engine that executes stages in sequence, handling retries, timeouts, and checkpointing.

### Class: `Pipeline`

- **`execute(self, input, ctx)`**: Runs the pipeline from the beginning.
- **`resume(self, checkpoint, ctx)`**: Resumes execution from a saved checkpoint.
- **Features**:
  - **Retries**: Exponential backoff for transient failures.
  - **Checkpoints**: Saves state after each successful stage.
  - **Timeouts**: Enforces a global timeout budget.

### Class: `PipelineConfig`

- `max_retries`: Max attempts per stage (default 3).
- `timeout_seconds`: Total execution time budget.
- `fail_fast`: Stop on first error (default True).

---

## 2. Research Pipeline (`src/pipeline/research_pipeline.py`)

The specific implementation for company research, orchestrating the various research phases.

### Class: `ResearchPipeline`

- **`research(self, company: CompanyProfile)`**:
  - Configures and runs the research process.
  - Supports **Parallel** or **Sequential** execution of phases.
- **`create_research_pipeline(...)`**: Factory function for easy instantiation.

### Stages

- **`ParallelResearchStage`**: Executes multiple research types (Market, Financial, Competitor, etc.) concurrently using `asyncio.gather`.
- **`SequentialResearchStage`**: Executes phases one by one (slower but lower resource usage).

---

## 3. Stages (`src/pipeline/stage.py`)

The building blocks of the pipeline.

### Class: `Stage` (Abstract)

- **`run(self, input, ctx)`**: The main logic for the stage.
- **`can_retry(self, error)`**: Determines if a failure should trigger a retry.

---

## 4. Context (`src/pipeline/context.py`)

Holds request-scoped data.

### Class: `RequestContext`

- `request_id`: Unique ID for tracing.
- `logger`: Context-aware logger.
- `timeout_budget`: Tracks remaining time.
- `cancellation`: Handles cancellation signals.
