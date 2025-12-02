# Architecture Overview

Company Researcher is an AI-powered research platform that conducts multi-phase company analysis using large language models and web scraping.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  CLI (main.py)          │  REST API (FastAPI)      │  Streamlit UI           │
└────────────┬────────────┴───────────┬──────────────┴───────────┬────────────┘
             │                        │                          │
             └────────────────────────┼──────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Pipeline Layer                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  PipelineOrchestrator    →    ResearchPipeline    →    Research Stages      │
│  - Timeout management         - Stage execution        - Market Analysis     │
│  - Error handling             - Result aggregation     - Financial Analysis  │
│  - Progress tracking          - Parallel/Sequential    - Competitor Analysis │
│                                                        - Brand Analysis      │
│                                                        - Sales Intelligence  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agent Layer                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  BaseAgent                                                                    │
│  ├── MarketAnalyst          - Market size, trends, growth analysis           │
│  ├── FinancialAnalyst       - Revenue, funding, financial health            │
│  ├── CompetitorAnalyst      - Competitor identification and comparison      │
│  ├── BrandAnalyst           - Brand positioning, perception, strategy       │
│  └── SalesIntelligenceAgent - Sales strategy, channels, opportunities       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Core Layer                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  AIClientManager          │  SearchTool            │  BrowserTool            │
│  - Multi-provider support │  - DuckDuckGo          │  - Playwright           │
│  - Circuit breaker        │  - Serper.dev          │  - Content extraction   │
│  - Fallback chain         │  - Tavily              │  - JavaScript rendering │
│  - Smart routing          │  - Rate limiting       │  - Parallel fetching    │
├───────────────────────────┼────────────────────────┼─────────────────────────┤
│  CircuitBreaker           │  RetryStrategy         │  TimeoutBudget          │
│  - Failure detection      │  - Exponential backoff │  - Budget tracking      │
│  - State management       │  - Jitter              │  - Sub-budget creation  │
│  - Recovery logic         │  - Policy-based retry  │  - Time allocation      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Storage Layer                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  SQLite (tasks.db)        │  File System (outputs/) │  Vault (data/vault/)   │
│  - Task tracking          │  - Research reports     │  - HTML cache          │
│  - Request history        │  - Markdown files       │  - Search results      │
│  - Status management      │  - Source tracking      │  - Vector embeddings   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Pipeline Orchestrator

**Location:** `src/pipeline/orchestrator.py`

Coordinates the entire research workflow:
- Creates `RequestContext` with timeout budgets
- Manages stage execution (parallel or sequential)
- Handles errors and timeouts gracefully
- Aggregates results from all stages

### 2. Research Stages

**Location:** `src/pipeline/stages/`

Each stage is responsible for a specific research domain:

| Stage | Agent | Output |
|-------|-------|--------|
| Market | MarketAnalyst | Market size, trends, growth |
| Financial | FinancialAnalyst | Revenue, funding, financials |
| Competitor | CompetitorAnalyst | Competitor analysis |
| Brand | BrandAnalyst | Brand positioning |
| Sales | SalesIntelligenceAgent | Sales intelligence |

### 3. AI Client Layer

**Location:** `src/core/ai_client.py`

Multi-provider AI client with resilience patterns:
- **Providers:** OpenAI, Anthropic, Gemini, Groq
- **Smart Router:** Routes requests based on complexity
- **Circuit Breaker:** Prevents cascading failures
- **Fallback Chain:** Tries all providers before failing

### 4. Tools

**Location:** `src/tools/`

| Tool | Purpose |
|------|---------|
| SearchTool | Web search via DuckDuckGo, Serper, Tavily |
| BrowserTool | Web scraping via Playwright |
| PDFParser | PDF content extraction |
| TechStackDetector | Technology detection |

### 5. Reliability Patterns

**Location:** `src/core/`

- **Circuit Breaker:** `circuit_breaker.py` - Prevents cascading failures
- **Retry Strategy:** `retry_strategy.py` - Exponential backoff with jitter
- **Timeout Budget:** Tracks time across pipeline stages

## Data Flow

### Research Request Flow

```
1. Client sends POST /api/v1/research
   └── Request: { company: "Example Corp", url: "https://example.com" }

2. API validates request and creates task
   └── Task stored in SQLite with status: "pending"

3. Background task starts PipelineOrchestrator
   └── Creates RequestContext with 30-minute timeout

4. ResearchPipeline executes stages (parallel by default)
   ├── Market Stage
   │   ├── Generate search queries
   │   ├── Execute searches (DuckDuckGo)
   │   ├── Fetch page content (Playwright)
   │   └── Analyze with AI (OpenAI/etc)
   ├── Financial Stage (same pattern)
   ├── Competitor Stage (same pattern)
   ├── Brand Stage (same pattern)
   └── Sales Stage (same pattern)

5. Results aggregated and saved
   ├── Markdown files → outputs/{company}/
   ├── Task status → tasks.db (completed)
   └── Source cache → data/vault/

6. Client polls GET /api/v1/research/{task_id}
   └── Returns: { status: "completed", result: {...} }
```

### AI Request Flow

```
1. Agent calls ai.generate(prompt)

2. AIClientManager.generate()
   ├── Select client via smart router
   ├── Check circuit breaker state
   └── Execute with retry strategy

3. If primary fails:
   ├── Record failure in circuit breaker
   ├── Try next provider in fallback chain
   └── Continue until success or all fail

4. Return response or raise error
```

## Configuration

### Environment Variables

See `.env.example` for full list. Key categories:
- **AI:** Provider API keys, model selection
- **Search:** Search provider keys, timeouts
- **Performance:** Concurrent queries, timeouts
- **Security:** API key, injection blocking

### Configurable Behaviors

| Config | Default | Description |
|--------|---------|-------------|
| `AGENT_MAX_CONCURRENT_QUERIES` | 5 | Parallel search queries |
| `LLM_TIMEOUT_SECONDS` | 120 | AI request timeout |
| `SEARCH_TIMEOUT_SECONDS` | 30 | Search timeout |
| `SHUTDOWN_TIMEOUT_SECONDS` | 30 | Graceful shutdown wait |

## Extension Points

### Adding a New Research Stage

1. Create agent in `src/agents/`:
   ```python
   class NewAnalyst(BaseAgent):
       async def research(self, company: CompanyProfile) -> ResearchPhaseResult:
           ...
   ```

2. Create stage in `src/pipeline/stages/`:
   ```python
   class NewStage(BaseResearchStage):
       async def execute(self, context: PipelineContext) -> StageResult:
           ...
   ```

3. Register in pipeline configuration

### Adding a New AI Provider

1. Create client in `src/core/ai_clients/`:
   ```python
   class NewProviderClient(BaseAIClient):
       async def generate(self, prompt: str, ...) -> str:
           ...
   ```

2. Register in `AIClientManager._initialize_clients()`

### Adding a New Search Provider

1. Create provider in `src/tools/search/`:
   ```python
   class NewSearchProvider(BaseSearchProvider):
       async def search(self, query: str, ...) -> List[SearchResult]:
           ...
   ```

2. Register in search manager

## Related Documentation

- [Deployment Guide](../deployment.md)
- [Troubleshooting Guide](../troubleshooting.md)
- [API Documentation](http://localhost:8000/docs)
