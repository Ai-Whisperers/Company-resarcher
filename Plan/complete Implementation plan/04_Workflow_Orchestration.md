# Workflow Orchestration: The 4 Waves

This document details the cyclic execution flow of the system.

## 1. The "Gap Fill" Philosophy

Unlike linear chains, our workflow is designed to **loop back**.

- **Linear**: Gather -> Analyze -> Write.
- **Cyclic**: Gather -> Analyze -> (Missing Data?) -> Gather -> Analyze -> Write.

## 2. Detailed Wave Breakdown

### Wave 1: Gathering (Parallel Execution)

- **Trigger**: Start of process OR "Gap Fill" request.
- **Action**: `Orchestrator` triggers `FinancialAgent`, `MarketAnalyst`, `CompetitorScout` in parallel.
- **Logic**:
  - Agents check `ResearchState` for existing data to avoid redundant work.
  - Agents use `BrowserTool` and `Tavily` to fetch new data.
  - Agents update `raw_sources` and `source_log`.

### Wave 2: Thinking (Analysis & Synthesis)

- **Trigger**: Completion of Wave 1.
- **Action**: `InsightGenerator` processes raw data.
- **Logic**:
  - Extracts structured data (Revenue, SWOT, etc.).
  - **Self-Correction Check**: "Do I have enough data to answer the user's request?"
  - **IF NO**: Triggers `GapFillRequest` -> Returns to Wave 1 with specific queries.
  - **IF YES**: Proceed to Logic Critic.

### Wave 2.5: The Logic Critic (Verification)

- **Trigger**: `InsightGenerator` produces a draft insight.
- **Action**: `LogicCritic` reviews the insight.
- **Logic**:
  - "Is this revenue figure from 2024 or 2021?"
  - "Does the SWOT analysis contradict the financial data?"
  - **IF FAIL**: Returns to Insight Generator with feedback.
  - **IF PASS**: Proceed to Wave 3.

### Wave 3: Writing (Drafting)

- **Trigger**: Validated Insights.
- **Action**: `ReportWriter` generates Markdown.
- **Logic**:
  - Uses Jinja2 templates (`01-Market-Intelligence.md`, etc.).
  - Injects data and citations.
  - Saves drafts to `ResearchState.drafts`.

### Wave 4: Review & Delivery

- **Trigger**: Drafts complete.
- **Action**: `SourceReviewer` / Human Review.
- **Logic**:
  - Checks for broken links or hallucinated sources.
  - **Collaborative Mode**: Pauses for Human Approval (if configured).
  - **Finalize**: Writes files to disk (`/output/{Company}/`).
  - **Vault**: Upserts knowledge to Pinecone/Neo4j.

---

## 3. The Meta-Wave (Sector Intelligence)

This runs _after_ multiple single-company runs.

1.  **Trigger**: User requests "Sector Report for Fintech".
2.  **Gather**: `SectorAnalyst` queries the Vault for all "Fintech" companies.
3.  **Analyze**: Aggregates metrics (e.g., "Average CAC in Fintech").
4.  **Synthesize**: Identifies trends common across the dataset.
5.  **Write**: Generates a Sector Report.
