# Architecture & Refactoring Backlog Items

## Resolved Items

### ~~[ARCH] Implement Dependency Injection Container~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/architecture/ARCH-001-dependency-injection.md`
> **Implementation:** `src/core/container.py` (440 lines, thread-safe, lifecycle support)

### ~~[ARCH] Refactor DeepResearchAgent State Management~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/architecture/ARCH-002-state-management.md`
> **Implementation:** `src/graph/state.py` (ResearchState with bounds, checkpointing, validation)

### ~~[ARCH] Extract Prompts to External Files~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/architecture/ARCH-003-external-prompts.md`
> **Implementation:** `src/prompts/` directory (6 prompt files with Jinja2 templating)

## Remaining Items

### ~~[ARCH] Standardize Configuration Management~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/architecture/ARCH-config-standardization.md`
> **Implementation:** `src/core/config.py` - Added `CLIConfig` and `apply_cli_overrides()`

### ~~[ARCH] Decouple GraphBuilder from LangGraph~~ [RESOLVED]

> **Moved to:** `docs/planning/resolved/architecture/ARCH-004-graphbuilder-decoupling.md`
> **Implementation:** `src/graph/graph_builder.py` (local imports, GraphBackend abstraction)
