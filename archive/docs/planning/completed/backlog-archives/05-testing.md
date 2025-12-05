# Testing & QA Backlog Items

### [TEST] Add Unit Tests for OutputManager

**Priority:** High
**Description:** `OutputManager` is critical for security and data integrity.
**Acceptance Criteria:**

- [ ] Test `save_research_output` with valid inputs.
- [ ] Test `_validate_path` with traversal attempts (`../`).
- [ ] Test `_sanitize_filename` with special chars.

### [TEST] Add Mock Tests for SearchTool

**Priority:** Medium
**Description:** Test search fallback logic without making real API calls.
**Acceptance Criteria:**

- [ ] Mock `SearchManager`.
- [ ] Simulate provider failures.
- [ ] Verify fallback order (DDG -> Jina -> Serper -> Tavily).

### [TEST] Integration Test for Full Pipeline

**Priority:** High
**Description:** Run a full research cycle with mocked agents to verify wiring.
**Acceptance Criteria:**

- [ ] Mock `AIClient` to return predictable responses.
- [ ] Run `PipelineOrchestrator`.
- [ ] Verify output files are created.

### [TEST] Chaos Testing

**Priority:** Low
**Description:** Simulate network failures to test resilience.
**Acceptance Criteria:**

- [ ] Create a `ChaosNetworkProxy`.
- [ ] Run research with 10%, 30%, 50% packet loss simulation.
- [ ] Verify system recovers or fails gracefully.
