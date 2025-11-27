# Agentic Pattern Reference

**Objective**: Explicitly map the 21 AI Design Patterns to the system's architecture, now including Cyclic and Meta-Analysis patterns.

## 🏗️ Core Patterns (Execution)

| Pattern                 | Implementation in System                                                   | Agents Involved |
| :---------------------- | :------------------------------------------------------------------------- | :-------------- |
| **01. Prompt Chaining** | **Wave 3 (Writing)**: `Draft Section` -> `Check Source` -> `Refine Tone`.  | `ReportWriter`  |
| **02. Routing**         | **Orchestrator**: Routes sub-tasks to specific domains.                    | `Orchestrator`  |
| **03. Parallelization** | **Wave 1 (Gathering)**: All 5 Researchers run concurrently.                | All Researchers |
| **04. Reflection**      | **Wave 2 (Logic Check)**: `LogicCritic` challenges the `InsightGenerator`. | `LogicCritic`   |
| **05. Tool Use**        | **Browser & Search**: `BrowserUse` and `Tavily`.                           | All Researchers |
| **06. Planning**        | **Initialization**: Decomposes goal into a DAG of questions.               | `Orchestrator`  |
| **07. Multi-Agent**     | **The Whole System**: Team of Experts with Shared State.                   | All Agents      |

## 🧠 Advanced Patterns (Intelligence)

| Pattern          | Implementation in System                                          | Agents Involved |
| :--------------- | :---------------------------------------------------------------- | :-------------- |
| **08. Memory**   | **The Vault**: Cross-project vector storage.                      | `VaultClient`   |
| **09. Learning** | **Few-Shot Prompting**: Initialized with "Good vs. Bad" examples. | All Agents      |
| **10. MCP**      | **Resource Access**: Standardized access to `99-Sources/raw`.     | `FileManager`   |
| **11. Goals**    | **Completeness Check**: Tracks % of fields filled.                | `Orchestrator`  |

## 🛡️ Integration Patterns (Reliability)

| Pattern               | Implementation in System                                       | Agents Involved    |
| :-------------------- | :------------------------------------------------------------- | :----------------- |
| **12. Exceptions**    | **Gap Fill Loop**: If data is missing, loop back to Wave 1.    | `Orchestrator`     |
| **13. Human-in-Loop** | **Plan Review**: User approves research plan before execution. | `Orchestrator`     |
| **14. RAG**           | **Company Brain**: Querying collected raw data.                | `InsightGenerator` |

## 🚀 Production Patterns (Scale)

| Pattern                | Implementation in System                               | Agents Involved    |
| :--------------------- | :----------------------------------------------------- | :----------------- |
| **15. A2A Comm**       | **Graph State**: Blackboard Pattern.                   | All Agents         |
| **16. Optimization**   | **Budget Manager**: Enforces token/$ limits.           | `BudgetManager`    |
| **17. Reasoning**      | **Chain of Thought**: Deriving insights from raw data. | `InsightGenerator` |
| **18. Guardrails**     | **Source Enforcement**: Blocking unsourced claims.     | `SourceReviewer`   |
| **19. Evaluation**     | **Quality Score**: Confidence scoring.                 | `SourceReviewer`   |
| **20. Prioritization** | **Task Queue**: Prioritizing critical data points.     | `Orchestrator`     |
| **21. Exploration**    | **Sector Intelligence**: Meta-analysis of the Vault.   | `SectorAnalyst`    |
