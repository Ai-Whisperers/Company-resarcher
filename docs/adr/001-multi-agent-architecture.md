# ADR-001: Multi-Agent Research Architecture

## Status

Accepted

## Context

Company research requires gathering information from multiple domains (market, financial, competitor, brand, sales) which have different:
- Data sources and search strategies
- Analysis techniques and prompts
- Output formats and structures

We needed to decide between:
1. **Monolithic approach:** Single large prompt handling all domains
2. **Multi-agent approach:** Specialized agents for each domain
3. **LangGraph workflow:** State machine with nodes for each stage

## Decision

We chose a **multi-agent architecture with LangGraph orchestration**:

1. **Specialized Agents:** Each domain has a dedicated agent (`MarketAnalyst`, `FinancialAnalyst`, etc.) that:
   - Uses domain-specific search queries
   - Has tailored prompts for analysis
   - Produces structured output for its domain

2. **Pipeline Orchestration:** A `PipelineOrchestrator` coordinates agent execution:
   - Supports parallel or sequential execution
   - Manages timeouts and error handling
   - Aggregates results from all agents

3. **Shared Tools:** Agents share common tools (search, browser) through dependency injection:
   - Reduces resource usage
   - Enables consistent rate limiting
   - Simplifies testing with mocks

## Consequences

### Positive

- **Modularity:** Easy to add/modify/remove research domains
- **Specialization:** Each agent can be optimized for its domain
- **Parallelism:** Agents can run concurrently for faster research
- **Testability:** Agents can be tested in isolation
- **Maintainability:** Changes to one domain don't affect others

### Negative

- **Complexity:** More moving parts than a monolithic approach
- **Coordination:** Need careful orchestration for parallel execution
- **Consistency:** Must ensure agents use consistent company context

### Neutral

- LangGraph provides state management but adds a dependency
- Agent communication is one-way (orchestrator to agents)

## References

- `src/agents/base_agent.py` - Base agent class
- `src/pipeline/orchestrator.py` - Pipeline orchestration
- `src/pipeline/research_pipeline.py` - Stage execution
