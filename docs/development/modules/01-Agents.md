# Agents Module Documentation

This module contains the core logic for the AI agents that drive the research process.

## 1. Orchestrator (`src/agents/orchestrator.py`)

The `ResearchOrchestrator` is the main entry point for the system. It initializes the LangGraph workflow and manages the execution lifecycle.

### Class: `ResearchOrchestrator`

- **`__init__(self)`**: Initializes the `ResearchState` graph by calling `build_graph()`.
- **`conduct_research(self, company_name: str, url: str) -> Dict[str, Any]`**:
  - **Input**: Company name and website URL.
  - **Output**: Final state dictionary containing gathered data, drafts, and logs.
  - **Logic**:
    1.  Initializes `ResearchState` with the input data.
    2.  Invokes the LangGraph (`self.graph.ainvoke`).
    3.  Returns the final state or raises an exception on failure.

---

## 2. Specialists (`src/agents/specialists.py`)

This file defines the specialized agents responsible for specific research domains. All agents inherit from `BaseAgent`.

### Class: `MarketAnalyst`

Researches industry trends, market size, and growth.

- **`research(self, company: CompanyProfile) -> ResearchPhaseResult`**:
  - Generates queries for market size, trends, and growth.
  - Uses `_gather_data` to fetch information.
  - Prompts the LLM to generate a structured JSON report (Market Size, CAGR, Trends).
  - Renders `01-Market-Intelligence.md`.

### Class: `BrandAuditor`

Analyzes brand voice, positioning, and values.

- **`research(self, company: CompanyProfile) -> ResearchPhaseResult`**:
  - Generates queries for brand values, mission, and tone of voice.
  - Prompts the LLM to extract USP, Brand Archetype, and Messaging Pillars.
  - Renders `04-Brand-Strategy.md`.

### Class: `CompetitorScout`

Identifies and analyzes competitors.

- **`research(self, company: CompanyProfile) -> ResearchPhaseResult`**:
  - Searches for top competitors and alternatives.
  - Prompts the LLM to create a comparison matrix (Strengths, Weaknesses, Pricing).
  - Renders `03-Competitive-Landscape.md`.

---

## 3. Base Agent (`src/agents/base_agent.py`)

The abstract base class for all agents.

### Class: `BaseAgent`

- **`__init__(self, ai_client, search_tool, browser_tool)`**: Dependency injection for tools.
- **`_gather_data(self, queries: List[str]) -> List[ResearchSource]`**: Helper to run search and browser tools.
- **`_render(self, template_name: str, data: Dict, sources: List[ResearchSource]) -> str`**: Helper to render Jinja2 templates.
