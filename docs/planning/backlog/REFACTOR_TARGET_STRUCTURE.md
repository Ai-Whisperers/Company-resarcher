# Target Directory Structure After Refactoring

## Complete Tree Structure

```
src/
├── __init__.py
│
├── core/                              # Foundation layer
│   ├── __init__.py
│   │
│   ├── config/                        # [NEW] Centralized configuration
│   │   ├── __init__.py               # Public exports, get_config()
│   │   ├── base.py                   # BaseConfig, ConfigLoader, ConfigProfile
│   │   ├── providers.py              # AIProviderConfig, OpenAIConfig, AnthropicConfig, etc.
│   │   ├── services.py               # CacheConfig, SearchConfig, BrowserConfig
│   │   ├── pipeline.py               # PipelineConfig, ResearchConfig, GraphConfig
│   │   ├── database.py               # DatabaseConfig, RedisConfig
│   │   ├── server.py                 # ServerConfig, CORSConfig
│   │   ├── defaults.py               # All default values (replaces constants.py)
│   │   └── validator.py              # ConfigValidator for startup validation
│   │
│   ├── di/                            # [NEW] Dependency Injection
│   │   ├── __init__.py               # Public exports, get_container()
│   │   ├── container.py              # Enhanced DI container
│   │   ├── decorators.py             # @singleton, @transient, @scoped
│   │   ├── lifecycle.py              # ServiceLifecycle (startup/shutdown)
│   │   └── providers.py              # ServiceProvider, lazy initialization
│   │
│   ├── managers/                      # [NEW] Manager base classes
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseManager abstract class
│   │   ├── state_manager.py          # StateManager[T] - mutable state
│   │   ├── factory_manager.py        # FactoryManager[T] - instance creation
│   │   ├── service_manager.py        # ServiceManager[T] - service provision
│   │   └── orchestrator.py           # Orchestrator - coordination
│   │
│   ├── providers/                     # [NEW] Provider chain abstraction
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseProvider, ProviderResult
│   │   ├── chain.py                  # ProviderChain[T] - fallback logic
│   │   ├── registry.py               # ProviderRegistry[T] - discovery
│   │   ├── strategies.py             # RoundRobin, Priority, CostOptimized
│   │   └── health.py                 # HealthChecker, HealthStatus
│   │
│   ├── resilience/                    # [NEW] Unified resilience patterns
│   │   ├── __init__.py
│   │   ├── retry.py                  # RetryPolicy, RetryExecutor
│   │   ├── circuit_breaker.py        # CircuitBreaker, CircuitBreakerPolicy
│   │   ├── fallback.py               # FallbackPolicy, FallbackExecutor
│   │   ├── timeout.py                # TimeoutPolicy, AdaptiveTimeout
│   │   ├── bulkhead.py               # BulkheadPolicy (concurrency limiting)
│   │   ├── executor.py               # ResilientExecutor (composable)
│   │   └── decorators.py             # @resilient, @retry, @circuit_breaker
│   │
│   ├── validation/                    # [NEW] Validation framework
│   │   ├── __init__.py
│   │   ├── base.py                   # ValidationRule, ValidationResult
│   │   ├── registry.py               # ValidatorRegistry
│   │   ├── chain.py                  # ValidationChain
│   │   ├── rules/
│   │   │   ├── __init__.py
│   │   │   ├── common.py             # Range, Pattern, Required, Length
│   │   │   ├── business.py           # CompanyName, Industry, Domain
│   │   │   ├── financial.py          # Currency, Percentage, MarketCap
│   │   │   └── content.py            # URL, HTML, JSON validation
│   │   └── decorators.py             # @validated decorator
│   │
│   ├── ai/                            # [REORGANIZED] AI client layer
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseAIClient abstract
│   │   ├── manager.py                # AIClientManager
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── openai.py             # OpenAIClient
│   │   │   ├── anthropic.py          # AnthropicClient
│   │   │   ├── gemini.py             # GeminiClient
│   │   │   ├── groq.py               # GroqClient
│   │   │   ├── ollama.py             # OllamaClient
│   │   │   └── mock.py               # MockClient
│   │   ├── wrappers/
│   │   │   ├── __init__.py
│   │   │   ├── cached.py             # CachedAIClient
│   │   │   ├── cost_tracked.py       # CostTrackedClient
│   │   │   └── rate_limited.py       # RateLimitedClient
│   │   ├── routing/
│   │   │   ├── __init__.py
│   │   │   └── smart_router.py       # SmartRouter
│   │   └── features/
│   │       ├── __init__.py
│   │       ├── query_planner.py      # AIQueryPlanner
│   │       ├── gap_analyzer.py       # AIGapAnalyzer
│   │       ├── relevance_scorer.py   # AIRelevanceScorer
│   │       ├── entity_extractor.py   # AIEntityExtractor
│   │       └── contradiction_resolver.py
│   │
│   ├── cache/                         # [REORGANIZED] Caching layer
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseCache abstract
│   │   ├── file_cache.py             # FileCache (JSON-based)
│   │   ├── redis_cache.py            # RedisCache
│   │   ├── semantic_cache.py         # SemanticCache (vector-based)
│   │   └── manager.py                # CacheManager
│   │
│   ├── exceptions/                    # [REORGANIZED] Exception hierarchy
│   │   ├── __init__.py               # Public exports
│   │   ├── base.py                   # CompanyResearcherError
│   │   ├── ai.py                     # AIError, AIProviderError, etc.
│   │   ├── network.py                # NetworkError, TimeoutError, etc.
│   │   ├── validation.py             # ValidationError, etc.
│   │   ├── search.py                 # SearchError, etc.
│   │   └── pipeline.py               # PipelineError, StageError, etc.
│   │
│   ├── logging/                       # [REORGANIZED] Logging
│   │   ├── __init__.py
│   │   ├── logger.py                 # setup_logger, get_logger
│   │   ├── formatters.py             # Custom formatters
│   │   └── handlers.py               # Custom handlers
│   │
│   ├── types/                         # [REORGANIZED] Type definitions
│   │   ├── __init__.py
│   │   ├── base.py                   # Base TypedDicts
│   │   ├── research.py               # ResearchContext, ResearchResult
│   │   ├── financial.py              # FinancialData, MarketData
│   │   ├── ai.py                     # AIRequest, AIResponse
│   │   └── analysis.py               # SWOT, StrategicInsights
│   │
│   └── models/                        # [REORGANIZED] Domain models
│       ├── __init__.py
│       ├── company.py                # CompanyProfile, CompanyInfo
│       ├── research.py               # ResearchPhaseResult, ResearchSource
│       ├── financial.py              # FinancialData, MarketData
│       └── context.py                # TypedResearchContext
│
├── agents/                            # Agent layer
│   ├── __init__.py
│   │
│   ├── framework/                     # [NEW] Agent framework
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseAgent (enhanced)
│   │   ├── mixins.py                 # ToolMixin, RetryMixin, CacheMixin
│   │   ├── pool.py                   # AgentPool - resource pooling
│   │   └── coordinator.py            # AgentCoordinator - multi-agent
│   │
│   ├── research/                      # Research agents
│   │   ├── __init__.py
│   │   ├── generic.py                # GenericAgent
│   │   ├── specialist.py             # Specialist
│   │   ├── sector.py                 # SectorAnalyst
│   │   └── deep.py                   # DeepResearch
│   │
│   ├── analysis/                      # Analysis agents
│   │   ├── __init__.py
│   │   ├── reasoning.py              # Reasoning
│   │   ├── critic.py                 # Critic
│   │   └── insight.py                # InsightGenerator
│   │
│   ├── output/                        # Output agents
│   │   ├── __init__.py
│   │   └── writer.py                 # Writer
│   │
│   └── orchestration/                 # Orchestration
│       ├── __init__.py
│       ├── orchestrator.py           # Orchestrator
│       └── factory.py                # AgentFactory
│
├── tools/                             # Tool layer
│   ├── __init__.py
│   │
│   ├── framework/                     # [NEW] Tool framework
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseTool[TInput, TOutput]
│   │   ├── registry.py               # ToolRegistry
│   │   ├── config.py                 # ToolConfig base
│   │   ├── errors.py                 # ToolError hierarchy
│   │   ├── metrics.py                # ToolMetrics
│   │   └── middleware.py             # ToolMiddleware (retry, cache, etc.)
│   │
│   ├── search/                        # Search tools
│   │   ├── __init__.py
│   │   ├── base.py                   # SearchProvider base
│   │   ├── manager.py                # SearchManager (uses ProviderChain)
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── tavily.py             # TavilySearchTool
│   │   │   ├── duckduckgo.py         # DuckduckgoSearchTool
│   │   │   ├── brave.py              # BraveSearchTool
│   │   │   ├── serper.py             # SerperSearchTool
│   │   │   ├── jina.py               # JinaSearchTool
│   │   │   ├── langsearch.py         # LangsearchTool
│   │   │   └── bing.py               # BingSearchTool
│   │   └── fallback.py               # SearchFallback (uses ProviderChain)
│   │
│   ├── browser/                       # Browser tools
│   │   ├── __init__.py
│   │   ├── base.py                   # BrowserTool base
│   │   ├── manager.py                # BrowserManager
│   │   ├── pool.py                   # BrowserPool
│   │   ├── navigator.py              # BrowserNavigator
│   │   └── extractor.py              # ContentExtractor
│   │
│   ├── data/                          # Data tools
│   │   ├── __init__.py
│   │   ├── financial/
│   │   │   ├── __init__.py
│   │   │   ├── alpha_vantage.py      # AlphaVantageTool
│   │   │   ├── sec_filings.py        # SECFilingsTool
│   │   │   └── bond_yields.py        # BondYieldsTool
│   │   ├── market/
│   │   │   ├── __init__.py
│   │   │   ├── stock_data.py         # StockDataTool
│   │   │   └── metrics.py            # FinancialMetricsTool
│   │   ├── company/
│   │   │   ├── __init__.py
│   │   │   ├── linkedin.py           # LinkedInTool
│   │   │   ├── glassdoor.py          # GlassdoorTool
│   │   │   └── crunchbase.py         # CrunchbaseTool
│   │   └── content/
│   │       ├── __init__.py
│   │       ├── pdf_parser.py         # PDFParserTool
│   │       └── news_aggregator.py    # NewsAggregatorTool
│   │
│   └── specialized/                   # Specialized tools
│       ├── __init__.py
│       ├── chart.py                  # ChartGenerationTool
│       ├── code_review.py            # CodeReviewTool
│       ├── tech_stack.py             # TechStackAnalyzerTool
│       ├── patent.py                 # PatentTool
│       └── local_search.py           # LocalSearchTool
│
├── services/                          # Service layer
│   ├── __init__.py
│   ├── base.py                       # BaseService abstract class
│   │
│   ├── ai/                            # AI services
│   │   ├── __init__.py
│   │   ├── embedding.py              # EmbeddingService
│   │   ├── semantic_cache.py         # SemanticCacheService
│   │   └── query_optimizer.py        # QueryOptimizerService
│   │
│   ├── research/                      # Research services
│   │   ├── __init__.py
│   │   ├── deep_research.py          # DeepResearchService
│   │   ├── incremental.py            # IncrementalResearchService
│   │   ├── iterative.py              # IterativeResearchService
│   │   └── gap_analyzer.py           # GapAnalyzerService
│   │
│   ├── quality/                       # Quality services
│   │   ├── __init__.py
│   │   ├── assessor.py               # QualityAssessorService
│   │   ├── source_scorer.py          # SourceQualityScorerService
│   │   ├── fact_verifier.py          # FactVerifierService
│   │   └── contradiction_detector.py # ContradictionDetectorService
│   │
│   ├── content/                       # Content services
│   │   ├── __init__.py
│   │   ├── extractor.py              # ContentExtractorService
│   │   ├── compressor.py             # ContextCompressorService
│   │   └── html_cache.py             # HTMLCacheService
│   │
│   ├── data/                          # Data services
│   │   ├── __init__.py
│   │   ├── source_registry.py        # SourceRegistryService
│   │   ├── source_tracker.py         # SourceTrackerService
│   │   └── reprocessor.py            # SourceReprocessorService
│   │
│   └── security/                      # Security services
│       ├── __init__.py
│       ├── encryption.py             # EncryptionService
│       └── security.py               # SecurityService
│
├── pipeline/                          # Pipeline layer
│   ├── __init__.py
│   │
│   ├── core/                          # [NEW] Pipeline core
│   │   ├── __init__.py
│   │   ├── stage.py                  # Stage[TIn, TOut] base class
│   │   ├── context.py                # RequestContext (enhanced)
│   │   ├── builder.py                # PipelineBuilder fluent API
│   │   ├── executor.py               # PipelineExecutor
│   │   └── checkpoint.py             # CheckpointManager
│   │
│   ├── stages/                        # Pipeline stages
│   │   ├── __init__.py
│   │   ├── search/
│   │   │   ├── __init__.py
│   │   │   ├── stage.py              # SearchStage
│   │   │   ├── query_builder.py      # QueryBuilder
│   │   │   ├── executor.py           # SearchExecutor
│   │   │   └── result_processor.py   # ResultProcessor
│   │   ├── fetch/
│   │   │   ├── __init__.py
│   │   │   ├── stage.py              # FetchStage
│   │   │   ├── content_fetcher.py    # ContentFetcher
│   │   │   └── content_parser.py     # ContentParser
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── stage.py              # ResearchStage (~150 lines)
│   │   │   ├── analyzer.py           # ContentAnalyzer (~200 lines)
│   │   │   ├── synthesizer.py        # InformationSynthesizer (~200 lines)
│   │   │   ├── validator.py          # ResultValidator (~150 lines)
│   │   │   ├── prompts.py            # ResearchPrompts (~100 lines)
│   │   │   └── models.py             # ResearchModels (~100 lines)
│   │   ├── analyze/
│   │   │   ├── __init__.py
│   │   │   ├── stage.py              # AnalyzeStage
│   │   │   └── processors.py         # PostProcessors
│   │   └── evaluate/
│   │       ├── __init__.py
│   │       ├── stage.py              # EvaluateStage
│   │       └── metrics.py            # EvaluationMetrics
│   │
│   └── orchestration/                 # Pipeline orchestration
│       ├── __init__.py
│       ├── pipeline.py               # MainPipeline
│       ├── comprehensive.py          # ComprehensiveResearchPipeline
│       ├── smart_executor.py         # SmartParallelExecutor
│       └── orchestrator.py           # PipelineOrchestrator
│
├── graph/                             # LangGraph layer
│   ├── __init__.py
│   │
│   ├── builder/                       # [NEW] Graph building
│   │   ├── __init__.py
│   │   ├── graph.py                  # GraphBuilder main (~300 lines)
│   │   ├── nodes.py                  # NodeDefinitions (~400 lines)
│   │   ├── edges.py                  # EdgeDefinitions (~300 lines)
│   │   ├── conditions.py             # ConditionalRouting (~200 lines)
│   │   └── error_handlers.py         # ErrorHandlerNodes (~200 lines)
│   │
│   ├── state/                         # [NEW] State management
│   │   ├── __init__.py
│   │   ├── schema.py                 # StateSchema TypedDict (~300 lines)
│   │   ├── validators.py             # StateValidators (~200 lines)
│   │   ├── transitions.py            # StateTransitions (~200 lines)
│   │   └── persistence.py            # StatePersistence (~150 lines)
│   │
│   └── workflow/                      # Workflow execution
│       ├── __init__.py
│       ├── definitions.py            # WorkflowDefinitions
│       └── executor.py               # WorkflowExecutor
│
├── api/                               # API layer
│   ├── __init__.py
│   ├── app.py                        # FastAPI setup (~100 lines)
│   │
│   ├── routers/                       # [NEW] API routers
│   │   ├── __init__.py
│   │   ├── research.py               # Research endpoints
│   │   ├── companies.py              # Company endpoints
│   │   ├── sources.py                # Source endpoints
│   │   ├── health.py                 # Health check endpoints
│   │   └── admin.py                  # Admin endpoints
│   │
│   ├── models/                        # API models
│   │   ├── __init__.py
│   │   ├── requests.py               # Request models
│   │   └── responses.py              # Response models
│   │
│   ├── dependencies.py               # FastAPI dependencies
│   │
│   ├── middleware/                    # Middleware
│   │   ├── __init__.py
│   │   ├── security.py               # SecurityMiddleware
│   │   └── tracing.py                # TracingMiddleware
│   │
│   └── database/                      # Database
│       ├── __init__.py
│       ├── connection.py             # Database connection
│       └── models.py                 # ORM models
│
├── mcp/                               # MCP layer (unchanged)
│   ├── __init__.py
│   ├── server.py
│   └── handlers.py
│
├── data/                              # Data layer (unchanged)
│   ├── __init__.py
│   ├── models.py
│   └── pipeline.py
│
├── evaluation/                        # Evaluation layer (unchanged)
│   ├── __init__.py
│   └── evaluator.py
│
├── plugins/                           # Plugin layer (unchanged)
│   ├── __init__.py
│   └── manager.py
│
├── prompts/                           # Prompts (unchanged)
│   └── templates/
│
├── templates/                         # Templates (unchanged)
│   └── schemas/
│
├── scripts/                           # Scripts (unchanged)
│   └── utilities/
│
└── utils/                             # Utils (unchanged)
    ├── __init__.py
    └── helpers.py
```

