# Codebase Critique & Review

**Date**: 2025-11-26
**Scope**: `src/` directory (Agents, Core, Graph, API)

## 🚨 Critical Issues (Must Fix)

### 1. Code Duplication in Specialists

**File**: `src/agents/specialists.py`
**Problem**: The `research` method in `FinancialAgent`, `MarketAnalyst`, `BrandAuditor`, `CompetitorScout`, and `SalesAgent` is nearly identical. They all follow the pattern:

1.  Define queries.
2.  `_gather_data`.
3.  Build context string.
4.  Construct prompt.
5.  Call AI with `response_format="json"`.
6.  Parse JSON.
7.  Render Markdown.
8.  Return `ResearchPhaseResult`.

**Bad Practice**: Violates DRY (Don't Repeat Yourself). If we want to change how we handle JSON errors or context building, we have to change it in 5 places.
**Recommendation**: Refactor `BaseAgent` to include a `execute_research_cycle` method that takes `queries`, `prompt_template`, and `output_template` as arguments.

### 2. Hardcoded Prompts

**File**: `src/agents/specialists.py`
**Problem**: Large multi-line f-string prompts are embedded in the code.
**Bad Practice**: Hard to read, hard to test, and hard to modify without touching logic.
**Recommendation**: Move prompts to `src/prompts/` (e.g., as text or Jinja2 files) and load them. This allows non-coders to tweak prompts.

### 3. In-Memory State for API

**File**: `src/api/app.py`
**Problem**: `TASKS = {}` is a global dictionary.
**Bad Practice**: Data is lost on server restart. Not scalable across multiple workers (e.g., if using Gunicorn with multiple workers, they won't share state).
**Recommendation**: Use Redis or a simple SQLite database for task persistence.

## ⚠️ Improvements (Should Fix)

### 4. Dependency Injection in Graph

**File**: `src/graph/graph_builder.py`
**Problem**: Agents are instantiated inside the node functions (e.g., `agent = FinancialAgent()`).
**Bad Practice**: Makes unit testing difficult because you cannot mock the agent instance easily.
**Recommendation**: Pass agent instances via the `ResearchState` or use a Dependency Injection container/factory pattern.

### 5. Magic Strings

**Files**: Various
**Problem**: Strings like `"Unknown"`, `"USA"`, `"gpt-4-turbo-preview"` are hardcoded.
**Bad Practice**: Prone to typos and hard to update globally.
**Recommendation**: Define these in `src/core/constants.py`.

### 6. Broad Exception Handling

**File**: `src/agents/specialists.py`
**Problem**: `except Exception as e:` catches everything.
**Bad Practice**: Can mask `KeyboardInterrupt` or system errors that should crash the app.
**Recommendation**: Catch specific exceptions (`AIProviderError`, `JSONDecodeError`) or at least log the stack trace.

## 💡 Architectural Observations

### Good Practices

- **LangGraph**: The graph topology is clean and leverages parallel execution well.
- **Pydantic**: Strong typing for configuration and state management.
- **Async**: Fully asynchronous I/O handling.
- **Logging**: Consistent usage of `setup_logger`.

### Refactoring Plan

1.  **Extract Prompts**: Move all prompts to `src/prompts/*.txt`.
2.  **Refactor BaseAgent**: Create a generic research method.
3.  **Database**: Add SQLite support for the API.
