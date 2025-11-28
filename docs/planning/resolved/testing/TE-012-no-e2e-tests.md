# TE-012: No End-to-End Tests

**Priority**: High
**Category**: Testing
**Status**: Open
**Estimated Effort**: Large

## Description

The system lacks end-to-end tests that verify complete research workflows from API request to final report generation. While unit and integration tests check components, nothing tests the full user journey.

## Current State

- No E2E test infrastructure
- Manual testing required for full workflows
- No automated verification of complete research flow
- No tests for CLI interface
- No tests for report generation pipeline

## Impact

- **Unknown system behavior**: Components work but system might not
- **Manual regression testing**: Time-consuming for releases
- **Integration gaps**: Issues at component boundaries
- **User journey untested**: Real usage patterns not validated

## Proposed Solution

1. **Create E2E test infrastructure**:

   ```python
   # tests/e2e/conftest.py
   import pytest
   from src.api.app import app
   from fastapi.testclient import TestClient

   @pytest.fixture(scope="module")
   def e2e_client():
       """Provide E2E test client with full setup."""
       return TestClient(app)

   @pytest.fixture
   def mock_llm_responses():
       """Provide consistent LLM responses for E2E tests."""
       return MockLLMResponses()
   ```

2. **Create full workflow tests**:

   ```python
   @pytest.mark.e2e
   @pytest.mark.slow
   async def test_full_research_workflow(e2e_client, mock_llm_responses):
       """Test complete research workflow from request to report."""
       # 1. Submit research request
       response = e2e_client.post("/api/v1/research", json={
           "company_name": "Test Corp",
           "website": "https://testcorp.com"
       })
       assert response.status_code == 200
       task_id = response.json()["task_id"]

       # 2. Poll for completion
       for _ in range(30):
           status = e2e_client.get(f"/api/v1/research/{task_id}/status")
           if status.json()["status"] == "completed":
               break
           await asyncio.sleep(1)

       # 3. Verify results
       result = e2e_client.get(f"/api/v1/research/{task_id}/result")
       assert result.status_code == 200
       assert "reports" in result.json()

       # 4. Verify report structure
       reports = result.json()["reports"]
       assert "financial" in reports
       assert "market" in reports
   ```

3. **Create CLI E2E tests**:

   ```python
   @pytest.mark.e2e
   def test_cli_research_command():
       """Test CLI research command."""
       result = subprocess.run(
           ["python", "main.py", "--name", "Test Corp", "--url", "https://test.com", "--local"],
           capture_output=True,
           timeout=300
       )
       assert result.returncode == 0
       assert "Research completed" in result.stdout.decode()
   ```

4. **Create report verification tests**:

   ```python
   @pytest.mark.e2e
   def test_report_files_generated(temp_output_dir):
       """Verify all expected report files are generated."""
       # Run research
       run_research("Test Corp", "https://test.com", output_dir=temp_output_dir)

       # Check files exist
       expected_files = [
           "00-Strategic-Context.md",
           "01-Market-Intelligence.md",
           "02-Competitor-Landscape.md",
           "03-Financial-Analysis.md",
       ]
       for filename in expected_files:
           assert (temp_output_dir / filename).exists()
   ```

## Acceptance Criteria

- [ ] E2E test infrastructure set up
- [ ] Full API workflow test (request → status → result)
- [ ] CLI workflow test
- [ ] Report generation verification
- [ ] Tests use mocked external services (deterministic)
- [ ] E2E tests run in CI (with extended timeout)
- [ ] Tests marked with `@pytest.mark.e2e`

## Related Issues

- [TE-002](TE-002-no-integration-tests.md) - No integration test suite
- [TE-009](TE-009-flaky-tests.md) - Tests depend on external services
