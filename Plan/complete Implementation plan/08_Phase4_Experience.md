# Phase 4: Experience & Collaboration Implementation Plan

This document details the implementation of the User Interface and API layer for the Company Researcher system.

## 1. API Layer (FastAPI)

We will expose the core research functionality via a REST API.

### Endpoints

- `POST /api/v1/research`

  - **Input**: `{"company_name": "...", "url": "...", "industry": "...", "country": "..."}`
  - **Output**: `{"task_id": "..."}` (Async) or `{"report": "..."}` (Sync for MVP)
  - **Description**: Triggers the `ResearchOrchestrator`.

- `GET /api/v1/research/{task_id}`

  - **Output**: `{"status": "running|completed|failed", "result": ...}`
  - **Description**: Checks the status of a background research task.

- `GET /api/v1/vault/companies`
  - **Output**: `[{"name": "...", "industry": "..."}]`
  - **Description**: Lists companies stored in the Vault.

### Implementation Details

- Use `FastAPI` for the framework.
- Use `Pydantic` for request/response validation.
- Use `uvicorn` as the server.
- **Async Handling**: For the MVP, we might keep it synchronous or use `BackgroundTasks` in FastAPI. Ideally, we should use a task queue (Celery/Redis), but that adds infrastructure complexity. We will start with `BackgroundTasks`.

## 2. User Interface (Streamlit)

A simple, interactive dashboard for users to run research and view results.

### Pages

1.  **New Research**: Form to input company details and start a job.
2.  **Vault Explorer**: View past reports and aggregated sector data.
3.  **Settings**: Configure API keys (optional).

### Features

- **Real-time Logs**: Display logs from the research process (using a custom log handler or by polling).
- **Markdown Rendering**: Render the final report beautifully.
- **Download**: Button to download the report as Markdown/PDF.

## 3. Human-in-the-Loop (Future)

- Add a "Review" step in the LangGraph where execution pauses until a human approves via the API/UI.
