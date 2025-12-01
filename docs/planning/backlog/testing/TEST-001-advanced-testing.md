# TEST-001: Advanced Testing Suite

## Priority: Medium

## Category: Testing

## Status: Backlog

## Summary

Implement comprehensive testing including agent behavior tests, golden outputs, and chaos testing.

## Current State

- Basic unit tests exist
- Some integration tests
- No agent behavior testing
- No golden output comparisons
- No chaos/resilience testing

## Implementation Tasks

### A. Agent Behavior Testing

- [ ] Create `tests/agents/test_agent_behavior.py`
- [ ] Test retry behavior on transient failures
- [ ] Test timeout budget respect
- [ ] Test source deduplication
- [ ] Test graceful degradation
- [ ] Use mocks for external dependencies

```python
async def test_retries_on_transient_failure(self, agent, mock_search):
    """Agent should retry on rate limits."""
    mock_search.side_effect = [
        RateLimitError(retry_after=1),
        RateLimitError(retry_after=1),
        [{"url": "https://example.com", "title": "Test"}]
    ]

    result = await agent.research(CompanyProfile(name="Test"))

    assert mock_search.call_count == 3
    assert result is not None
```

### B. Golden Output Testing

- [ ] Create `tests/golden/` directory
- [ ] Store known-good report examples
- [ ] Test report structure matches expected
- [ ] Test required sections present
- [ ] Calculate similarity scores
- [ ] Flag significant deviations

```python
def test_financial_report_structure(self, financial_agent):
    result = await financial_agent.research(company)

    required_sections = [
        "## Revenue", "## Margins", "## Growth", "## Risk Factors"
    ]
    for section in required_sections:
        assert section in result.markdown

    similarity = calculate_similarity(result.markdown, golden)
    assert similarity > 0.7
```

### C. Chaos Testing

- [ ] Create `tests/chaos/test_resilience.py`
- [ ] Test survival of search API outage
- [ ] Test partial agent failure
- [ ] Test network latency spikes
- [ ] Test cache unavailability
- [ ] Test concurrent request handling

```python
async def test_survives_search_api_outage(self, pipeline):
    """System should degrade gracefully if search fails."""
    with patch("src.tools.search_tool.SearchTool.search") as mock:
        mock.side_effect = ConnectionError("API unavailable")

        result = await pipeline.research(company)

        assert result is not None
        assert "website" in result.sources_used
```

### D. Performance Testing

- [ ] Create `tests/performance/test_benchmarks.py`
- [ ] Benchmark single agent execution
- [ ] Benchmark full pipeline execution
- [ ] Test with varying company complexities
- [ ] Track performance regressions
- [ ] Set performance budgets

### E. Contract Testing

- [ ] Test API response schemas
- [ ] Validate LLM output formats
- [ ] Test inter-agent communication contracts
- [ ] Ensure backwards compatibility

## Test Data

- [ ] Create `tests/fixtures/` with sample companies
- [ ] Include various industries
- [ ] Include edge cases (new companies, private companies)
- [ ] Mock responses for reproducibility

## Acceptance Criteria

- [ ] 80%+ code coverage
- [ ] All agent behaviors have explicit tests
- [ ] Golden output tests catch breaking changes
- [ ] Chaos tests verify resilience claims
- [ ] Performance benchmarks tracked in CI

## Technical Notes

- Use `pytest-asyncio` for async tests
- Use `pytest-benchmark` for performance
- Consider `hypothesis` for property-based testing
