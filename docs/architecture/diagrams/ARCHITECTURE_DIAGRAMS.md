# Architecture Diagrams

Visual representations of the Company Researcher system architecture.

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Clients["Client Layer"]
        CLI[CLI<br/>main.py]
        API[REST API<br/>FastAPI]
        UI[Streamlit UI]
    end

    subgraph Orchestration["Orchestration Layer"]
        ORCH[ResearchOrchestrator]
        GRAPH[LangGraph StateGraph]
        STATE[ResearchState<br/>Blackboard]
    end

    subgraph Agents["Agent Layer"]
        FIN[FinancialAgent]
        MKT[MarketAnalyst]
        COMP[CompetitorScout]
        BRAND[BrandAuditor]
        SALES[SalesAgent]
        INSIGHT[InsightGenerator]
        WRITER[ReportWriter]
        CRITIC[LogicCritic]
    end

    subgraph Core["Core Services"]
        AI[AI Client<br/>Multi-Provider]
        CACHE[Response Cache]
        RATE[Rate Limiter]
        ROUTER[Smart Router]
    end

    subgraph Tools["Data Tools"]
        BROWSER[Browser<br/>Playwright]
        SEARCH[Search<br/>Tavily/DDG]
        FINANCE[Financial<br/>yfinance]
        NEWS[News<br/>NewsAPI]
        SEC[SEC Filings]
    end

    subgraph Providers["LLM Providers"]
        OPENAI[OpenAI]
        ANTHROPIC[Anthropic]
        GEMINI[Gemini]
        GROQ[Groq]
        OLLAMA[Ollama]
    end

    CLI --> ORCH
    API --> ORCH
    UI --> ORCH

    ORCH --> GRAPH
    GRAPH --> STATE
    STATE --> Agents

    Agents --> Core
    Core --> Tools
    Core --> Providers

    ROUTER --> OPENAI
    ROUTER --> ANTHROPIC
    ROUTER --> GEMINI
    ROUTER --> GROQ
    ROUTER --> OLLAMA
```

## 3-Wave Execution Model

```mermaid
flowchart LR
    subgraph Wave1["Wave 1: Gathering"]
        direction TB
        W1A[FinancialAgent]
        W1B[MarketAnalyst]
        W1C[CompetitorScout]
        W1D[BrandAuditor]
        W1E[SalesAgent]
    end

    subgraph Wave2["Wave 2: Analysis"]
        direction TB
        W2A[InsightGenerator]
        W2B[Cross-Reference Data]
        W2C[Generate Insights]
    end

    subgraph Wave3["Wave 3: Writing"]
        direction TB
        W3A[ReportWriter]
        W3B[LogicCritic]
        W3C[Final Reports]
    end

    INPUT[Company Name<br/>+ Website] --> Wave1
    Wave1 --> Wave2
    Wave2 --> Wave3
    Wave3 --> OUTPUT[20+ Markdown<br/>Reports]

    W1A -.-> |parallel| W1B
    W1B -.-> |parallel| W1C
    W1C -.-> |parallel| W1D
    W1D -.-> |parallel| W1E
```

## Data Flow

```mermaid
flowchart TD
    INPUT[/"Input:<br/>Company Name, URL"/]

    subgraph Gathering["Data Gathering"]
        SEARCH_Q[Generate Search Queries]
        WEB[Web Scraping]
        API_CALLS[API Calls]
        SOURCES[(Source Log)]
    end

    subgraph Processing["Data Processing"]
        EXTRACT[Extract Structured Data]
        VALIDATE[Validate & Clean]
        ENRICH[Enrich with Context]
    end

    subgraph Analysis["Analysis"]
        CROSS[Cross-Reference]
        INSIGHTS[Generate Insights]
        CRITIQUE[Quality Review]
    end

    subgraph Output["Output Generation"]
        TEMPLATES[Jinja2 Templates]
        RENDER[Render Reports]
        SAVE[Save to Disk]
    end

    INPUT --> SEARCH_Q
    SEARCH_Q --> WEB
    SEARCH_Q --> API_CALLS
    WEB --> SOURCES
    API_CALLS --> SOURCES

    SOURCES --> EXTRACT
    EXTRACT --> VALIDATE
    VALIDATE --> ENRICH

    ENRICH --> CROSS
    CROSS --> INSIGHTS
    INSIGHTS --> CRITIQUE

    CRITIQUE --> TEMPLATES
    TEMPLATES --> RENDER
    RENDER --> SAVE

    SAVE --> REPORTS[/"20+ Reports<br/>+ Source Audit"/]