---

## Directory Comparison

### Before vs After Summary

| Directory | Before | After | Change |
|-----------|--------|-------|--------|
| core/ | 145 files (flat) | Organized into 12 subdirs | +12 new packages |
| agents/ | 11 files (flat) | 4 subdirs (framework, research, analysis, output) | +framework layer |
| tools/ | 47 files (semi-organized) | framework/ + 4 categories | +framework layer |
| services/ | 30 files (flat) | 6 category subdirs | Clear separation |
| pipeline/ | 15 files (flat) | core/, stages/, orchestration/ | Split stages |
| graph/ | 3 files | builder/, state/, workflow/ | Split large file |
| api/ | 4 files | routers/, models/, middleware/, database/ | Split app.py |

### New Packages Created

1. **`core/config/`** - Centralized configuration (7 files)
2. **`core/di/`** - Dependency injection (5 files)
3. **`core/managers/`** - Manager base classes (6 files)
4. **`core/providers/`** - Provider chain abstraction (6 files)
5. **`core/resilience/`** - Resilience patterns (8 files)
6. **`core/validation/`** - Validation framework (8 files)
7. **`core/ai/`** - AI client organization (15 files)
8. **`agents/framework/`** - Agent framework (5 files)
9. **`tools/framework/`** - Tool framework (7 files)
10. **`pipeline/core/`** - Pipeline core (6 files)
11. **`graph/builder/`** - Graph building (6 files)
12. **`graph/state/`** - State management (5 files)
13. **`api/routers/`** - API routers (6 files)

