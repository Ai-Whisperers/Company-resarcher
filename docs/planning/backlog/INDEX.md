# Company Researcher - Implementation Backlog

This backlog contains detailed tickets for features, improvements, and learnings derived from analyzing external reference repositories.

## 🏗️ Major Refactoring Initiatives

| Initiative                                                                  | Description                                                                                         | Status         |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------- |
| [**Refactoring Plan**](refactor_plan/00_OVERVIEW.md)                        | Comprehensive plan to clean up technical debt, consolidate managers, and improve architecture.      | 🚧 In Progress |
| [**Post-Refactor Improvements**](post_refactor_improvements/00_OVERVIEW.md) | Roadmap for performance, DX, observability, and new features to be built on the clean architecture. | 📅 Planned     |

---

## Quick Stats

| Category       | Count | Priority High | Priority Medium | Priority Low |
| -------------- | ----- | ------------- | --------------- | ------------ |
| Features       | 12    | 5             | 5               | 2            |
| Improvements   | 10    | 4             | 4               | 2            |
| Integrations   | 8     | 3             | 3               | 2            |
| Technical Debt | 6     | 2             | 3               | 1            |
| Learning       | 5     | 1             | 3               | 1            |

**Total: 41 tickets**

---

## Priority Legend

- **P0 - Critical**: Blocks other work or major impact
- **P1 - High**: Significant value, should be done soon
- **P2 - Medium**: Good improvement, schedule when capacity allows
- **P3 - Low**: Nice to have, backlog for later

## Effort Estimates

- **XS**: < 2 hours
- **S**: 2-4 hours
- **M**: 1-2 days
- **L**: 3-5 days
- **XL**: 1-2 weeks

---

## Features (New Capabilities)

| ID                                                            | Title                                 | Priority | Effort | Source Repo             |
| ------------------------------------------------------------- | ------------------------------------- | -------- | ------ | ----------------------- |
| [FEAT-001](features/FEAT-001-crawl4ai-browser-replacement.md) | Replace Browser Tool with Crawl4AI    | P1       | L      | crawl4ai                |
| [FEAT-002](features/FEAT-002-deep-crawl-strategies.md)        | Implement BFS/DFS Deep Crawling       | P1       | M      | crawl4ai                |
| [FEAT-003](features/FEAT-003-multi-extraction-strategies.md)  | Multiple Extraction Strategies        | P1       | M      | crawl4ai                |
| [FEAT-004](features/FEAT-004-graham-intrinsic-value.md)       | Graham Intrinsic Value Calculator     | P1       | S      | Intrinsic-Value-Monitor |
| [FEAT-005](features/FEAT-005-technical-indicators.md)         | Technical Indicators Engine           | P2       | M      | LSTM_AI_Stock_Predictor |
| [FEAT-006](features/FEAT-006-investment-backtesting.md)       | Investment Thesis Backtesting         | P2       | L      | Intrinsic-Value-Monitor |
| [FEAT-007](features/FEAT-007-url-scoring-prioritization.md)   | URL Scoring for Source Prioritization | P1       | S      | crawl4ai                |
| [FEAT-008](features/FEAT-008-semantic-clustering.md)          | Semantic Content Clustering           | P2       | M      | crawl4ai                |
| [FEAT-009](features/FEAT-009-regex-extraction.md)             | Regex-Based Data Extraction           | P2       | S      | crawl4ai                |
| [FEAT-010](features/FEAT-010-predictive-growth-signals.md)    | Predictive Growth Signal Model        | P3       | XL     | LSTM_AI_Stock_Predictor |
| [FEAT-011](features/FEAT-011-uncertainty-estimation.md)       | Confidence Intervals for Predictions  | P2       | M      | LSTM_AI_Stock_Predictor |
| [FEAT-012](features/FEAT-012-mcp-protocol-support.md)         | MCP Protocol Tool Registration        | P3       | L      | MCP-Agents              |

---

## Improvements (Enhance Existing)

