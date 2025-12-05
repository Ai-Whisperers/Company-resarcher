# Current AI Stack & Migration Opportunities

This document outlines the current AI/Agent technology stack used in `Company-resarcher` and identifies opportunities to modernize it using the recently researched technologies (LangChain ecosystem, Browserbase, etc.).

## 1. Current AI Stack

### Core Frameworks

- **LangGraph**: Used for orchestrating the research workflow (`src/graph`).
- **LangChain**: Used as the underlying abstraction for LLM models (`src/core/ai/langchain_models.py`).
- **FastAPI**: Serves the API (`src/api`).
- **FastMCP**: Implements the Model Context Protocol server (`src/mcp_server.py`).

### Tools (`src/tools`)

| Tool Category | Current Implementation           | Description                                      |
| :------------ | :------------------------------- | :----------------------------------------------- |
| **Browser**   | `Playwright` (Local)             | Launches a local Chromium instance for scraping. |
| **Crawling**  | `Crawl4AI`                       | Extracts markdown content from web pages.        |
| **Search**    | `Tavily`                         | Performs web searches.                           |
| **Financial** | `Alpha Vantage`, `Yahoo Finance` | Fetches stock data and technicals.               |
| **Scraping**  | `BeautifulSoup`                  | Parses HTML for specific selectors.              |

### MCP Server (`src/mcp_server.py`)

We expose a **FastMCP** server named "Company Researcher" with the following tools:

- `research_company`: Triggers the full research pipeline.
- `analyze_stock`: Runs financial analysis (technicals, intrinsic value).
- `get_financial_data`: Fetches raw financial statements.
- `calculate_intrinsic_value`: Graham formula calculator.
- `crawl_url` / `deep_crawl`: Exposes Crawl4AI capabilities.
- `search_web`: Exposes Tavily search.

## 2. Migration & Modernization Opportunities

We have identified several areas where new technologies can replace or enhance existing components.

### A. Browser Automation: Local Playwright -> Browserbase

- **Current**: `src/tools/browser` uses local Playwright. This is hard to scale and easily blocked.
- **Target**: **Browserbase**.
- **Benefit**: Serverless, stealthy, scalable, and includes "Stagehand" for AI-driven navigation.
- **Action**: Refactor `BrowserTool` to connect to Browserbase WebSocket.

### B. Scraping: BeautifulSoup -> Scrapegraph-AI

- **Current**: Custom parsing logic using `BeautifulSoup` or regex. Brittle to UI changes.
- **Target**: **Scrapegraph-AI**.
- **Benefit**: LLM-driven extraction ("Get the pricing table") is resilient to layout changes.
- **Action**: Create a `SmartScraperTool` that uses Scrapegraph-AI for complex pages.

### C. Prompt Engineering: Manual Templates -> DSPy

- **Current**: Jinja2 templates or f-strings in `src/prompts`.
- **Target**: **DSPy**.
- **Benefit**: Automatic prompt optimization and type-safe outputs.
- **Action**: Pilot DSPy for the `FinancialDataTool` extraction logic to improve accuracy.

### D. Knowledge Storage: Postgres/Redis -> LanceDB

- **Current**: Relational data in Postgres, caching in Redis.
- **Target**: **LanceDB**.
- **Benefit**: Store embeddings of every research document. Enables "Chat with Research" features (RAG).
- **Action**: Add a `VectorStore` component using LanceDB to index research outputs.

### E. Orchestration: LangGraph -> Temporal (Hybrid)

- **Current**: LangGraph handles state.
- **Target**: **Temporal** (wrapping LangGraph).
- **Benefit**: If a research job takes 3 days (e.g., "Monitor news"), Temporal guarantees it survives server restarts.
- **Action**: Wrap the `ResearchPipeline.execute()` call in a Temporal Activity.

## 3. Recommended Roadmap

1.  **Phase 1 (Low Hanging Fruit)**:

    - Integrate **Browserbase** to fix scraping blocks.
    - Add **LangSmith** tracing (already configured, just needs env vars).

2.  **Phase 2 (Intelligence Upgrade)**:

    - Implement **Scrapegraph-AI** for difficult sites.
    - Add **LanceDB** to store research for RAG.

3.  **Phase 3 (Optimization)**:
    - Refactor prompts to **DSPy** modules.
    - (Optional) Add **Temporal** if long-running monitoring is required.
