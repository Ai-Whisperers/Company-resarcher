# Agentic Workflow Processes

**Objective**: Detailed step-by-step execution flows for the system, including cyclic loops and meta-analysis.

## 🌊 The Standard "Deep Dive" Workflow (Cyclic)

This is the default workflow for generating a full company report.

### Phase 0: Initialization

1.  **User Input**: `python main.py --url "https://example.com"`
2.  **Setup**:
    - Create `output/[Company]/` directory.
    - Initialize `GlobalState` (Blackboard).
3.  **Plan Review**:
    - Orchestrator generates a "Research Plan".
    - **Checkpoint**: User approves or refines the plan.

### Phase 1: The Gathering Wave (Primary Research)

**Goal**: Fill the "Online Data" bucket.

1.  **Vault Check**: Orchestrator queries `The Vault` for existing data on this company.
2.  **Dispatch**: Orchestrator launches Specialist Agents for _missing_ data.
3.  **Execution**:
    - **FinancialAgent**: Searches "Company X revenue", "Company X funding". Scrapes Crunchbase/News.
    - **MarketAgent**: Searches "Company X competitors", "Company X market size".
    - **SalesAgent**: Scrapes LinkedIn, Glassdoor, G2.
4.  **Data Ingestion**:
    - Every webpage visited is saved as `99-Sources/raw/Source-XXX.md`.
    - Metadata (URL, Date) is logged in `GlobalState.source_log`.
    - Extracted facts are added to `GlobalState.raw_data`.

### Phase 2: The Thinking Wave (Secondary Analysis & Logic Check)

**Goal**: Generate the "Inferred Data" bucket and verify logic.

1.  **Trigger**: Orchestrator detects Wave 1 is complete.
2.  **Analysis**:
    - **InsightGenerator**: Reads `raw_data`. Calculates "Burn Rate" (Funding / Headcount).
    - **RiskAssessor**: Checks for "Red Flags".
3.  **Logic Check (The Loop)**:
    - **LogicCritic**: Reviews the insights.
    - **Scenario A (Pass)**: Logic is sound. Proceed to Wave 3.
    - **Scenario B (Fail - Logic)**: "You said X, but data says Y." -> InsightGenerator re-thinks.
    - **Scenario C (Fail - Data)**: "Cannot determine Burn Rate without Headcount." -> **Gap Fill Request**.
4.  **Gap Fill**:
    - Orchestrator sends a targeted task back to Wave 1 ("Find Headcount").
    - _Limit_: Max 2 loops.

### Phase 3: The Writing Wave (Drafting)

**Goal**: Create the markdown reports.

1.  **Trigger**: Logic Critic approves Wave 2.
2.  **Execution**:
    - **ReportWriter**: Iterates through the 10 sections.
    - **Templating**: Uses Jinja2 templates to fill in data from `GlobalState`.
    - **Citation**: For every fact used, it looks up the `SourceID` and adds `[Source-XXX]`.
3.  **Drafting**: Saves initial `.md` files to a temporary `drafts/` folder.

### Phase 4: The Review Wave (Quality Control)

**Goal**: Ensure accuracy and attribution.

1.  **Trigger**: Drafts are ready.
2.  **Execution**:
    - **SourceReviewer**: Reads each draft.
    - **Check 1**: "Is this claim sourced?"
    - **Check 2**: "Does the source actually say this?"
3.  **Feedback Loop**:
    - **Pass**: Move file to final `output/` folder. Generate `_Sources.md`.
    - **Fail**: Send feedback back to `ReportWriter`.

### Phase 5: The Meta-Wave (Sector Intelligence)

**Goal**: Update the ecosystem knowledge.

1.  **Trigger**: Report is finalized.
2.  **Execution**:
    - **GraphBuilder**: Extracts nodes (Company, Tech, People) and edges (Competes, Uses).
    - **Update**: Pushes new data to `The Vault` (Vector/Graph DB).

---

## ⚡ Specialized Workflows

### 1. "Red Flag Check" (Fast)

- **Goal**: Quick Go/No-Go decision for investors.
- **Agents**: `Financial`, `Legal`, `RiskAssessor`.
- **Time**: ~1 minute.
- **Output**: Single-page Risk Memo.

### 2. "Sales Prep" (Tactical)

- **Goal**: 5-minute pre-meeting brief.
- **Agents**: `Sales`, `ProductFit`, `NewsMonitor`.
- **Time**: ~2 minutes.
- **Output**: 1-page Brief + Pitch Points.

### 3. "Sector Pulse" (Meta)

- **Goal**: "State of the Industry" report.
- **Agents**: `SectorAnalyst`.
- **Input**: The Vault.
- **Output**: Sector Trends & Tech Adoption Report.
