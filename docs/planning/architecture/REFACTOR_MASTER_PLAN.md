# Architectural Refactor & Technology Integration Master Plan

## 1. Critique of Current Structure

> **Note**: This plan is part of **Stream A** in the [Master Implementation Plan](../MASTER_IMPLEMENTATION_PLAN.md).

### Issues Identified

1.  **`src/core` Overload**: The `src/core` directory has become a "dumping ground" with 32+ subdirectories. It mixes true infrastructure (logging, config) with domain logic (research, quant, strategies) and feature implementations (browser, indexing).
2.  **Monolithic Files**: `src/graph/graph_builder.py` is ~2000 lines long, containing multiple distinct responsibilities (Metrics, Circuit Breaker, Graph Backend, Visualization) that should be separate components.
3.  **Ambiguous Boundaries**:
    - `src/core/browser` vs `src/tools/browser`: Unclear distinction between core browser logic and browser tools.
    - `src/core/agents` vs `src/agents`: Potential duplication or confusion in agent definitions.
4.  **Flat `src` Root**: While `src` has some organization, the top-level folders don't clearly separate "Domain" (Business Logic) from "Infrastructure" (Tech Stack).

## 2. Proposed New Folder Structure

We will move towards a **Domain-Driven Design (DDD)** inspired structure, separating **Core** (Infra), **Domain** (Business Logic), and **Interface** (API/CLI).

```text
src/
├── core/                   # Pure Infrastructure & Utilities (No Business Logic)
│   ├── config/
│   ├── logging/
│   ├── exceptions/
│   ├── di/                 # Dependency Injection
│   └── types/              # Base types/interfaces
├── domain/                 # Business Logic & Entities
│   ├── research/           # Research domain logic
│   ├── quant/              # Quantitative analysis domain
│   ├── strategies/         # Trading/Analysis strategies
│   └── models/             # Shared domain models
├── infrastructure/         # External Integrations (The "How")
│   ├── ai/                 # LangChain, LLM Providers
│   ├── browser/            # Browserbase, Playwright
│   ├── database/           # LanceDB, Postgres, Redis
│   ├── scraping/           # Scrapegraph, Crawl4AI
│   └── temporal/           # Temporal.io workflows
├── graph/                  # Orchestration Logic
│   ├── framework/          # The reusable graph engine (CircuitBreaker, Metrics)
│   └── workflows/          # Specific graph definitions (ResearchGraph)
├── tools/                  # High-level tools exposed to Agents
│   ├── financial/
│   ├── search/
│   └── ...
├── agents/                 # Agent Definitions
├── api/                    # FastAPI endpoints
└── cli/                    # CLI commands
```

## 3. Implementation Plan

### Phase 1: Structural Migration (Moving Folders)

- **Goal**: Clean up `src/core` and establish `src/domain` and `src/infrastructure`.
- **Steps**:
  1.  Create `src/domain` and `src/infrastructure`.
  2.  Move `src/core/research` -> `src/domain/research`.
  3.  Move `src/core/quant` -> `src/domain/quant`.
  4.  Move `src/core/strategies` -> `src/domain/strategies`.
  5.  Move `src/core/ai` -> `src/infrastructure/ai`.
  6.  Move `src/core/persistence` -> `src/infrastructure/database`.
  7.  Consolidate `src/core/browser` into `src/infrastructure/browser`.

### Phase 2: File Decomposition (Breaking Monoliths)

- **Goal**: Refactor `src/graph/graph_builder.py` into smaller, focused modules.
- **Target Directory**: `src/graph/framework/`
- **New Files**:
  - `metrics.py`: `NodeMetrics`, `ExecutionMetrics`
  - `resilience.py`: `CircuitBreaker`, `CircuitState`
  - `queue.py`: `DeadLetterQueue`, `DeadLetterEntry`
  - `execution.py`: `ParallelNodeExecutor`, `with_timeout`, `with_retry`
  - `backend.py`: `GraphBackend`, `LangGraphBackend`
  - `visualization.py`: `GraphVisualization`
  - `subgraph.py`: `Subgraph`

### Phase 3: Technology Integration (Adding New Tech)

- **Goal**: Integrate the researched technologies into the new `src/infrastructure` layer.
- **Steps**:
  1.  **Browserbase**: Implement `src/infrastructure/browser/browserbase_client.py`.
  2.  **Scrapegraph**: Implement `src/infrastructure/scraping/smart_scraper.py`.
  3.  **LanceDB**: Implement `src/infrastructure/database/vector_store.py`.
  4.  **DSPy**: Implement `src/infrastructure/ai/prompt_optimizer.py`.
  5.  **Temporal**: Implement `src/infrastructure/temporal/client.py`.

## 4. Execution Order

1.  **Refactor Plan Approval**: Get user sign-off on this document.
2.  **Phase 2 (Decomposition)**: Start here because it's less risky than moving folders (imports stay relative or easy to fix).
3.  **Phase 1 (Migration)**: Move folders and fix imports globally.
4.  **Phase 3 (Integration)**: Add new capabilities one by one.
