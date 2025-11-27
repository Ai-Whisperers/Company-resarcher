# Company Researcher System

**An Autonomous Multi-Agent System for Deep B2B & Investment Analysis**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)

## 📖 Overview

The **Company Researcher System** is an advanced AI-powered platform designed to automate the gathering and analysis of deep company intelligence. Unlike standard scrapers that just grab text, this system employs a **Multi-Agent Architecture** to "think" like a human researcher, strategist, and financial analyst combined.

Our goal is to provide **"All Perspectives"** on a target company to drive two key outcomes:

1.  **B2B Sales**: Identify specific pain points and strategic gaps to pitch our services (Social Media Intelligence, AI Training, Automation).
2.  **Investment Analysis**: Detect growth signals, risks, and competitive advantages for a future investment platform.

## 🏗️ Core Architecture

The system is built on a **V2 Research Schema** that breaks down analysis into granular, focused phases.

### 🤖 The Agents

1.  **The Researcher**: Scours the web, financial portals, and news sites. It handles navigation, anti-bot detection, and raw data extraction.
2.  **The Analyst**: Processes raw data into structured insights using RAG (Retrieval-Augmented Generation) and Reflection patterns.
3.  **The Strategist**: Connects the dots between data points to form a sales pitch or investment thesis.
4.  **The Critic**: Reviews findings for bias, hallucinations, and quality assurance.

### 📂 V2 Research Schema

We organize research into a structured hierarchy of Markdown reports:

- `00-Strategic-Context/`: Company overview, key people, mission.
- `01-Market-Intelligence/`: Market size, trends, regulatory landscape.
- `02-Target-Audience/`: ICPs, customer demographics.
- `03-Competitive-Landscape/`: Direct/indirect competitors, SWOT.
- `04-Brand-Strategy/`: Positioning, messaging, archetypes.
- `05-Marketing-Execution/`: Channels, content strategy.
- `06-Data-Room/`: Financials, statistics.
- `07-Creative-Inspiration/`: Visual style, ad examples.
- `99-Sources/`: **Raw Source Logging** for full auditability.

## ✨ Key Features

- **Granular Reporting**: Generates 20+ specific markdown reports (e.g., `01-Financials.md`, `04-Key-People.md`) instead of one giant blob of text.
- **Robust Source Tracking**: Every webpage visited is saved as a raw markdown file in `99-Sources/raw/`, and logged in `Source-Log.md`.
- **Resilient AI Client**: Automatically falls back to a Mock Client if OpenAI/Anthropic rate limits are hit, ensuring the pipeline never crashes.
- **Jinja2 Templating**: Uses strict templates to ensure consistent, high-quality output formats.
- **Smart JSON Parsing**: Includes a robust parser to handle "noisy" LLM outputs.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API Key (or Anthropic)
- Tavily API Key (for search)

### Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/Ai-Whisperers/Company-resarcher.git
    cd Company-resarcher
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file:
    ```env
    OPENAI_API_KEY=sk-...
    TAVILY_API_KEY=tvly-...
    ```

### Usage

Run the main script with a company name and industry:

```bash
python main.py --name "Adidas" --industry "Sportswear"
```

The system will:

1.  Create the folder structure in `output/Adidas/`.
2.  Execute all research phases sequentially.
3.  Generate markdown reports and save raw sources.

## 🗺️ Roadmap

- [x] **Phase 1: Foundation**: Core agents, V2 Schema, File Management.
- [ ] **Phase 2: Intelligence**: Implement RAG (Vector DB) to query the "Company Brain".
- [ ] **Phase 3: Specialist Agents**: Deploy `SalesAgent` and `InvestmentAgent` to act on the data.
- [ ] **Phase 4: Graph Analysis**: Connect insights across multiple companies.

## 📚 Documentation

- [**Agentic Workflow Strategy**](./docs/plans/agentic_workflow_strategy.md): Detailed breakdown of our AI design patterns.
- [**Repository Explanations**](./docs/repo_explanations/): In-depth guide to all 44 repos in our ecosystem.
- [**Research Schema Design**](./docs/plans/research_schema_design.md): The blueprint for our data structure.
- [**Quick Start Tools**](./docs/guides/QUICK_START_TOOLS.md): Guide for new tools.

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License. See [LICENSE](./LICENSE).
