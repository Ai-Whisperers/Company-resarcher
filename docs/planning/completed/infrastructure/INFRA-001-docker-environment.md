# INFRA-001: Dockerized Environment Setup

## Problem Statement

Setting up the project locally is complex due to dependencies like Playwright, Redis, and Python libraries. We need a reproducible environment.

## Proposed Solution

Create a `Dockerfile` and `docker-compose.yml` similar to `crawl4ai`. This ensures everyone runs in the same environment with all system deps pre-installed.

## Implementation Steps

1.  Create `Dockerfile` based on `python:3.12-slim`.
2.  Install system deps (build-essential, redis-server).
3.  Install Playwright browsers (`playwright install --with-deps`).
4.  Setup a non-root user for security.
5.  Add `docker-compose.yml` to spin up the app and Redis.

## Code Example

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y redis-server
RUN pip install playwright && playwright install --with-deps
USER appuser
CMD ["python", "main.py"]
```

## Acceptance Criteria

- [ ] `docker-compose up` starts the application and Redis.
- [ ] Playwright works inside the container.
- [ ] Environment is reproducible on any machine.

## Source References

- Repo: `crawl4ai`
- File: `crawl4ai/Dockerfile`