```

## Agent Communication (Blackboard Pattern)

```mermaid
flowchart TB
    subgraph State["ResearchState (Blackboard)"]
        direction LR
        S1[company_name]
        S2[website]
        S3[financial_data]
        S4[market_data]
        S5[competitor_data]
        S6[brand_data]
        S7[sales_data]
        S8[insights]
        S9[drafts]
        S10[errors]
    end

    FA[FinancialAgent] -->|writes| S3
    MA[MarketAnalyst] -->|writes| S4
    CS[CompetitorScout] -->|writes| S5
    BA[BrandAuditor] -->|writes| S6
    SA[SalesAgent] -->|writes| S7

    S3 -->|reads| IG
    S4 -->|reads| IG
    S5 -->|reads| IG
    S6 -->|reads| IG
    S7 -->|reads| IG

    IG[InsightGenerator] -->|writes| S8

    S8 -->|reads| RW[ReportWriter]
    RW -->|writes| S9

    S9 -->|reads| LC[LogicCritic]
    LC -->|writes| S10
```

## AI Client Architecture

```mermaid
flowchart TB
    subgraph Interface["Public Interface"]
        GEN[generate<br/>prompt → response]
    end

    subgraph Layers["Processing Layers"]
        CACHE[CachedAIClient<br/>Response Caching]
        RATE[RateLimitedClient<br/>Request Throttling]
        ROUTER[SmartRouter<br/>Model Selection]
    end

    subgraph Providers["Provider Clients"]
        OAI[OpenAI Client]
        ANT[Anthropic Client]
        GEM[Gemini Client]
        GRQ[Groq Client]
        OLL[Ollama Client]
    end

    GEN --> CACHE
    CACHE -->|cache miss| RATE
    RATE --> ROUTER

    ROUTER -->|complex task| OAI
    ROUTER -->|complex task| ANT
    ROUTER -->|simple task| GRQ
    ROUTER -->|local| OLL
    ROUTER -->|fallback| GEM

    CACHE -->|cache hit| RESP[Response]
    OAI --> RESP
    ANT --> RESP
    GEM --> RESP
    GRQ --> RESP
    OLL --> RESP
```

## API Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as Database
    participant O as Orchestrator
    participant A as Agents
    participant LLM as LLM Providers

    C->>API: POST /api/v1/research
    API->>API: Validate Request
    API->>API: Rate Limit Check
    API->>DB: Create Task (pending)
    API-->>C: {task_id, status: pending}

    API->>O: Background: run_research_task
    O->>DB: Update (in_progress)

    loop Wave 1-3
        O->>A: Execute Agents
        A->>LLM: Generate Response
        LLM-->>A: Response
        A->>O: Update State
    end

    O->>DB: Update (completed, result)

    C->>API: GET /api/v1/research/{task_id}
    API->>DB: Get Task
    DB-->>API: Task Data
    API-->>C: {status: completed, result: {...}}
```

## Output File Structure

```mermaid
flowchart TD
    ROOT[output/CompanyName/]

    ROOT --> S0[00-Strategic-Context/]
    ROOT --> S1[01-Market-Intelligence/]
    ROOT --> S2[02-Target-Audience/]
    ROOT --> S3[03-Competitive-Landscape/]
    ROOT --> S4[04-Brand-Strategy/]
    ROOT --> S5[05-Marketing-Execution/]
    ROOT --> S6[06-Data-Room/]
    ROOT --> S7[07-Creative-Inspiration/]
    ROOT --> S99[99-Sources/]

    S0 --> F01[Company-Overview.md]
    S0 --> F02[Key-People.md]

    S1 --> F11[Market-Size.md]
    S1 --> F12[Industry-Trends.md]

    S6 --> F61[Financials.md]
    S6 --> F62[Statistics.md]

    S99 --> RAW[raw/]
    S99 --> LOG[Source-Log.md]

    RAW --> R1[source-001.md]
    RAW --> R2[source-002.md]
    RAW --> RN[...]
```

## Rendering Diagrams

These diagrams use [Mermaid](https://mermaid.js.org/) syntax. To view:

1. **GitHub**: Renders automatically in markdown files
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Online**: Use [Mermaid Live Editor](https://mermaid.live/)
4. **Export**: Use Mermaid CLI to export as PNG/SVG

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Export to PNG
mmdc -i ARCHITECTURE_DIAGRAMS.md -o diagram.png
```