| ID                                                             | Title                               | Priority | Effort | Source Repo             |
| -------------------------------------------------------------- | ----------------------------------- | -------- | ------ | ----------------------- |
| [IMP-001](improvements/IMP-001-unified-caching-layer.md)       | Unified Caching Layer               | P1       | M      | crawl4ai                |
| [IMP-002](improvements/IMP-002-memory-adaptive-concurrency.md) | Memory-Adaptive Concurrency         | P1       | M      | crawl4ai                |
| [IMP-003](improvements/IMP-003-enhanced-rate-limiting.md)      | Enhanced Rate Limiting System       | P2       | S      | crawl4ai                |
| [IMP-004](improvements/IMP-004-structured-agent-prompts.md)    | Structured Agent Prompt Templates   | P1       | M      | MCP-Agents              |
| [IMP-005](improvements/IMP-005-agent-output-formatting.md)     | Consistent Agent Output Formatting  | P2       | S      | MCP-Agents              |
| [IMP-006](improvements/IMP-006-financial-data-pipeline.md)     | Enhanced Financial Data Pipeline    | P1       | M      | Intrinsic-Value-Monitor |
| [IMP-007](improvements/IMP-007-source-quality-enhancement.md)  | Enhanced Source Quality Scoring     | P2       | S      | crawl4ai                |
| [IMP-008](improvements/IMP-008-browser-config-management.md)   | Browser Configuration Management    | P2       | S      | crawl4ai                |
| [IMP-009](improvements/IMP-009-streaming-results.md)           | Streaming Results for Long Research | P3       | M      | crawl4ai                |
| [IMP-010](improvements/IMP-010-error-recovery-patterns.md)     | Improved Error Recovery Patterns    | P2       | M      | MCP-Agents              |

---

## Integrations (Connect External Systems)

| ID                                                       | Title                                | Priority | Effort | Source Repo             |
| -------------------------------------------------------- | ------------------------------------ | -------- | ------ | ----------------------- |
| [INT-001](integrations/INT-001-crawl4ai-library.md)      | Crawl4AI Library Integration         | P1       | L      | crawl4ai                |
| [INT-002](integrations/INT-002-alpha-vantage-api.md)     | Alpha Vantage API Integration        | P1       | M      | Intrinsic-Value-Monitor |
| [INT-003](integrations/INT-003-bond-yield-data.md)       | AAA Bond Yield Data Feed             | P2       | S      | Intrinsic-Value-Monitor |
| [INT-004](integrations/INT-004-litellm-provider.md)      | LiteLLM Multi-Provider Support       | P1       | M      | crawl4ai                |
| [INT-005](integrations/INT-005-playwright-upgrade.md)    | Playwright Browser Pool              | P2       | M      | crawl4ai                |
| [INT-006](integrations/INT-006-sentence-transformers.md) | Sentence Transformers for Clustering | P2       | M      | crawl4ai                |
| [INT-007](integrations/INT-007-tavily-enhancement.md)    | Enhanced Tavily Integration          | P3       | S      | MCP-Agents              |
| [INT-008](integrations/INT-008-yfinance-enhancement.md)  | Enhanced yfinance Features           | P3       | S      | LSTM_AI_Stock_Predictor |

---

## Technical Debt (Refactoring)

| ID                                                                 | Title                          | Priority | Effort | Source Repo |
| ------------------------------------------------------------------ | ------------------------------ | -------- | ------ | ----------- |
| [DEBT-001](technical-debt/DEBT-001-browser-tool-refactor.md)       | Browser Tool Modularization    | P1       | M      | crawl4ai    |
| [DEBT-002](technical-debt/DEBT-002-extraction-strategy-pattern.md) | Extraction Strategy Pattern    | P1       | M      | crawl4ai    |
| [DEBT-003](technical-debt/DEBT-003-config-serialization.md)        | Configuration Serialization    | P2       | S      | crawl4ai    |
| [DEBT-004](technical-debt/DEBT-004-agent-state-management.md)      | Agent State Management Cleanup | P2       | M      | MCP-Agents  |
| [DEBT-005](technical-debt/DEBT-005-async-context-managers.md)      | Proper Async Context Managers  | P2       | S      | crawl4ai    |
| [DEBT-006](technical-debt/DEBT-006-type-safety-improvements.md)    | Type Safety Improvements       | P3       | M      | All         |

