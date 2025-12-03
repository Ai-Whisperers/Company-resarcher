# Refactoring Plan Overview

## Executive Summary

This document outlines a comprehensive refactoring plan for the `src/` directory (246 files, ~88,000 LOC) to address:

- **Rate Limiter Fragmentation** - 3 incompatible systems
- **Configuration duplication** - 2 overlapping config files + 182 direct env reads
- **HTTP Client Duplication** - No unified client, duplicated 4x
- **AIClientManager God Object** - ~1000 LOC handling 7 responsibilities
- **AI Client Wrapper Soup** - 3 wrappers with no common base
- **Caching Scattered** - 5+ different cache implementations
- **Exception Handling** - 244 bare `except Exception:` blocks
- **Singleton overuse** - 134+ usages
- **Manager class ambiguity** - 35+ classes
- **Large monolithic files** - 10+ files over 900 lines

## Roadmap & Priority Order

### 🔴 CRITICAL - Immediate (Sprint 1-2)

1. **Rate Limiter Consolidation** (8h) - Prevents configuration drift
2. **Config Consolidation** (4h) - Single source of truth
3. **HTTP Client Abstraction** (6h) - DRY, unified retry/timeout

### 🟠 HIGH - Soon (Sprint 3-4)

4. **AIClientManager Split** (12h) - Maintainability
5. **Cache Interface Unification** (6h) - Consistent caching API
6. **Exception Handling Cleanup** (8h) - Better debugging
7. **DelegatingAIClient Base** (4h) - Composable wrappers

### 🟡 MEDIUM - Scheduled (Sprint 5-6)

8. **Logger Cleanup** (2h) - Consistency
9. **Provider Error Detection** (3h) - Unified error handling
10. **Magic Numbers → Config** (2h) - Configurability
11. **Service Standardization** (4h) - DI pattern

### 🟢 LOWER - Future (Sprint 7+)

12. **Singleton → DI Container** (6h)
13. **Provider Registry** (3h)
14. **File I/O Patterns** (4h)

## Risk Mitigation

### Risk 1: Breaking Changes

- **Mitigation:** Maintain backward compatibility during transition
- **Strategy:** Create adapters for old APIs

### Risk 2: Regression Bugs

- **Mitigation:** Comprehensive test suite before migration
- **Strategy:** Run tests after each change

### Risk 3: Timeline Slippage

- **Mitigation:** Prioritize high-impact changes
- **Strategy:** Deliver in incremental phases

### Risk 4: Knowledge Loss

- **Mitigation:** Document architecture decisions
- **Strategy:** Create architecture decision records (ADRs)
