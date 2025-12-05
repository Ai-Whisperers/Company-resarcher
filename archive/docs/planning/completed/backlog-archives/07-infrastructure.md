# DevOps & Infrastructure Backlog Items

### [INFRA] Docker Compose for Local Dev

**Priority:** Medium
**Description:** Simplify local setup.
**Acceptance Criteria:**

- [ ] Create `docker-compose.yml`.
- [ ] Include `redis`, `postgres` (future), and `app` services.

### [INFRA] CI/CD Pipeline

**Priority:** High
**Description:** Automate testing and linting.
**Acceptance Criteria:**

- [ ] Create `.github/workflows/test.yml`.
- [ ] Run `pytest`, `mypy`, `ruff` on every PR.
