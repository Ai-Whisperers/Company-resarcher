# Bugs and Issues Backlog

This folder contains identified bugs, issues, and problems in the Company Researcher codebase.

## Summary

| # | Severity | Issue | File |
|---|----------|-------|------|
| 01 | 🔴 Critical | Broken API Endpoint - Missing Decorator | `src/api/app.py` |
| 02 | 🔴 Critical | Missing `run_research_task` Function | `src/api/app.py` |
| 03 | 🔴 Critical | Singleton Orchestrator Startup Crash | `src/agents/orchestrator.py` |
| 04 | 🔴 Critical | Thread Safety Issues in Singletons | `src/tools/__init__.py` |
| 05 | 🟠 High | Async Functions Without Await | `src/core/ai_client.py` |
| 06 | 🟠 High | Deprecated `asyncio.get_event_loop()` | `src/tools/search.py` |
| 07 | 🟠 High | Browser Resource Leak | `src/tools/browser.py` |
| 08 | 🟠 High | Settings Not Cached | `src/core/config.py` |
| 09 | 🟠 High | SEC Tool Uses Ticker, Not Company Name | `src/agents/specialists.py` |
| 10 | 🟡 Medium | Hardcoded Date in main.py | `main.py` |
| 11 | 🟡 Medium | Python Version Incompatible Type Hint | `src/tools/browser.py` |
| 12 | 🟡 Medium | fetch_multiple Creates Duplicate ResearchSource | `src/tools/browser.py` |
| 13 | 🟡 Medium | No Input Validation on Research Request | `src/api/models.py` |
| 14 | 🟡 Medium | Database Session Not Used in Background Task | `src/api/app.py` |
| 15 | 🟡 Medium | Exception Handling Swallows All Errors | Multiple files |
| 16 | 🟡 Medium | Unsafe JSON Parsing for Database | `src/api/app.py` |
| 17 | 🔵 Low | Print Statements Instead of Logger | `src/graph/graph_builder.py` |
| 18 | 🔵 Low | Unused Tools in Specialists | `src/agents/specialists.py` |
| 19 | 🔵 Low | Inconsistent Error Types | `src/core/ai_client.py` |
| 20 | 🔵 Low | No Graceful Degradation for Missing Tools | `src/agents/factory.py` |
| 21 | 🔵 Low | State Model Uses Pydantic v1 Style Config | `src/graph/state.py` |
| 22 | 🔵 Low | Outdated Model Names | `src/core/config.py` |
| 23 | 🔵 Low | No Rate Limiting on Parallel Fetches | `src/tools/browser.py` |

## Priority

### Must Fix (Blocking)
- Issues 01-04: Critical bugs that prevent the system from working

### Should Fix (Important)
- Issues 05-09: High severity issues affecting performance and reliability

### Nice to Fix (Quality)
- Issues 10-16: Medium severity issues affecting robustness
- Issues 17-23: Low severity issues affecting code quality

## How to Use

Each file contains:
1. Problem description
2. Code location
3. Impact assessment
4. Proposed solution
5. Testing instructions

Pick an issue, implement the solution, and create a PR referencing the issue number.
