# TE-023: No Smoke Test Suite

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Small

## Description

No quick smoke test suite exists to verify basic functionality after deployments. A smoke test should run in under 2 minutes and verify critical paths work.

## Current State

- No smoke test concept
- Full test suite is slow
- No quick verification for deployments
- No health check automation

## Impact

- **Slow deployment verification**: Must run full suite or test manually
- **Deployment confidence**: Unknown if deployment works
- **Rollback delays**: Issues discovered late
- **Manual verification**: Time-consuming post-deploy checks

## What Smoke Tests Should Cover

| Area | Test | Time |
|------|------|------|
| API | Health endpoint responds | <1s |
| API | Research endpoint accepts request | <2s |
| Database | Connection works | <1s |
| LLM | Basic generation works | <5s |
| Search | Search tool initializes | <1s |
| Graph | Graph builds without error | <2s |

## Proposed Solution

1. **Create smoke test directory**:

   ```
   tests/
   └── smoke/
       ├── __init__.py
       ├── test_api_smoke.py
       ├── test_database_smoke.py
       ├── test_llm_smoke.py
       └── conftest.py
   ```

2. **Create API smoke tests**:

   ```python
   # tests/smoke/test_api_smoke.py
   import pytest

   @pytest.mark.smoke
   @pytest.mark.timeout(5)
   def test_health_endpoint(api_client):
       """Verify health endpoint responds."""
       response = api_client.get("/health")
       assert response.status_code == 200
       assert response.json()["status"] == "healthy"

   @pytest.mark.smoke
   @pytest.mark.timeout(10)
   def test_research_endpoint_accepts_request(api_client):
       """Verify research endpoint accepts valid request."""
       response = api_client.post("/api/v1/research", json={
           "company_name": "Smoke Test Corp",
           "website": "https://smoketest.com"
       })
       assert response.status_code == 200
       assert "task_id" in response.json()
   ```

3. **Create database smoke tests**:

   ```python
   @pytest.mark.smoke
   @pytest.mark.timeout(5)
   def test_database_connection():
       """Verify database connection works."""
       from src.api.database import engine
       with engine.connect() as conn:
           result = conn.execute("SELECT 1")
           assert result.scalar() == 1
   ```

4. **Create LLM smoke tests**:

   ```python
   @pytest.mark.smoke
   @pytest.mark.timeout(30)
   async def test_llm_generation():
       """Verify LLM can generate response."""
       from src.core.ai_client import get_ai_client
       client = get_ai_client()
       response = await client.generate("Say 'smoke test passed'")
       assert response is not None
       assert len(response) > 0
   ```

5. **Run smoke tests**:

   ```bash
   # Run only smoke tests
   pytest -m smoke -v --timeout=60

   # Run in CI after deployment
   pytest -m smoke --tb=short
   ```

6. **Add to deployment pipeline**:

   ```yaml
   deploy:
     steps:
       - name: Deploy to production
         run: ./deploy.sh

       - name: Run smoke tests
         run: |
           sleep 10  # Wait for deployment
           pytest -m smoke --timeout=60
         env:
           API_URL: https://api.production.com

       - name: Rollback on failure
         if: failure()
         run: ./rollback.sh
   ```

## Acceptance Criteria

- [ ] Smoke test directory created
- [ ] Health endpoint smoke test
- [ ] Research endpoint smoke test
- [ ] Database connection smoke test
- [ ] All smoke tests complete in <2 minutes
- [ ] Smoke tests marked with `@pytest.mark.smoke`
- [ ] Smoke tests integrated into deployment pipeline

## Related Issues

- [TE-012](TE-012-no-e2e-tests.md) - No end-to-end tests
- [TE-013](TE-013-slow-tests.md) - Tests are too slow
