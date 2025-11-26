# Agentic Agents Registry

**Objective**: The master directory of all agents, defining their roles, tools, and I/O.

---

## 🏛️ The Core Team (MVP)

### 1. Orchestrator

- **Role**: Project Manager & Router.
- **Input**: User Request ("Research Company X").
- **Output**: Task Assignments to Specialist Agents.
- **Tools**: `BudgetManager`, `VaultClient`.
- **Key Responsibility**: Managing the `GlobalState`, enforcing the 4-Wave process, and handling "Gap Fill" requests.

### 2. Financial Researcher

- **Role**: Quantitative Data Gatherer.
- **Input**: Task ("Find revenue for X").
- **Output**: `FinancialData` object (Revenue, Funding, Stock).
- **Tools**: `Tavily` (Search), `Browser` (Scraping).
- **Focus**: 10-K filings, Crunchbase, Yahoo Finance.

### 3. Market Researcher

- **Role**: Macro Strategist.
- **Input**: Task ("Analyze market for X").
- **Output**: `MarketData` object (Competitors, Trends, TAM).
- **Tools**: `Tavily`, `Browser`.
- **Focus**: Industry reports, Competitor websites, News.

### 4. Sales Researcher

- **Role**: Deal Intelligence.
- **Input**: Task ("Find buyer personas for X").
- **Output**: `SalesData` object (Pain points, Tech stack).
- **Tools**: `LinkedIn` (via Browser), `BuiltWith`.
- **Focus**: Employee profiles, Job postings, Customer reviews (G2/Capterra).

### 5. Insight Generator

- **Role**: Data Synthesizer (Wave 2).
- **Input**: Full `raw_data` from Wave 1.
- **Output**: `InferredData` (Calculated metrics, Risk scores).
- **Tools**: None (LLM Reasoning).
- **Focus**: Cross-referencing data to find hidden insights.

### 6. Logic Critic Agent (The Devil's Advocate)

- **Role**: Logic Validator (Wave 2).
- **Input**: `InferredData` + `raw_data`.
- **Output**: `CritiqueResult` (Pass/Fail + Feedback).
- **Tools**: None (LLM Reasoning).
- **Focus**: Challenging assumptions, detecting contradictions, and requesting "Gap Fills".

### 7. Report Writer

- **Role**: Content Drafter (Wave 3).
- **Input**: `GlobalState` (Raw + Inferred Data).
- **Output**: Markdown files (`01-Overview.md`, etc.).
- **Tools**: Jinja2 Templates.
- **Focus**: Tone, formatting, and structure.

### 8. Source Reviewer

- **Role**: Quality Assurance (Wave 4).
- **Input**: Draft Markdown files + `SourceLog`.
- **Output**: Validated Files OR Rejection Feedback.
- **Tools**: Source Lookup.
- **Focus**: "Is this claim cited?" "Is the link valid?"

---

## 🚀 The Expanded Team (Future)

### 9. Legal & Compliance Agent

- **Focus**: Lawsuits, GDPR, IP disputes.
- **Workflow**: "Red Flag Check".

### 10. Brand Identity Agent

- **Focus**: Visuals, Colors, Ad Creatives.
- **Tools**: Vision API.

### 11. Product Fit Agent

- **Focus**: Mapping company pain points to _your_ product.
- **Output**: Tailored Sales Pitch.

### 12. News Monitor Agent

- **Focus**: Real-time events (last 30 days).
- **Tools**: Google News, RSS.

### 13. Query Refiner Agent

- **Focus**: Optimizing search queries for other agents.
- **Pattern**: Prompt Chaining.

### 14. Sector Analyst Agent (The Meta-Brain)

- **Role**: Cross-Company Analysis.
- **Input**: Aggregated data from multiple companies (The Vault).
- **Output**: `Sector_Report.md` (Trends, Tech Adoption, Causal Links).
- **Tools**: Graph Query, Trend Analysis.

### 15. Graph Builder Agent (The Cartographer)

- **Role**: Knowledge Graph Maintenance.
- **Task**: Updates the "Vault" with new nodes/edges after each company research.
