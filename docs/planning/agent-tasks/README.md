# Agent Task Distribution

This directory contains 4 focused TODO lists designed for parallel agent work on the Company Researcher backlog.

## Quick Overview

| Agent | Focus Area | Priority | Est. Files |
|-------|-----------|----------|------------|
| [Agent 1](./AGENT-1-core-infrastructure.md) | Core Infrastructure & Reliability | HIGH | 12-15 |
| [Agent 2](./AGENT-2-testing-quality.md) | Testing & Quality Assurance | HIGH | 15-20 |
| [Agent 3](./AGENT-3-security-observability.md) | Security & Observability | HIGH | 12-15 |
| [Agent 4](./AGENT-4-features-docs.md) | Features & Documentation | MEDIUM | 12-16 |

## Agent 1: Core Infrastructure & Reliability

**Key Deliverables:**
- Cost optimization (tiered model routing)
- Speed improvements (parallel execution, streaming)
- Reliability patterns (circuit breaker, retry strategies)
- Critical bug fixes (Unicode, rate limiting)

**Main Backlog Items:**
- PERF-001, PERF-002, ARCH-005, 01-critical.md

---

## Agent 2: Testing & Quality Assurance

**Key Deliverables:**
- Test coverage improvements (unit, integration, E2E)
- Report quality scoring system
- Validation frameworks
- Advanced testing (behavior, golden, chaos)

**Main Backlog Items:**
- TEST-001, FEAT-010, VAL-001 through VAL-006

---

## Agent 3: Security & Observability

**Key Deliverables:**
- Security hardening (prompt injection defense)
- Vault encryption
- OpenTelemetry integration
- Health checks and metrics

**Main Backlog Items:**
- SEC-010, SEC-006, OPS-001, FEAT-014

---

## Agent 4: Features & Documentation

**Key Deliverables:**
- API and architecture documentation
- Interactive research mode
- Progress reporting
- Tech debt cleanup (hardcoded values)

**Main Backlog Items:**
- DOC-001 through DOC-013, FEAT-001, FEAT-009, TECH-001 through TECH-016

---

## Dependency Graph

```
Agent 1 (Infrastructure)
    └── Provides: circuit_breaker.py, retry_strategy.py

Agent 2 (Testing)
    └── Depends on: Stable core infrastructure
    └── Provides: test coverage, quality scoring

Agent 3 (Security)
    └── Depends on: Logger improvements (Agent 1)
    └── Provides: security.py, telemetry.py

Agent 4 (Features)
    └── Depends on: Core stability (Agent 1)
    └── Can run mostly in parallel
```

## Recommended Execution Order

1. **Phase 1** (Can run in parallel):
   - Agent 1: Start with critical bugs and ARCH-005
   - Agent 3: Start with OPS-001 observability

2. **Phase 2** (After Phase 1 stabilizes):
   - Agent 2: Full testing implementation
   - Agent 4: Documentation and features

3. **Phase 3** (Final):
   - All agents: Integration testing and cleanup

## How to Use These Files

Each agent file contains:
- Specific tasks with subtasks
- Files to create/modify
- Code examples where applicable
- Acceptance criteria
- Getting started commands

### For Claude Code Agents:

```bash
# Agent 1
claude "Work on docs/planning/agent-tasks/AGENT-1-core-infrastructure.md"

# Agent 2
claude "Work on docs/planning/agent-tasks/AGENT-2-testing-quality.md"

# Agent 3
claude "Work on docs/planning/agent-tasks/AGENT-3-security-observability.md"

# Agent 4
claude "Work on docs/planning/agent-tasks/AGENT-4-features-docs.md"
```

## Progress Tracking

Update task checkboxes as work completes:
- `[ ]` = Not started
- `[x]` = Completed

## Related Documents

- [Full Backlog](../backlog/)
- [Improvement Roadmap](../backlog/IMPROVEMENT-ROADMAP.md)
- [Caching Guide](../../guides/CACHING.md)
