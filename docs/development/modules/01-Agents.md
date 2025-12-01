# Agents Module Documentation

This module contains the core logic for the AI agents that drive the research process.

## 1. Base Agent (`src/agents/base_agent.py`)

The abstract base class for all research agents. It handles tool injection, LLM interaction with retries, and data gathering.

### Class: `BaseAgent`

- **`__init__(self, client, name, prompt_template, search_tool, browser_tool, renderer)`**:
  - Initializes the agent with necessary tools and services.
  - Supports dependency injection via `from_container()`.
- **`research(self, company: CompanyProfile) -> ResearchPhaseResult`**:
  - Abstract method that must be implemented by all subclasses.
- **`_safe_generate(self, prompt, response_format, timeout)`**:
  - Invokes the AI client with retry logic for rate limits and timeouts.
- **`_gather_data(self, queries: List[str]) -> List[ResearchSource]`**:
  - Executes search queries in parallel using `SearchTool` and `BrowserTool`.
  - Handles rate limiting and deduplication.
- **`execute_research_cycle(...)`**:
  - Standard workflow: Gather Data -> Load Prompt -> Generate JSON -> Render Report.

---

## 2. Deep Research Agent (`src/agents/deep_research.py`)

The primary agent for recursive, depth-first research.

### Class: `DeepResearchAgent`

- **`deep_research(self, query, breadth, depth, ...)`**:
  - Recursively generates search queries, scrapes results, extracts learnings, and generates follow-up questions.
- **`research(self, company: CompanyProfile)`**:
  - Initiates the deep research process for a company.

---

## 3. Specialists (`src/agents/specialists.py`)

Specialized agents focusing on specific domains.

### Class: `FinancialAgent`

- **Focus**: Financial performance, SEC filings, stock analysis.
- **Key Methods**:
  - `_fetch_sec_data`: Retrieves 10-K filings.
  - `research`: Combines SEC data and quantitative analysis (via `AlphaFactorMiner`) to generate `01-Financials.md`.

### Class: `MarketAnalyst`

- **Focus**: Market size, trends, demographics.
- **Output**: `01-Market-Size-Growth.md`.

### Class: `CompetitorScout`

- **Focus**: Competitor analysis, tech stack detection.
- **Key Methods**:
  - `_fetch_tech_stack`: Analyzes the company's technology usage.
  - `research`: Generates `01-Competitor-List.md` with a comparison matrix.

### Class: `BrandAuditor`

- **Focus**: Brand reputation, sentiment, positioning.
- **Output**: `01-Positioning.md`.

### Class: `SalesAgent`

- **Focus**: Sales strategy, channels, pricing.
- **Output**: `05-Sales-Strategy.md`.

---

## 4. Sector Analyst (`src/agents/sector_analyst.py`)

Analyzes broader sector trends by aggregating data from multiple companies.

### Class: `SectorAnalyst`

- **`analyze_sector(self, sector_name)`**:
  - Fetches companies from the Vault.
  - Aggregates data and generates a sector-wide report.

---

## 5. Orchestration

_Note: The orchestration logic has moved to `src/pipeline/orchestrator.py`._

The `PipelineOrchestrator` manages the execution of these agents, handling the flow of data and context between them.