### Files Removed/Merged

| File | Action | Destination |
|------|--------|-------------|
| `core/configs.py` | DELETED | Merged into `core/config/` |
| `core/constants.py` | DELETED | Merged into `core/config/defaults.py` |
| `core/config.py` | SPLIT | Into `core/config/` package |
| `core/ai_client.py` | SPLIT | Into `core/ai/` package |
| `core/validators.py` | SPLIT | Into `core/validation/` package |
| `graph/graph_builder.py` | SPLIT | Into `graph/builder/` package |
| `graph/state.py` | SPLIT | Into `graph/state/` package |
| `pipeline/research.py` | SPLIT | Into `pipeline/stages/research/` |
| `api/app.py` | SPLIT | Into `api/` + `api/routers/` |

---

## Import Path Changes

### Configuration
```python
# Before
from src.core.config import get_settings
from src.core.configs import get_config
from src.core.constants import DEFAULT_MODEL

# After
from src.core.config import get_config
config = get_config()
model = config.ai.default_model
```

### DI Container
```python
# Before
from src.core.container import get_container

# After
from src.core.di import container, singleton

@singleton
class MyService:
    pass

instance = container.resolve(MyService)
```

### AI Client
```python
# Before
from src.core.ai_client import get_ai_manager, AIClientManager

# After
from src.core.ai import AIClientManager, get_ai_manager
from src.core.ai.clients import OpenAIClient, AnthropicClient
```

