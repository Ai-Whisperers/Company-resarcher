# Implementation Roadmap

This roadmap defines the step-by-step execution plan to build the full system.

## Phase 1: Core Foundation (The MVP)

**Goal**: A CLI tool that runs the 4-Wave cycle for a single company using LangGraph.

- [x] **Architecture**: Define `ResearchState` and Graph Topology.
- [x] **Orchestrator**: Implement LangGraph runtime.
- [x] **Agents**: Implement logic for `Financial`, `Market`, `Sales`, `Insight`, `Writer`.
- [x] **Tools**: Connect `BrowserTool` and `Tavily` to agents.
- [ ] **Sector Analyst**: Agent to aggregate data from the Vault.
- [ ] **B2B Sales**: Implement Product Matching logic (RAG).
- [ ] **Investment Analysis**: Implement Due Diligence Checklist agents.

## Phase 4: Experience & Collaboration

**Goal**: A user-friendly interface for teams.

- [ ] **Web UI**: React/Next.js Dashboard.
- [ ] **Collaborative Mode**: Human-in-the-loop approval queue.
- [ ] **Multi-Modal**: Video/Audio analysis of interviews.
- [ ] **API**: Expose the system as a REST API (FastAPI).

---

## Immediate Next Steps (Actionable)

1.  **Complete Phase 1**:
    - Flesh out `src/agents/specialists.py` with real logic (currently skeletons).
    - Implement `src/agents/insight_generator.py`.
    - Implement `src/agents/writer.py`.
2.  **Verify**: Run `main.py` against a complex company (e.g., Nvidia) and check report quality.
