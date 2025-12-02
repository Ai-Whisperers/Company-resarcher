# [RESOLVED] DOC: Architecture Diagrams

**Status**: RESOLVED
**Original File**: backlog/06-documentation.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Medium
**Description:** Create Mermaid diagrams for the current architecture.

**Acceptance Criteria:**
- [x] Create `docs/architecture/diagrams/system_overview.mermaid`.
- [x] Create `docs/architecture/diagrams/research_flow.mermaid`.

## Resolution

Created comprehensive Mermaid diagrams documenting the system architecture.

### Files Created

1. **`docs/architecture/diagrams/system_overview.mermaid`**
   - High-level system architecture
   - Component relationships and dependencies
   - Layer organization (Entry Points, Core, Pipeline, Agents, Tools, Services, Storage)
   - Security and quality components

2. **`docs/architecture/diagrams/research_flow.mermaid`**
   - Detailed research request flow
   - Input handling (CLI, API, UI)
   - Planning phase with query generation
   - Search and collection process
   - Analysis and synthesis pipeline
   - Report generation with critic feedback loop
   - Output formatting and storage
   - Monitoring integration

### Diagram Components

#### System Overview
- **Entry Points**: CLI, FastAPI, Streamlit UI
- **Core**: Configuration, DI Container, Logger
- **Pipeline**: Orchestrator, Research/Analyze/Search stages
- **Agents**: Deep Research, Specialists, Writer, Critic
- **AI Clients**: Cached, Cost-tracked, Rate-limited wrappers
- **Tools**: Search Manager, Browser, YouTube, Financial Data
- **Providers**: Serper, DuckDuckGo, Tavily, Jina, LangSearch
- **Services**: Vault, Source Registry, Output Manager, Gap Analyzer
- **Security**: URL Validator, Circuit Breaker, Concurrency Manager
- **Storage**: File System, SQLite, Vector Store

#### Research Flow
- Complete request lifecycle from input to output
- Error handling and retry paths
- Gap analysis feedback loops
- Cost tracking integration
- Multi-format output support

### Viewing the Diagrams

Mermaid diagrams can be viewed in:
- GitHub (renders automatically in .md files)
- VS Code with Mermaid extension
- Mermaid Live Editor (https://mermaid.live)
- Any Mermaid-compatible documentation tool

### Example Usage in Markdown

```markdown
## System Architecture

```mermaid
graph TB
    %% Include content from system_overview.mermaid
```
```
