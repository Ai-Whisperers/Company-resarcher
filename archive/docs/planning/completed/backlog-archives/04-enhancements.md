# Enhancements Backlog Items

## Major Enhancement Suites

See detailed items in subdirectories:

- [PERF-001: Cost Optimization](./performance/PERF-001-cost-optimization.md) - Tiered models, caching, cost tracking
- [PERF-002: Speed & Latency](./performance/PERF-002-speed-latency.md) - Parallel execution, streaming
- [FEAT-010: Report Quality](./features/FEAT-010-report-quality.md) - Quality scoring, validation
- [IMPROVEMENT-ROADMAP](./IMPROVEMENT-ROADMAP.md) - Phased implementation plan

---

### [ENH] Improve URL Extraction Regex

**Priority:** Low
**Description:** The regex in `process_research_results` is complex.
**Acceptance Criteria:**

- [ ] Replace custom regex with a robust library (e.g., `validators` or `urllib`).
- [ ] Add tests for various URL formats.

**Technical Notes:**
- File: `src/agents/deep_research.py`

### [ENH] Structured Logging

**Priority:** Medium
**Status:** Partially Complete (see ARCH-004)
**Description:** Replace text logs with JSON logs for better observability.
**Acceptance Criteria:**

- [x] Configure JSON formatter (`StructuredJSONFormatter`)
- [x] Include `request_id` in all logs
- [ ] Add `trace_id`, `span_id` for distributed tracing (see OPS-001)

**Technical Notes:**
- File: `src/core/logger.py`
- See: `operations/OPS-001-observability.md` for full observability suite

### [ENH] Dynamic Concurrency Control

**Priority:** Medium
**Description:** Allow dynamic adjustment of concurrency based on system load/rate limits.
**Acceptance Criteria:**

- [ ] Implement a `ConcurrencyManager`.
- [ ] Monitor rate limit headers.
- [ ] Adjust `semaphore` size dynamically.

**Technical Notes:**
- Related to: `performance/PERF-002-speed-latency.md`
