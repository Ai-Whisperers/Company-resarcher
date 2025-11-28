# Company Researcher System

**An Autonomous Multi-Agent System for Deep B2B & Investment Analysis**

## Overview

The **Company Researcher System** is an advanced AI-powered platform designed to automate the gathering and analysis of deep company intelligence. Unlike standard scrapers that just grab text, this system employs a **Multi-Agent Architecture** to "think" like a human researcher, strategist, and financial analyst combined.

Our goal is to provide **"All Perspectives"** on a target company to drive two key outcomes:

1. **B2B Sales**: Identify specific pain points and strategic gaps to pitch our services
2. **Investment Analysis**: Detect growth signals, risks, and competitive advantages

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Ai-Whisperers/Company-resarcher.git
cd Company-resarcher

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run research
python main.py --name "Adidas" --industry "Sportswear"
```

## Core Architecture

### The Agents

| Agent | Role |
|-------|------|
| **Researcher** | Scours the web, financial portals, and news sites |
| **Analyst** | Processes raw data into structured insights |
| **Strategist** | Forms sales pitches or investment theses |
| **Critic** | Reviews findings for bias and quality |

### V2 Research Schema

We organize research into a structured hierarchy:

- `00-Strategic-Context/` - Company overview, key people, mission
- `01-Market-Intelligence/` - Market size, trends, regulatory landscape
- `02-Target-Audience/` - ICPs, customer demographics
- `03-Competitive-Landscape/` - Competitors, SWOT analysis
- `04-Brand-Strategy/` - Positioning, messaging
- `05-Marketing-Execution/` - Channels, content strategy
- `06-Data-Room/` - Financials, statistics
- `99-Sources/` - Raw source logging for auditability

## Key Features

- **Granular Reporting** - Generates 20+ specific markdown reports
- **Source Tracking** - Every webpage saved for full auditability
- **Resilient AI Client** - Automatic fallback handling
- **Template System** - Consistent, high-quality outputs
- **Smart JSON Parsing** - Handles noisy LLM outputs

## Documentation

<div class="grid cards" markdown>

-   :material-rocket-launch: **Getting Started**

    ---

    Get up and running quickly

    [:octicons-arrow-right-24: Setup Guide](guides/SETUP.md)

-   :material-cog: **Configuration**

    ---

    All settings and environment variables

    [:octicons-arrow-right-24: Configuration](guides/CONFIGURATION.md)

-   :material-api: **API Reference**

    ---

    REST API documentation

    [:octicons-arrow-right-24: API Reference](api/API_REFERENCE.md)

-   :material-source-branch: **Architecture**

    ---

    Design patterns and system architecture

    [:octicons-arrow-right-24: Architecture](architecture/patterns/README.md)

</div>

## Requirements

- Python 3.10+
- OpenAI API Key (or Anthropic/Gemini/Groq)
- Tavily API Key (for search)

## License

MIT License - See [LICENSE](https://github.com/Ai-Whisperers/Company-resarcher/blob/main/LICENSE)
