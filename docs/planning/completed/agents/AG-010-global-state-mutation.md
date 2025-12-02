# AG-010: Global State Mutation

## Status: MITIGATED

> **Resolution**: The primary global state concern has been addressed:
>
> 1. **`_orchestrator` singleton** (AG-001): Now protected with thread-safe double-checked locking via `threading.Lock()` in `orchestrator.py`
>
> 2. **Global AI manager fallback**: The "global manager" pattern is intentional dependency injection with fallbacks - agents accept an optional `client` parameter and only fall back to the global manager if none is provided. This is a standard DI pattern, not problematic global state mutation.
>
> 3. **No mutable global state in specialists**: `specialists.py` and `factory.py` do not have mutable global variables - they only have module-level constants and class definitions.
>
> The codebase already uses dependency injection via `AgentFactory` which allows passing custom clients for testing and isolation.
>
> **Fixed in**: `src/agents/orchestrator.py` (thread-safe singleton)
> **Date**: 2024-11-28
> **Related**: AG-001

---

## Original Description (for reference)

## Priority: High

## Description

Global variables are mutated during runtime, causing unpredictable behavior in concurrent environments.

## Location

- **File**: `src/agents/orchestrator.py` (singleton - now thread-safe)
- **File**: `src/agents/factory.py` (no global state, uses DI)

## Implemented Mitigations

- Thread-safe singleton with `threading.Lock()` and double-checked locking
- Dependency injection via `AgentFactory` for testability
- `reset_orchestrator()` function for test isolation

## Impact

- **Severity**: High
- **Risk**: Race conditions, debugging difficulty
