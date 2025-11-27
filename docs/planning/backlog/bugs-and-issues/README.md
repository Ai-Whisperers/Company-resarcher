# Bugs and Issues Backlog V2

This folder contains 106 identified bugs, issues, and problems in the Company Researcher codebase.

## Summary by Severity

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 5 | Security vulnerabilities, crashes, data loss |
| 🟠 High | 15 | Major bugs, resource leaks, security risks |
| 🟡 Medium | 50 | Moderate issues, code quality, performance |
| 🔵 Low | 36 | Minor issues, documentation, testing gaps |
| **Total** | **106** | |

## Critical Issues (Fix First!)

| # | Issue | File |
|---|-------|------|
| 001 | Pickle Deserialization Vulnerability | `src/core/cache.py` |
| 002 | Uninitialized Variable in Exception Handler | `src/agents/generic_agent.py` |
| 003 | Race Condition in Cache Initialization | `src/core/cache.py` |
| 004 | Path Traversal in Output Manager | `src/core/output_manager.py` |
| 005 | API Key Exposure in Factory | `src/agents/factory.py` |

## High Priority Issues

| # | Issue | File |
|---|-------|------|
| 006 | Type Error - Wrong Attribute Name | `src/agents/writer.py` |
| 007 | None.strip() Error | `src/tools/search.py` |
| 008 | Swallowed Exception in Browser | `src/tools/browser.py` |
| 009 | Circular Import Risk | `src/agents/orchestrator.py` |
| 010 | Hardcoded Constants | `src/core/constants.py` |
| 011 | Blocking OllamaClient | `src/core/ai_client.py` |
| 012 | No File Timeout in Vault | `src/core/vault.py` |
| 013 | Path Traversal in Logger | `src/core/logger.py` |
| 014 | No API Rate Limiting | `src/api/app.py` |
| 015 | Missing CORS Configuration | `src/api/app.py` |
| 016 | No Request Size Limit | `src/api/app.py` |
| 017 | Global AI Manager Race Condition | `src/core/ai_client.py` |
| 018 | Semaphore Initialization Race | `src/tools/browser.py` |
| 019 | No Background Task Timeout | `src/api/app.py` |
| 020 | Browser Page Resource Leak | `src/tools/browser.py` |

## Medium Priority Issues (021-070)

Issues related to:
- Error handling improvements
- Code quality and duplication
- Performance optimizations
- Configuration management
- Memory management
- Observability and logging
- API design consistency

## Low Priority Issues (071-106)

Issues related to:
- Type safety improvements
- Documentation gaps
- Testing coverage
- Code style consistency
- Dependency management
- Feature enhancements

## Categories

| Category | Count |
|----------|-------|
| Security | 12 |
| Error Handling | 15 |
| Concurrency | 6 |
| Performance | 10 |
| Configuration | 10 |
| Type Safety | 8 |
| Code Quality | 12 |
| Testing | 5 |
| Documentation | 5 |
| API Design | 5 |
| Memory Management | 5 |
| Observability | 4 |
| Operations | 4 |
| Async | 3 |
| Reliability | 2 |

## How to Use

1. Start with Critical issues (001-005)
2. Move to High priority (006-020)
3. Address Medium as time allows (021-070)
4. Low priority for cleanup sprints (071-106)

Each file contains:
- Issue number and severity
- Category
- File location
- Problem description
- Solution suggestion

## Quick Fix Commands

```bash
# List all critical issues
ls backlog/bugs-and-issues-v2/0{01,02,03,04,05}*.md

# List all high priority
ls backlog/bugs-and-issues-v2/0{06,07,08,09,10,11,12,13,14,15,16,17,18,19,20}*.md

# Count issues by severity
ls backlog/bugs-and-issues-v2/*.md | wc -l
```

## Progress Tracking

Move completed issues to `completed/` subfolder:
```bash
mkdir -p backlog/bugs-and-issues-v2/completed
mv backlog/bugs-and-issues-v2/001-*.md backlog/bugs-and-issues-v2/completed/
```
