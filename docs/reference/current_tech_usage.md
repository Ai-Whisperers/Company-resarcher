# Current Technology Usage Analysis

This document outlines how the requested technologies are currently utilized within the `Company-resarcher` repository.

## Summary

| Technology         | Status              | Current Implementation                                                       |
| :----------------- | :------------------ | :--------------------------------------------------------------------------- |
| **LangChain**      | ✅ **Heavily Used** | Core abstraction for LLM interactions and model unification.                 |
| **LangSmith**      | ✅ **Used**         | Configured for observability and tracing of LLM runs.                        |
| **LangFlow**       | ❌ **Not Used**     | Workflows are built using **LangGraph** via code, not a visual UI.           |
| **Browserbase**    | ❌ **Not Used**     | Browser automation is handled by **Playwright** and **Crawl4AI**.            |
| **Scrapegraph-AI** | ❌ **Not Used**     | Scraping is performed using **Crawl4AI**, **BeautifulSoup**, and **Tavily**. |
| **DSPy**           | ❌ **Not Used**     | Prompt engineering is manual/template-based via LangChain.                   |
| **LanceDB**        | ❌ **Not Used**     | Data storage relies on **PostgreSQL (AsyncPG)** and **Redis**.               |
| **Temporal.io**    | ❌ **Not Used**     | Orchestration is handled by **LangGraph** and Python's `asyncio`.            |

## Detailed Usage

### 1. LangChain

**Location:** `src/core/ai/langchain_models.py`

- **Model Factory:** The project implements a `ModelFactory` that wraps LangChain's chat models (`ChatAnthropic`, `ChatOpenAI`, `ChatGoogleGenerativeAI`, `ChatGroq`, `ChatOllama`).
- **Resilience:** LangChain runnables are wrapped with custom resilience layers:
  - `CircuitBreakerRunnable`
  - `RateLimitedRunnable`
  - `TimeoutRunnable`
- **Fallbacks:** Automatic fallback chains are configured (e.g., Primary -> Fallback 1 -> Fallback 2).

### 2. LangSmith

**Location:** `src/core/ai/langsmith_setup.py`

- **Configuration:** A setup module checks for `LANGSMITH_API_KEY` and enables tracing by setting environment variables (`LANGCHAIN_TRACING_V2=true`).
- **Integration:** It is integrated into the `ModelFactory` initialization to ensure all model calls are traced.

### 3. LangFlow

- **Current State:** The project uses **LangGraph** (`src/graph/graph_builder.py`) to define research workflows programmatically.
- **Potential:** LangFlow could be used to visualize or prototype these graphs, but it is not currently part of the runtime stack.

### 4. Browserbase & Scrapegraph-AI

- **Current State:** The project uses:
  - **Playwright**: For direct browser automation (`src/tools/browser`).
  - **Crawl4AI**: For efficient web crawling and extraction.
  - **Tavily**: For search and content retrieval.
- **Potential:** Browserbase could replace the local Playwright setup for better scalability/stealth. Scrapegraph-AI could replace custom scraping logic.

### 5. DSPy

- **Current State:** Prompts are likely managed as f-strings or Jinja2 templates within the `src/prompts` directory or agent classes.
- **Potential:** DSPy could be introduced to optimize these prompts automatically.

### 6. LanceDB

- **Current State:** The project uses **PostgreSQL** (with `asyncpg` and `sqlalchemy`) for structured data and **Redis** for caching/state.
- **Potential:** LanceDB could be added if high-performance vector search or multimodal data storage becomes a requirement.

### 7. Temporal.io

- **Current State:** Long-running workflows are managed by **LangGraph**'s state management and checkpointing system.
- **Potential:** Temporal could be useful if the workflows need to survive process restarts or run over extremely long periods (days/weeks) with robust retries, but LangGraph handles much of this for agentic workflows.
