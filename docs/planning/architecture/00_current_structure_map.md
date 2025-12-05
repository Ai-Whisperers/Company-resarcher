# Current Project Structure Map

This document captures the state of the `src` directory before refactoring.

## Source Root (`src/`)

- `agents/`
- `api/`
- `cli/`
- `core/` (Overloaded)
- `dashboard/`
- `data/`
- `evaluation/`
- `graph/`
- `mcp/`
- `middleware/`
- `pipeline/`
- `plugins/`
- `prompts/`
- `scripts/`
- `services/`
- `templates/`
- `tools/`
- `ui/`
- `utils/`
- `mcp_server.py`

## Core Directory (`src/core/`)

This is the primary target for refactoring.

- `agents/`
- `ai/`
- `browser/`
- `cache/`
- `concurrency/`
- `config/`
- `content/`
- `di/`
- `domain/`
- `exceptions/`
- `filesystem/`
- `indexing/`
- `logging/`
- `managers/`
- `models/`
- `network/`
- `output/`
- `persistence/`
- `prompts/`
- `quant/`
- `research/`
- `resilience/`
- `security/`
- `session/`
- `sources/`
- `strategies/`
- `streaming/`
- `tracking/`
- `types/`
- `validation/`
- `workflow/`
- `company_classifier.py`
- `company_probe.py`
- `result.py`

## Tools Directory (`src/tools/`)

- `browser/`
- `data/`
- `framework/`
- `search/`
- `specialized/`

## Graph Directory (`src/graph/`)

- `graph_builder.py` (Monolith)
- `state.py`
- `research_graph.py`
