# Architecture & Refactoring Backlog Items

### [ARCH] Implement Dependency Injection Container

**Priority:** High
**Description:** Currently, classes are manually instantiated and passed around (e.g., in `main.py`). This makes testing and swapping implementations difficult.
**Acceptance Criteria:**

- [ ] Introduce a DI container (e.g., `dependency_injector` or simple registry).
- [ ] Register core services (`AIClient`, `SearchTool`, `BrowserTool`).
- [ ] Refactor `main.py` to resolve dependencies from the container.
      **Technical Notes:**
- This will simplify `run_comprehensive_research` signature.

### [ARCH] Refactor DeepResearchAgent State Management

**Priority:** High
**Description:** `DeepResearchAgent.deep_research` passes `learnings`, `citations`, `visited_urls`, etc., recursively. This is messy.
**Acceptance Criteria:**

- [ ] Create a `ResearchState` dataclass to hold all research context.
- [ ] Refactor `deep_research` to accept and return `ResearchState`.
- [ ] Consider using `LangGraph` state management if applicable.
      **Technical Notes:**
- File: `src/agents/deep_research.py`

### [ARCH] Extract Prompts to External Files

**Priority:** Medium
**Description:** Prompts are hardcoded in Python files (e.g., `deep_research.py`). They should be managed separately to allow for easy updates and versioning.
**Acceptance Criteria:**

- [ ] Create `src/prompts/` directory structure.
- [ ] Move prompts from `deep_research.py` to YAML/Text files.
- [ ] Implement a `PromptManager` to load prompts.
      **Technical Notes:**
- Use Jinja2 for prompt templating.

### [ARCH] Standardize Configuration Management

**Priority:** Medium
**Description:** Config is split between `.env`, `argparse`, and `config.py`. We need a unified source of truth.
**Acceptance Criteria:**

- [ ] Move all CLI args to override `Settings` values.
- [ ] Ensure `Settings` (Pydantic) is the single source of truth.
- [ ] Remove direct `os.getenv` calls in code (use `settings.xxx`).
      **Technical Notes:**
- File: `src/core/config.py`

### [ARCH] Decouple GraphBuilder from LangGraph

**Priority:** Medium
**Description:** `GraphBuilder` has a `LangGraphBackend`. We should ensure the abstraction is leaky-proof so we can swap backends if needed.
**Acceptance Criteria:**

- [ ] Review `GraphBackend` interface.
- [ ] Ensure no `langgraph` imports exist outside `LangGraphBackend`.
      **Technical Notes:**
- File: `src/graph/graph_builder.py`
