# DOC-002: Missing Architecture Documentation

## Priority: Medium
## Category: Documentation
## Status: Backlog

## Summary

The project lacks comprehensive architecture documentation explaining the system design, component interactions, and data flow.

## Current State

- No architecture diagrams
- No component documentation
- No data flow documentation
- Limited code comments explaining design decisions

## Proposed Documentation Structure

### 1. Architecture Overview

```markdown
# docs/architecture/README.md

## System Architecture

### Overview
Company Researcher is an AI-powered research platform that conducts
multi-phase company analysis using large language models and web scraping.

### Key Components

1. **Pipeline Orchestrator**
   - Coordinates research phases
   - Manages timeouts and retries
   - Aggregates results

2. **Research Stages**
   - Market Analysis Stage
   - Financial Analysis Stage
   - Competitor Analysis Stage
   - Brand Analysis Stage
   - Sales Intelligence Stage

3. **AI Client Layer**
   - Multi-provider support (OpenAI, Anthropic, Cohere, Ollama)
   - Caching and rate limiting
   - Smart routing based on task type

4. **Tools**
   - Browser tool (Playwright-based web scraping)
   - Search tool (DuckDuckGo integration)
   - Tech stack detection tool

5. **API Layer**
   - FastAPI REST API
   - Background task processing
   - SQLite persistence
```

### 2. Component Diagrams (Mermaid)

```markdown
# docs/architecture/diagrams/system-overview.md

graph TB
    subgraph "API Layer"
        API[FastAPI App]
        DB[(SQLite)]
    end

    subgraph "Orchestration"
        PO[Pipeline Orchestrator]
        RP[Research Pipeline]
    end

    subgraph "Stages"
        MS[Market Stage]
        FS[Financial Stage]
        CS[Competitor Stage]
        BS[Brand Stage]
        SS[Sales Stage]
    end

    subgraph "AI Layer"
        AC[AI Client]
        Cache[Response Cache]
        Router[Smart Router]
    end

    subgraph "Providers"
        OpenAI
        Anthropic
        Cohere
        Ollama
    end

    API --> PO
    PO --> RP
    RP --> MS & FS & CS & BS & SS
    MS & FS & CS & BS & SS --> AC
    AC --> Cache
    AC --> Router
    Router --> OpenAI & Anthropic & Cohere & Ollama
```

### 3. Data Flow Documentation

```markdown
# docs/architecture/data-flow.md

## Research Request Flow

1. Client sends POST /api/v1/research
2. API creates task in database (status: pending)
3. Background task starts PipelineOrchestrator
4. Orchestrator creates RequestContext with timeout
5. ResearchPipeline executes stages (parallel or sequential)
6. Each stage:
   a. Searches for relevant information
   b. Scrapes web pages if needed
   c. Sends prompt to AI for analysis
   d. Returns structured result
7. Orchestrator aggregates stage results
8. Task updated in database (status: completed)
9. Client polls GET /api/v1/research/{task_id}
```

## Implementation Tasks

- [ ] Create `docs/architecture/` directory
- [ ] Write system overview document
- [ ] Create Mermaid diagrams for each component
- [ ] Document data flow for main use cases
- [ ] Add ADR (Architecture Decision Records) template
- [ ] Document design decisions and trade-offs
- [ ] Add deployment architecture diagram

## Success Criteria

- Clear system overview for new developers
- Visual diagrams of component relationships
- Data flow documented for main operations
- Design decisions explained
- Easy onboarding for contributors
