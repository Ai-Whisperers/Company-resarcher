# Refactoring & Improvement Plan

**Status**: Planned
**Based on**: `CRITIQUE.md` and `CRITIQUE_PATTERNS.md`

This plan outlines the steps to address the critical issues and improvements identified in the codebase and documentation reviews.

## 🛠️ Part 1: Codebase Refactoring

### 1.1 Extract Prompts

**Goal**: Move hardcoded prompts from Python code to external files for better maintainability.

- [ ] Create `src/prompts/` directory.
- [ ] Extract prompts from `src/agents/specialists.py` into individual text files (e.g., `financial_analysis.txt`).
- [ ] Update `BaseAgent` to load prompts from files.

### 1.2 Refactor Specialists (DRY)

**Goal**: Remove code duplication in specialist agents.

- [ ] Implement `execute_research_cycle` in `BaseAgent`.
- [ ] Update `FinancialAgent`, `MarketAnalyst`, `BrandAuditor`, `CompetitorScout`, and `SalesAgent` to use this new method.

### 1.3 API Persistence

**Goal**: Replace in-memory `TASKS` dictionary with a persistent store.

- [ ] Add `sqlite3` support to `src/api/app.py`.
- [ ] Create a simple `Task` table to store task status and results.

### 1.4 Dependency Injection

**Goal**: Decouple agent instantiation from graph logic.

- [ ] Create an `AgentFactory` or pass agent instances to `build_graph`.
- [ ] Update `src/graph/graph_builder.py` to use injected agents.

### 1.5 Centralize Constants

**Goal**: Remove magic strings.

- [ ] Create `src/core/constants.py`.
- [ ] Move strings like "Unknown", "USA", model names, etc., to constants.

## 📚 Part 2: Documentation Improvements

### 2.1 Expand Core Patterns

**Goal**: Bring Core patterns (1-7) to the same depth as Advanced patterns.

- [ ] Update `01-prompt-chaining.md` with "Edge Cases" and "Common Pitfalls".
- [ ] Update `02-routing.md`, `03-parallelization.md`, etc.

### 2.2 Add Testing Strategies

**Goal**: Provide guidance on testing agentic patterns.

- [ ] Add `## 🧪 Testing Strategy` section to all 21 pattern files.
- [ ] Include specific techniques (mocking, golden datasets, eval metrics).

### 2.3 Runnable Examples

**Goal**: Provide copy-pasteable, working code.

- [ ] Create `docs/ai-design-patterns/examples/` directory.
- [ ] Create a runnable Python script for each pattern (e.g., `01_prompt_chaining.py`).
- [ ] Link examples in the documentation.

### 2.4 Visualizations

**Goal**: Professionalize diagrams.

- [ ] Convert ASCII art in `21-exploration-discovery.md` and others to Mermaid.js.

## 📅 Execution Order

1.  **Codebase Refactoring**: Prioritize 1.1 and 1.2 (High Impact on Maintainability).
2.  **API Persistence**: 1.3 (Critical for Reliability).
3.  **Documentation**: 2.1 and 2.2 (High Value for Users).
4.  **Polish**: 1.4, 1.5, 2.3, 2.4 (Nice to have).
