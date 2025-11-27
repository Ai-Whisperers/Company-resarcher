# Agent Roster & Responsibilities

This document details the specific roles, inputs, and outputs for every agent in the system.

## 1. The Core Team (MVP)

These agents are essential for the basic functioning of the system.

### 1.1. Orchestrator (The Hub)

- **Role**: Manages the workflow, decides the next step, and handles errors.
- **Input**: `ResearchState` (Current Wave, Errors, Data Status).
- **Output**: Next Node Name (e.g., "financial_agent", "insight_generator").
- **Tools**: None (Pure Logic).

### 1.2. Financial Agent

- **Role**: Gathers hard financial data.
- **Queries**: "Revenue 2024", "Stock Price", "EBITDA", "Annual Report PDF".
- **Tools**: `Tavily`, `Browser`, `LlamaParse` (for PDFs).
- **Output**: `financial_data` dict (Revenue, Profit, Growth, Stock Ticker).

### 1.3. Market Analyst

- **Role**: Analyzes the industry landscape.
- **Queries**: "Market Size", "CAGR", "Trends", "Competitors".
- **Tools**: `Tavily`, `Browser`.
- **Output**: `market_data` dict (TAM, SAM, SOM, Growth Rate, Top Trends).

### 1.4. Competitor Scout

- **Role**: Identifies and profiles competitors.
- **Queries**: "Top competitors of X", "X vs Y pricing".
- **Tools**: `Tavily`, `Browser`.
- **Output**: List of Competitor Profiles (Name, Strengths, Weaknesses, Pricing).

### 1.5. Insight Generator (The Brain)

- **Role**: Synthesizes raw data into strategic insights (SWOT, PESTLE).
- **Input**: `raw_data` from all gathering agents.
- **Tools**: LLM (Pure Logic).
- **Output**: Structured Insights (SWOT Analysis, Strategic Opportunities).

### 1.6. Report Writer

- **Role**: Drafts the final markdown sections.
- **Input**: Structured Insights + Raw Data.
- **Tools**: `TemplateRenderer`.
- **Output**: `drafts` dict (Markdown strings for each section).

---

## 2. The Intelligence Layer (Phase 2)

These agents add depth, verification, and memory.

### 2.1. Logic Critic (Devil's Advocate)

- **Role**: Challenges the Insight Generator's conclusions.
- **Trigger**: After Wave 2 (Thinking).
- **Logic**: Checks for contradictions, weak evidence, and logical fallacies.
- **Output**: `CritiqueResult` (Pass/Fail, Feedback).

### 2.2. Vault Manager

- **Role**: Interfaces with the Vector/Graph DBs.
- **Trigger**: Before Wave 1 (Check Memory) and After Wave 4 (Save Memory).
- **Tools**: `PineconeClient`, `Neo4jClient`.
- **Output**: Retrieved Context (Past reports) / Success Status (Saved).

### 2.3. Sales Agent

- **Role**: Matches company needs to _our_ product portfolio.
- **Input**: Company Pain Points + Our Product Catalog (RAG).
- **Output**: Recommended Products + Pitch Angle.

---

## 3. The Sector Layer (Phase 3)

These agents operate across multiple companies.

### 3.1. Sector Analyst

- **Role**: Aggregates data from 10+ companies to find sector-wide trends.
- **Input**: List of `CompanyProfiles`.
- **Output**: `SectorReport` (Tech Adoption Curves, Regulatory Shifts).

### 3.2. Graph Builder

- **Role**: Updates the Neo4j graph with new relationships.
- **Input**: Verified Company Data.
- **Logic**: Extracts entities (CEO, Suppliers, Investors) and links them.
