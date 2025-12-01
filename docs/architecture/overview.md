# Company Researcher Architecture

This document provides a comprehensive overview of the Company Researcher system architecture, including component diagrams, data flows, and key design patterns.

## System Overview

The Company Researcher is a multi-agent autonomous research platform that generates deep B2B and investment intelligence reports. The system follows a pipeline architecture with specialized agents for different research domains.

```mermaid
graph TB
    subgraph "Entry Points"
        CLI[CLI - main.py]
        API[REST API - FastAPI]
        UI[Streamlit UI]
    end

    subgraph "Orchestration Layer"
        PO[Pipeline Orchestrator]
        RP[Research Pipeline]
        CTX[Request Context]
    end

    subgraph "Agent Layer"
        BA[Base Agent]
        MA[Market Analyst]
        FA[Financial Agent]
        CS[Competitor Scout]
        BAU[Brand Auditor]
        SA[Sales Agent]
    end

    subgraph "Tool Layer"
        ST[Search Tool]
        BT[Browser Tool]
        FDT[Financial Data Tool]
        SEC[SEC Tool]
        NA[News Aggregator]
    end

    subgraph "Services Layer"
        AIC[AI Client Manager]
        ST2[Source Tracker]
        HC[HTML Cache]
        GS[Grounding Service]
    end

    subgraph "Data Layer"
        DB[(SQLite/PostgreSQL)]
        FS[File System]
        Cache[Cache Store]
    end

    CLI --> PO
    API --> PO
    UI --> PO

    PO --> RP
    RP --> CTX
    RP --> MA & FA & CS & BAU & SA

    MA & FA & CS & BAU & SA --> BA
    BA --> ST & BT
    BA --> AIC

    ST --> HC
    BT --> HC
    AIC --> Cache

    API --> DB
    PO --> FS
    ST2 --> FS
```

## Component Architecture

### Core Components

```mermaid
classDiagram
    class Settings {
        +Profile profile
        +AIConfig ai
        +RuntimeConfig runtime
        +CacheConfig cache
        +validate_config() list
        +has_any_ai_provider() bool
    }

    class PipelineOrchestrator {
        -ResearchPipelineConfig config
        -ResearchPipeline pipeline
        +conduct_research(company, url) dict
        +research_single_phase() dict
    }

    class ResearchPipeline {
        -ResearchPipelineConfig config
        +research(company, ctx) PipelineResult
        +research_single() PipelineResult
    }

    class BaseAgent {
        -SearchTool search_tool
        -BrowserTool browser_tool
        -AIClientManager ai_client
        +run(queries, context) AgentResult
        +_execute_single_query() str
    }

    class AIClientManager {
        -dict providers
        -str primary
        -str fallback
        +generate(prompt, model) Result
        +stream(prompt) AsyncIterator
    }

    Settings --> PipelineOrchestrator
    PipelineOrchestrator --> ResearchPipeline
    ResearchPipeline --> BaseAgent
    BaseAgent --> AIClientManager
```

### API Layer

```mermaid
classDiagram
    class FastAPI {
        +lifespan()
        +middleware()
    }

    class ResearchRequest {
        +str company_name
        +HttpUrl url
        +str industry
        +str country
    }

    class Task {
        +str task_id
        +str status
        +str request
        +str result
        +str error
        +datetime created_at
    }

    class RateLimiter {
        -int requests_per_minute
        -dict requests
        +is_allowed(ip) bool
    }

    FastAPI --> ResearchRequest
    FastAPI --> Task
    FastAPI --> RateLimiter
```

## Data Flow

### Research Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Orchestrator
    participant Pipeline
    participant Agents
    participant Tools
    participant AI

    Client->>API: POST /api/v1/research
    API->>API: Validate Request
    API->>API: Verify API Key
    API->>DB: Save Task (pending)
    API-->>Client: 200 OK (task_id)

    API->>Orchestrator: Background Task
    Orchestrator->>DB: Update Status (in_progress)
    Orchestrator->>Pipeline: conduct_research()

    loop For Each Research Phase
        Pipeline->>Agents: Execute Phase
        Agents->>Tools: Search & Fetch
        Tools->>Tools: Cache Results
        Agents->>AI: Generate Analysis
        AI-->>Agents: Response
        Agents-->>Pipeline: Phase Result
    end

    Pipeline-->>Orchestrator: Research Result
    Orchestrator->>DB: Save Result (completed)

    Client->>API: GET /api/v1/research/{task_id}
    API->>DB: Get Task
    DB-->>API: Task Data
    API-->>Client: 200 OK (results)
```

### Search Provider Fallback

```mermaid
flowchart TD
    A[Search Query] --> B{DuckDuckGo}
    B -->|Success| Z[Return Results]
    B -->|Fail/Rate Limit| C{Jina AI}
    C -->|Success| Z
    C -->|Fail/Rate Limit| D{Serper.dev}
    D -->|Success| Z
    D -->|Fail/Rate Limit| E{Tavily}
    E -->|Success| Z
    E -->|All Failed| F[Return Empty]
