# linkedin-content-system

**Description:** 
**URL:** https://github.com/Ai-Whisperers/linkedin-content-system
**Visibility:** PRIVATE

---

# AI-Whisperers Content Generator - Technical Documentation

## Overview

This directory contains technical documentation for the AI-Whisperers Content Generator system. For user-facing guides, see the `/guides` directory.

## Documentation Structure

### Implementation Documentation
Technical architecture and design specifications.

- **[WORKFLOW_DESIGN.md](./implementation/WORKFLOW_DESIGN.md)** - Corrected workflow architecture with error handling
- Architecture overview and design decisions
- MCP server integration details
- API integration specifications

**Location:** `docs/implementation/`

---

### Error Handling Documentation
Non-happy path scenarios, error recovery, and resilience patterns.

- **[ERROR_CATALOG.md](./error-handling/ERROR_CATALOG.md)** - Comprehensive catalog of all possible errors
- **[FAILURE_SCENARIOS.md](./error-handling/FAILURE_SCENARIOS.md)** - Non-happy path flows and edge cases
- **[RETRY_STRATEGIES.md](./error-handling/RETRY_STRATEGIES.md)** - Retry logic, backoff policies, and resilience
- **[RECOVERY_PROCEDURES.md](./error-handling/RECOVERY_PROCEDURES.md)** - Step-by-step recovery from failures

**Location:** `docs/error-handling/`

---

### Testing Documentation
Testing strategies, test plans, and quality assurance procedures.

- **[TEST_PLAN.md](./testing/TEST_PLAN.md)** - Comprehensive testing strategy
- **[INTEGRATION_TESTS.md](./testing/INTEGRATION_TESTS.md)** - Integration testing guide
- **[E2E_TESTS.md](./testing/E2E_TESTS.md)** - End-to-end testing scenarios

**Location:** `docs/testing/`

---

### Operations Documentation
Operational procedures, monitoring, and troubleshooting.

- **[RUNBOOKS.md](./operations/RUNBOOKS.md)** - Operational runbooks with step-by-step procedures
- **[TROUBLESHOOTING.md](./operations/TROUBLESHOOTING.md)** - Diagnostic procedures and issue resolution

**Location:** `docs/operations/`

---

## Critical Flaws Addressed

This documentation addresses 6 critical flaws identified in the content generator workflow:

| Flaw | Description | Documentation |
|------|-------------|---------------|
| **#1** | Double Trigger Race Condition | [FAILURE_SCENARIOS.md](./error-handling/FAILURE_SCENARIOS.md#race-condition) |
| **#2** | Context Validation Timing | [FAILURE_SCENARIOS.md](./error-handling/FAILURE_SCENARIOS.md#context-validation) |
| **#3** | Monolithic Read+Normalize+Validate | [WORKFLOW_DESIGN.md](./implementation/WORKFLOW_DESIGN.md#separation-of-concerns) |
| **#4** | Claude API Resilience | [RETRY_STRATEGIES.md](./error-handling/RETRY_STRATEGIES.md#api-resilience) |
| **#5** | Status Branching Logic | [WORKFLOW_DESIGN.md](./implementation/WORKFLOW_DESIGN.md#validation-contract) |
| **#6** | Version Tagging Implementation | [WORKFLOW_DESIGN.md](./implementation/WORKFLOW_DESIGN.md#version-management) |

---

## Quick Navigation

### For Developers
- Setting up the development environment → `/guides/01-GETTING_STARTED.md`
- Understanding the workflow architecture → [WORKFLOW_DESIGN.md](./implementation/WORKFLOW_DESIGN.md)
- Writing tests → [TEST_PLAN.md](./testing/TEST_PLAN.md)
- Handling errors → [ERROR_CATALOG.md](./error-handling/ERROR_CATALOG.md)

### For DevOps/Operations
- Running the generator → `/guides/03-RUNNING_GENERATOR.md`
- Operational procedures → [RUNBOOKS.md](./operations/RUNBOOKS.md)
- Troubleshooting issues → [TROUBLESHOOTING.md](./operations/TROUBLESHOOTING.md)
- Recovery from failures → [RECOVERY_PROCEDURES.md](./error-handling/RECOVERY_PROCEDURES.md)

### For QA
- Test planning → [TEST_PLAN.md](./testing/TEST_PLAN.md)
- Integration testing → [INTEGRATION_TESTS.md](./testing/INTEGRATION_TESTS.md)
- End-to-end testing → [E2E_TESTS.md](./testing/E2E_TESTS.md)
- Quality metrics → `/brand-docs/QUALITY_CHECKLIST.md`

---

## Related Documentation

- **User Guides:** `/guides/` - Step-by-step guides for using the system
- **Brand Documentation:** `/brand-docs/` - Brand standards and quality checklists
- **Reference Materials:** `/reference/` - Strategy documents and reference lists
- **Context Documentation:** `/context/README.md` - Context collection and management

---

## Contributing

When adding new documentation:

1. **Implementation details** → `docs/implementation/`
2. **Error handling & resilience** → `docs/error-handling/`
3. **Testing procedures** → `docs/testing/`
4. **Operational procedures** → `docs/operations/`
5. **User-facing guides** → `/guides/`

Ensure all new documents are linked in this README for discoverability.

---

## Version

Documentation Version: **2.0.0**
Last Updated: **2025-11-10**
Workflow Version: **2.0.0**