---

## Learning (Research & Documentation)

| ID                                                            | Title                              | Priority | Effort | Source Repo             |
| ------------------------------------------------------------- | ---------------------------------- | -------- | ------ | ----------------------- |
| [LEARN-001](learning/LEARN-001-value-investing-principles.md) | Value Investing Principles         | P2       | S      | Intrinsic-Value-Monitor |
| [LEARN-002](learning/LEARN-002-deep-learning-forecasting.md)  | Deep Learning for Forecasting      | P2       | M      | LSTM_AI_Stock_Predictor |
| [LEARN-003](learning/LEARN-003-mcp-protocol-standard.md)      | MCP Protocol Standard              | P2       | S      | MCP-Agents              |
| [LEARN-004](learning/LEARN-004-web-extraction-patterns.md)    | Web Extraction Best Practices      | P1       | S      | crawl4ai                |
| [LEARN-005](learning/LEARN-005-multi-agent-orchestration.md)  | Multi-Agent Orchestration Patterns | P3       | M      | MCP-Agents              |

---

## Recommended Implementation Order

### Sprint 1: Foundation (Week 1-2)

1. **FEAT-001**: Replace Browser with Crawl4AI
2. **INT-001**: Crawl4AI Library Integration
3. **DEBT-001**: Browser Tool Modularization
4. **LEARN-004**: Web Extraction Best Practices

### Sprint 2: Extraction & Caching (Week 3-4)

1. **FEAT-003**: Multiple Extraction Strategies
2. **IMP-001**: Unified Caching Layer
3. **IMP-002**: Memory-Adaptive Concurrency
4. **FEAT-007**: URL Scoring for Prioritization

### Sprint 3: Financial Analysis (Week 5-6)

1. **FEAT-004**: Graham Intrinsic Value Calculator
2. **INT-002**: Alpha Vantage API Integration
3. **IMP-006**: Enhanced Financial Data Pipeline
4. **FEAT-005**: Technical Indicators Engine

### Sprint 4: Deep Research (Week 7-8)

1. **FEAT-002**: BFS/DFS Deep Crawling
2. **FEAT-008**: Semantic Content Clustering
3. **IMP-004**: Structured Agent Prompts
4. **IMP-005**: Agent Output Formatting

### Backlog (Future Sprints)

- Investment backtesting
- Predictive models
- MCP protocol support
- Streaming results

---

## Cross-Reference: External Repo → Tickets

### crawl4ai (Main Library)

- FEAT-001, FEAT-002, FEAT-003, FEAT-007, FEAT-008, FEAT-009
- IMP-001, IMP-002, IMP-003, IMP-007, IMP-008, IMP-009
- INT-001, INT-004, INT-005, INT-006
- DEBT-001, DEBT-002, DEBT-003, DEBT-005
- LEARN-004

### Intrinsic-Value-Monitor

- FEAT-004, FEAT-006
- IMP-006
- INT-002, INT-003
- LEARN-001

### LSTM_AI_Stock_Predictor

- FEAT-005, FEAT-010, FEAT-011
- INT-008
- LEARN-002

### AI-Software-Engineering-Team-MCP

- FEAT-012
- IMP-004, IMP-005, IMP-010
- INT-007
- DEBT-004
- LEARN-003, LEARN-005

### web-scraping-with-crawl4AI

- Referenced in FEAT-003 and LEARN-004 as implementation example

---

## How to Use This Backlog

1. **Pick a ticket** from the priority list
2. **Read the detailed ticket** in the linked file
3. **Check the source repo documentation** for implementation reference
4. **Implement** following the patterns described
5. **Update ticket status** when complete

Each ticket contains:

- Problem statement
- Proposed solution
- Implementation steps
- Code examples
- Acceptance criteria
- Source references
