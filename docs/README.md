# Documentation Index

Welcome to the **Company Researcher** documentation.

## Structure

```text
docs/
├── architecture/           # System design & patterns
│   ├── patterns/          # AI design patterns (21 patterns)
│   └── critiques/         # System analysis & critiques
├── development/           # Developer resources
│   ├── modules/           # Module-level documentation
│   │   ├── 01-Agents.md   # Agent architecture
│   │   ├── 02-Core.md     # Core utilities
│   │   ├── 03-Graph.md    # LangGraph workflow
│   │   ├── 04-Tools.md    # Data acquisition tools
│   │   └── 05-Services.md # Helper services
│   └── workflows/         # Development workflows
├── guides/                # User & developer guides
│   ├── CONTRIBUTING.md    # Contribution guidelines
│   └── QUICK_START_TOOLS.md
├── planning/              # Project planning
│   ├── backlog/           # Future features (38 items)
│   ├── ideas/             # Implementation concepts
│   └── technical/         # Technical specifications
└── reference/             # External references
    └── external_repos/    # Related repository analysis
```

## Quick Links

### Getting Started

- [Project README](../README.md) - Project overview and setup
- [Contributing Guide](guides/CONTRIBUTING.md) - How to contribute
- [Quick Start Tools](guides/QUICK_START_TOOLS.md) - Tool usage guide

### Architecture

- [AI Design Patterns](architecture/patterns/README.md) - 21 agentic patterns
- [System Architecture](architecture/patterns/ARCHITECTURE_ANALYSIS.md) - Architecture overview

### Development

- [Agents Documentation](development/modules/01-Agents.md) - Agent system
- [Core Utilities](development/modules/02-Core.md) - Core infrastructure
- [Graph Workflow](development/modules/03-Graph.md) - LangGraph details
- [Tools Reference](development/modules/04-Tools.md) - Data acquisition tools

### Planning

- [Feature Backlog](planning/backlog/0_README.md) - Upcoming features
- [Technical Plans](planning/technical/) - Implementation details

## Module Overview

| Module | Description | Key Files |
|--------|-------------|-----------|
| `src/agents/` | Multi-agent orchestration | orchestrator.py, specialists.py |
| `src/api/` | FastAPI REST interface | app.py, models.py |
| `src/core/` | Infrastructure & utilities | config.py, ai_client.py |
| `src/graph/` | LangGraph state machine | graph_builder.py, state.py |
| `src/tools/` | Data acquisition tools | search.py, browser.py |
| `src/templates/` | Report templates (30+) | Jinja2 markdown templates |

## Test Structure

```text
tests/
├── conftest.py            # Shared fixtures
├── unit/                  # Unit tests (fast, isolated)
├── integration/           # Integration tests
└── manual/                # Manual verification tests
```

Run tests with: `pytest` or `pytest -m "not slow"`