### Resilience
```python
# Before
from src.core.retry_strategy import RetryStrategy
from src.core.circuit_breaker import CircuitBreaker

# After
from src.core.resilience import (
    ResilientExecutor,
    RetryPolicy,
    CircuitBreakerPolicy,
    resilient
)

@resilient(retry=RetryPolicy(max_attempts=3))
async def my_operation():
    pass
```

### Tools
```python
# Before
from src.tools.search.tavily import TavilySearchProvider

# After
from src.tools.search.providers import TavilySearchTool
from src.tools.framework import ToolRegistry

registry = ToolRegistry()
tavily = registry.get("tavily")
```

### Pipeline
```python
# Before
from src.pipeline.pipeline import Pipeline
from src.pipeline.research import ResearchStage

# After
from src.pipeline.core import Pipeline, PipelineBuilder
from src.pipeline.stages.research import ResearchStage

pipeline = (
    PipelineBuilder()
    .add_stage(ResearchStage())
    .build()
)
```

### Graph
```python
# Before
from src.graph.graph_builder import GraphBuilder
from src.graph.state import ResearchState

# After
from src.graph.builder import GraphBuilder
from src.graph.state import ResearchState, StateValidator
```

### API
```python
# Before
from src.api.app import app

# After
from src.api import create_app
from src.api.routers import research_router, companies_router

app = create_app()
```

