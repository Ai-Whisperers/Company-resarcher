# DevOps & Infrastructure Backlog Items

### ~~[INFRA] Docker Compose for Local Dev~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/infrastructure/INFRA-001-docker-compose.md`
> **Implementation:** `docker-compose.yml`
>
> Features:
> - [x] Main API service with health checks
> - [x] CLI runner for batch research
> - [x] Redis cache (optional profile)
> - [x] Prometheus monitoring (optional profile)
> - [x] Proper networking and volume mounts

### ~~[INFRA] CI/CD Pipeline~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/infrastructure/INFRA-cicd-pipeline.md`
> **Implementation:** `.github/workflows/test.yml` (pytest, mypy, ruff on PRs)
