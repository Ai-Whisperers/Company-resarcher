# Company Researcher - System Design & IDE Plan

## Overview

This document outlines the detailed plan and IDE setup for the `Company-resarcher` repository. The goal is to build an autonomous agentic system that researches prospective client companies and generates a comprehensive, structured knowledge base for each.

## 1. The "IDE" (System Design)

We are building a **Multi-Agent Research System**. Instead of a single script, we will have specialized "agents" that focus on different aspects of a company (Market, Brand, Competitors, etc.).

### Core Concept: The "Research Factory"

Imagine a factory line where a company name enters, and a complete dossier exits.

1.  **Input**: List of companies (e.g., "Nestlé", "Coca-Cola").
2.  **Orchestrator**: The manager that assigns tasks.
3.  **Workers (Agents)**:
    - _The Analyst_: Looks at market numbers.
    - _The Creative_: Looks at ads and branding.
    - _The Spy_: Looks at competitors.
4.  **Output**: A perfectly organized folder structure.

### Detailed Folder Structure (The Output)

This is the "product" we are delivering. For every company, the system will generate:

```text
[Company Name]/
├── 00-Executive-Brief/
│   ├── 00-Quick-Audit.md          # Immediate findings & "low hanging fruit"
│   └── 01-Executive-Summary.md    # 1-page overview for decision makers
├── 01-Market-Intelligence/
│   ├── Industry-Trends.md         # What's happening in their world?
│   ├── Market-Size.md             # TAM/SAM/SOM data
│   └── Regulatory-Notes.md        # Laws/Regulations affecting them
├── 02-Brand-Analysis/
│   ├── Brand-Voice.md             # How they talk (formal, fun, etc.)
│   ├── Positioning.md             # Where they sit in the market
│   └── Visual-Identity.md         # Colors, fonts, vibe
├── 03-Competitive-Landscape/
│   ├── Competitor-Matrix.md       # Table comparing features/pricing
│   ├── Competitor-Deep-Dives/     # Detailed files for top 3 rivals
│   └── Gap-Analysis.md            # What competitors do that they don't
├── 04-Customer-Insights/
│   ├── ICP-Personas/              # Detailed profiles of their buyers
│   └── Customer-Reviews.md        # What people are saying online
├── 05-Data-Room/
│   ├── Financials.md              # Revenue, stock price, funding
│   └── Statistics.md              # Verified data points with sources
└── 99-Sources/
    ├── Source-Log.csv             # Every URL visited
    └── Raw-Data/                  # Backup of text extracted
```

## 2. Technical Architecture

### The Stack

- **Python 3.10+**: The engine.
- **Pydantic**: For strict data validation (ensuring our JSONs are perfect).
- **AsyncIO**: To run multiple searches in parallel (speed is key).
- **Search API**: Tavily or SerpAPI (for high-quality web results).
- **LLM**: GPT-4o or Claude 3.5 Sonnet (the "brain").

### The Workflow

1.  **Initialization**: Load the list of companies.
2.  **Phase 1 - Reconnaissance**:
    - Find official website, LinkedIn, and basic description.
    - Determine the industry and top 3 competitors.
3.  **Phase 2 - Deep Research (Parallel)**:
    - Agent A searches for "Market trends in [Industry]".
    - Agent B searches for "[Company] brand guidelines" or analyzes their blog.
    - Agent C searches for "[Competitor] pricing".
4.  **Phase 3 - Synthesis**:
    - The LLM reads the raw search results.
    - It writes the Markdown files based on specific templates.
5.  **Phase 4 - Review**:
    - The system checks if any critical sections are empty.
    - If empty, it triggers a "Gap Fill" search.

## 3. IDE Setup (Development Environment)

To build this effectively, we recommend the following setup in VSCode:

### Recommended Extensions

- **Python (Microsoft)**: Essential for debugging and IntelliSense.
- **Ruff**: The fastest Python linter. It will keep your code clean automatically.
- **Pylance**: For type checking.
- **Markdown All in One**: To preview the generated reports easily.
- **GitLens**: To track changes in the codebase.

### Project Structure (Codebase)

This is how we will organize the _code_ (not the output):

```text
src/
├── agents/           # The "brains" (MarketAgent, BrandAgent, etc.)
├── tools/            # The "hands" (Search, WebScraper, FileSaver)
├── core/             # Config, Logging, Types
├── templates/        # Markdown templates for the reports
└── main.py           # The entry point
```

## Next Steps

1.  **Approve this plan**: Confirm the folder structure is what you want.
2.  **Setup Environment**: We will create the `src` folder and install dependencies.
3.  **Build the Prototype**: We will create a simple version that does just _one_ folder (e.g., "Brand Analysis") to test the concept.
