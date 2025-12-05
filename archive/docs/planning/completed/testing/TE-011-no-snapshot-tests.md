# TE-011: No Snapshot Testing for Outputs

**Priority**: High
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Medium
**Completed**: 2025-11-28
**Resolution**: Created tests/snapshot/test_snapshots.py with snapshot tests for API schemas, graph states, configurations, report templates, and agent outputs. syrupy already in dependencies. Added snapshot_exclude_dynamic fixture.

## Description

The system generates complex outputs (markdown reports, JSON structures, research states) but has no snapshot tests to detect unexpected changes. Output format changes can go unnoticed.

## Current State

- No snapshot testing infrastructure
- Report templates not tested for output format
- JSON response structures not snapshot tested
- Graph state transitions not recorded

## Impact

- **Silent format changes**: Output changes go undetected
- **Broken integrations**: Downstream consumers affected
- **Regression blind spots**: Format issues not caught
- **Manual verification**: Each change requires visual inspection

## Proposed Solution

1. **Install pytest-snapshot or syrupy**:

   ```bash
   pip install syrupy
   ```

2. **Create report output snapshots**:

   ```python
   def test_financial_report_format(snapshot):
       """Verify financial report format matches snapshot."""
       report = generate_financial_report(sample_data)
       assert report == snapshot

   def test_market_report_format(snapshot):
       """Verify market report format matches snapshot."""
       report = generate_market_report(sample_data)
       assert report == snapshot
   ```

3. **Create API response snapshots**:

   ```python
   def test_research_status_response(snapshot, api_client):
       """Verify status response format matches snapshot."""
       response = api_client.get("/api/v1/research/test-id/status")
       # Exclude dynamic fields
       data = response.json()
       data.pop("timestamp", None)
       data.pop("task_id", None)
       assert data == snapshot
   ```

4. **Create graph state snapshots**:

   ```python
   def test_initial_state_structure(snapshot):
       """Verify initial state structure matches snapshot."""
       state = ResearchState(company_name="Test", website="https://test.com")
       assert state.model_dump() == snapshot

   def test_state_after_financial_node(snapshot):
       """Verify state after financial node matches snapshot."""
       state = run_financial_node(initial_state)
       # Exclude variable data
       state_dict = state.model_dump()
       state_dict.pop("raw_data", None)
       assert state_dict == snapshot
   ```

5. **Handle dynamic content**:

   ```python
   from syrupy.filters import paths

   def test_report_with_dynamic_content(snapshot):
       """Snapshot test excluding dynamic fields."""
       report = generate_report(data)
       assert report == snapshot(exclude=paths("timestamp", "id", "date"))
   ```

## Acceptance Criteria

- [ ] Snapshot testing library installed (syrupy preferred)
- [ ] Snapshots for all report templates
- [ ] Snapshots for API responses
- [ ] Snapshots for graph state structures
- [ ] Dynamic content properly excluded
- [ ] Snapshot update process documented

## Snapshot Update Process

```bash
# Update all snapshots
pytest --snapshot-update

# Update specific snapshot
pytest tests/test_reports.py --snapshot-update
```

## Related Issues

- [TE-010](TE-010-no-contract-tests.md) - No API contract tests
- [TE-018](TE-018-no-regression-tests.md) - No regression test suite
