# Phase 1: Folder Structure Migration Plan

## Goal

Transition from the flat, overloaded `src/core` structure to a Domain-Driven Design (DDD) layout.

## 1. New Directory Creation

We will create these top-level directories first:

```bash
mkdir -p src/domain
mkdir -p src/infrastructure
```

## 2. Migration Mapping (Old -> New)

### Domain Logic (Business Rules)

| Old Path                         | New Path                            | Description                  |
| :------------------------------- | :---------------------------------- | :--------------------------- |
| `src/core/research/`             | `src/domain/research/`              | Core research logic          |
| `src/core/quant/`                | `src/domain/quant/`                 | Quantitative analysis        |
| `src/core/strategies/`           | `src/domain/strategies/`            | Trading/Analysis strategies  |
| `src/core/models/`               | `src/domain/models/`                | Shared data models           |
| `src/core/company_classifier.py` | `src/domain/research/classifier.py` | Company classification logic |
| `src/core/company_probe.py`      | `src/domain/research/probe.py`      | Initial probing logic        |

### Infrastructure (External Integrations)

| Old Path                | New Path                       | Description               |
| :---------------------- | :----------------------------- | :------------------------ |
| `src/core/ai/`          | `src/infrastructure/ai/`       | LLM providers (LangChain) |
| `src/core/browser/`     | `src/infrastructure/browser/`  | Browser automation        |
| `src/core/persistence/` | `src/infrastructure/database/` | DB adapters               |
| `src/core/cache/`       | `src/infrastructure/cache/`    | Redis/Memory cache        |
| `src/core/network/`     | `src/infrastructure/network/`  | HTTP clients              |
| `src/core/sources/`     | `src/infrastructure/sources/`  | External API clients      |

### Core (Pure Utilities)

These remain in `src/core` but cleaned up:

- `config/`
- `logging/`
- `exceptions/`
- `di/`
- `types/`
- `resilience/` (Circuit breakers, etc.)

## 3. Execution Steps

1.  **Create Directories**: Run `mkdir` commands.
2.  **Move Files**: Use `git mv` to preserve history.
3.  **Fix Imports**:
    - Search for `from src.core.research` -> Replace with `from src.domain.research`
    - Search for `from src.core.ai` -> Replace with `from src.infrastructure.ai`
    - (And so on for each mapping)
4.  **Verify**: Run tests to ensure no `ModuleNotFoundError`.