```

## Pipeline Architecture

### Research Pipeline Stages

```mermaid
flowchart LR
    subgraph Input
        CP[Company Profile]
        CTX[Request Context]
    end

    subgraph "Research Phases (Parallel)"
        M[Market Phase]
        F[Financial Phase]
        C[Competitor Phase]
        B[Brand Phase]
        S[Sales Phase]
    end

    subgraph Output
        PR[Phase Results]
        SR[Source Registry]
        MD[Markdown Files]
    end

    CP --> M & F & C & B & S
    CTX --> M & F & C & B & S
    M & F & C & B & S --> PR
    PR --> SR
    PR --> MD
```

### Agent Execution Flow

```mermaid
flowchart TD
    A[Agent.run] --> B[Generate Queries]
    B --> C{Parallel Execution}
    C --> D1[Query 1]
    C --> D2[Query 2]
    C --> D3[Query N]

    D1 & D2 & D3 --> E[Search Tool]
    E --> F[Filter Results]
    F --> G[Browser Tool]
    G --> H[Extract Content]
    H --> I[AI Analysis]
    I --> J[Format Output]
    J --> K[Return Result]
```

## Directory Structure

```
company-researcher/
├── src/
│   ├── agents/           # AI agents for research
│   │   ├── base_agent.py     # Abstract base class
│   │   ├── specialists.py    # Domain-specific agents
│   │   └── deep_research.py  # Recursive research
│   ├── api/              # REST API
│   │   ├── app.py           # FastAPI application
│   │   ├── models.py        # Request/Response models
│   │   └── database.py      # Database config
│   ├── core/             # Core utilities
│   │   ├── config.py        # Configuration
│   │   ├── ai_client.py     # LLM provider abstraction
│   │   ├── types.py         # Data models
│   │   └── logger.py        # Logging
│   ├── pipeline/         # Orchestration
│   │   ├── orchestrator.py  # Main orchestrator
│   │   ├── research_pipeline.py
│   │   └── stages/          # Pipeline stages
│   ├── tools/            # External integrations
│   │   ├── search_tool.py   # Search interface
│   │   ├── browser.py       # Web scraping
│   │   └── search/          # Search providers
│   ├── services/         # Business logic
│   │   ├── source_tracker.py
│   │   ├── html_cache.py
│   │   └── grounding_service.py
│   └── prompts/          # LLM prompt templates
├── docs/
│   ├── api/              # API documentation
│   ├── architecture/     # Architecture docs
│   └── guides/           # User guides
├── tests/                # Test suite
└── outputs/              # Generated reports
```

## Key Design Patterns

### 1. Pipeline Pattern
The system uses an explicit pipeline architecture instead of LangGraph's state machine:
- **Stages**: Each research phase is a discrete stage
- **Context**: Shared state via `RequestContext`
- **Results**: Typed `PipelineResult` with status

### 2. Provider Chain (Fallback)
Both AI and search components use fallback chains:
```python
# Search: DuckDuckGo -> Jina -> Serper -> Tavily
# AI: Primary Provider -> Fallback Provider -> Ollama
```

### 3. Result Type (Rust-style)
Explicit error handling without exceptions:
```python
result = await search_tool.search_safe(query)
if result.is_ok:
    process(result.unwrap())
else:
    handle_error(result.unwrap_err())
```

### 4. Dependency Injection
Loose coupling via container:
```python
container.register(SearchTool, lifecycle=Lifecycle.SINGLETON)
search_tool = container.resolve(SearchTool)
```

### 5. Profile-Based Configuration
Environment-specific defaults:
- **Development**: Debug logging, 3 search results
- **Staging**: Info logging, 5 search results
- **Production**: Warning logging, 10 search results

## Security Architecture

```mermaid
flowchart TD
    subgraph "Request Security"
        A[Request] --> B[Rate Limiter]
        B --> C[Size Limit 64KB]
        C --> D[API Key Validation]
        D --> E[Input Validation]
    end

    subgraph "URL Security"
        E --> F[URL Validator]
        F --> G{Private IP?}
        G -->|Yes| H[Block SSRF]
        G -->|No| I[Allow Request]
    end

    subgraph "Data Security"
        I --> J[SQL Injection Prevention]
        J --> K[Constant-Time Auth]
        K --> L[SecretStr for Keys]
    end
```

## Performance Considerations

| Component | Strategy | Default |
|-----------|----------|---------|
| Search | Multi-provider fallback | DuckDuckGo first |
| Browser | Semaphore rate limiting | 5 concurrent |
| AI | Response caching | 1 hour TTL |
| Pipeline | Parallel phase execution | Enabled |
| Database | Connection pooling | SQLAlchemy pool |

## Monitoring & Observability

- **Request ID**: Unique ID per request for tracing
- **Structured Logging**: JSON-formatted logs with context
- **Health Checks**: `/health` and `/health/detailed` endpoints
- **Error Tracking**: Langfuse integration (optional)

## Related Documentation

- [API Reference](../api/openapi.yaml) - OpenAPI specification
- [Deployment Guide](../guides/DEPLOYMENT.md) - Production deployment
- [Troubleshooting](../guides/TROUBLESHOOTING.md) - Common issues
- [Configuration](../guides/CONFIGURATION.md) - Environment variables