---

## File Count Comparison

| Category | Before | After | Notes |
|----------|--------|-------|-------|
| **Total Files** | ~246 | ~290 | +44 new framework files |
| **core/** | 145 | 85 | Split into subpackages |
| **core/config/** | 0 | 8 | NEW |
| **core/di/** | 0 | 5 | NEW |
| **core/managers/** | 0 | 6 | NEW |
| **core/providers/** | 0 | 6 | NEW |
| **core/resilience/** | 0 | 8 | NEW |
| **core/validation/** | 0 | 8 | NEW |
| **core/ai/** | 0 | 15 | Reorganized from core/ |
| **agents/** | 11 | 15 | +framework |
| **tools/** | 47 | 55 | +framework |
| **services/** | 30 | 30 | Reorganized only |
| **pipeline/** | 15 | 25 | Split stages |
| **graph/** | 3 | 15 | Split large file |
| **api/** | 4 | 12 | Split app.py |

---

## Module Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│  api/routers/  →  api/dependencies  →  api/middleware           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     ORCHESTRATION LAYER                          │
│  graph/builder/  →  pipeline/orchestration/  →  graph/workflow/ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      BUSINESS LAYER                              │
│  agents/  →  services/  →  pipeline/stages/  →  graph/state/    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     INTEGRATION LAYER                            │
│  tools/search/  →  tools/browser/  →  tools/data/               │
│         └──────────── tools/framework/ ────────────┘            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     FOUNDATION LAYER                             │
│  core/config/  ←  core/di/  ←  core/resilience/                 │
│  core/providers/  ←  core/validation/  ←  core/managers/        │
│  core/ai/  ←  core/cache/  ←  core/types/  ←  core/models/      │
│  core/exceptions/  ←  core/logging/                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Architectural Principles

### 1. Single Responsibility
- Each file has ONE clear purpose
- Max ~300-400 lines per file
- Split large files into focused modules

### 2. Dependency Inversion
- All dependencies via DI container
- No direct singleton access
- Interface-based design

### 3. Open/Closed
- Extend via new providers/tools
- Base classes for extension points
- Plugin architecture for tools

### 4. Interface Segregation
- Small, focused interfaces
- Mixins for optional capabilities
- Clear contracts between layers

### 5. Configuration Centralization
- Single source of truth
- Validated at startup
- Environment-specific profiles
