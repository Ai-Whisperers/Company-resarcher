# TEST-001: Test Suite Gaps and Missing Coverage

## Priority: High
## Category: Testing
## Status: Backlog

## Summary

The test suite has significant gaps in coverage, missing integration tests, and some unit tests are failing or incomplete.

## Current Test Status

### Unit Tests (`tests/unit/`)

| File | Status | Issue |
|------|--------|-------|
| `test_api.py` | Failing | Authentication mismatch (see BUG-002) |
| `test_api_models.py` | Unknown | Needs verification |
| `test_base_agent.py` | Partial | Missing edge cases |
| `test_browser_tool.py` | Partial | Mocking incomplete |
| `test_cache.py` | Partial | Missing TTL tests |
| `test_config.py` | Unknown | Needs verification |
| `test_graph_builder.py` | Unknown | Needs verification |
| `test_graph_state.py` | Unknown | Needs verification |
| `test_insight_generator.py` | Unknown | Needs verification |
| `test_orchestrator.py` | Partial | Missing failure cases |
| `test_search_tool.py` | Partial | Network mocking needed |
| `test_smart_router.py` | Unknown | Needs verification |
| `test_specialists.py` | Unknown | Needs verification |
| `test_tech_stack_tool.py` | Unknown | Needs verification |
| `test_writer.py` | Unknown | Needs verification |

### Missing Test Categories

| Category | Location | Status |
|----------|----------|--------|
| Integration | `tests/integration/` | Minimal |
| E2E | `tests/e2e/` | Empty |
| Security | `tests/security/` | Empty |
| Load | `tests/load/` | Empty |
| Regression | `tests/regression/` | Empty |
| Smoke | `tests/smoke/` | Empty |
| Property | `tests/property/` | Empty |

## Critical Coverage Gaps

### 1. Pipeline Components
- `src/pipeline/orchestrator.py` - Core orchestration logic
- `src/pipeline/research_pipeline.py` - Research execution
- `src/pipeline/stages/` - All stage implementations

### 2. Core Services
- `src/core/ai_client.py` - AI provider interactions
- `src/core/cached_ai_client.py` - Caching layer
- `src/core/error_tracking.py` - Error handling
- `src/core/rate_limiter.py` - Rate limiting logic

### 3. Agents
- `src/agents/orchestrator.py` - Agent coordination
- `src/agents/deep_research.py` - Deep research logic
- `src/agents/specialists.py` - Specialist agents

## Proposed Test Plan

### Phase 1: Fix Failing Tests

```bash
# Run and fix failing tests
pytest tests/unit/ -v --tb=long 2>&1 | tee test_results.txt
```

### Phase 2: Add Critical Unit Tests

```python
# tests/unit/test_pipeline_orchestrator.py
import pytest
from src.pipeline.orchestrator import PipelineOrchestrator

@pytest.fixture
def orchestrator():
    return PipelineOrchestrator()

class TestPipelineOrchestrator:
    @pytest.mark.asyncio
    async def test_conduct_research_success(self, orchestrator, mock_ai_client):
        result = await orchestrator.conduct_research("Test Co", "https://test.com")
        assert result["status"] == "success"
        assert "phases" in result

    @pytest.mark.asyncio
    async def test_conduct_research_timeout(self, orchestrator, mock_slow_ai):
        result = await orchestrator.conduct_research("Test Co", "https://test.com")
        assert result["status"] == "failed"
        assert "timeout" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_conduct_research_partial_failure(self, orchestrator, mock_flaky_ai):
        result = await orchestrator.conduct_research("Test Co", "https://test.com")
        assert result["status"] == "partial_success"
```

### Phase 3: Integration Tests

```python
# tests/integration/test_full_pipeline.py
@pytest.mark.integration
@pytest.mark.slow
class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_end_to_end_research(self, real_orchestrator, vcr_cassette):
        """Full pipeline with recorded API responses."""
        result = await real_orchestrator.conduct_research(
            "Test Company",
            "https://example.com"
        )
        assert result["status"] in ["success", "partial_success"]
```

### Phase 4: Security Tests

```python
# tests/security/test_injection.py
@pytest.mark.security
class TestInjectionPrevention:
    def test_sql_injection_prevented(self, db_session):
        # Test SQL injection in search queries
        pass

    def test_xss_prevented_in_output(self, app_client):
        # Test XSS in generated reports
        pass

    def test_ssrf_prevented(self, app_client):
        # Test SSRF in URL inputs
        pass
```

## Implementation Tasks

### Immediate (Week 1)
- [ ] Fix `test_api.py` authentication issues
- [ ] Run full test suite and document failures
- [ ] Add missing fixtures to `conftest.py`

### Short-term (Week 2-3)
- [ ] Add unit tests for pipeline components
- [ ] Add unit tests for core services
- [ ] Achieve 70% code coverage on critical paths

### Medium-term (Week 4-6)
- [ ] Add integration tests with VCR cassettes
- [ ] Add security test suite
- [ ] Add smoke tests for CI

### Long-term
- [ ] Add property-based tests (Hypothesis)
- [ ] Add load tests (Locust)
- [ ] Add E2E tests

## Test Infrastructure Needs

```python
# tests/conftest.py additions

@pytest.fixture
def mock_ai_client():
    """Mock AI client returning predictable responses."""
    pass

@pytest.fixture
def vcr_cassette():
    """VCR cassette for recording/replaying HTTP."""
    pass

@pytest.fixture
def test_database():
    """In-memory test database."""
    pass
```

## Success Criteria

- All existing tests passing
- 70% code coverage on critical paths
- Integration tests for main workflows
- Security tests for OWASP Top 10
- CI pipeline runs all tests
- Test documentation complete
