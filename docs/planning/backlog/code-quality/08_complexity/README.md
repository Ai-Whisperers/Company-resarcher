# Complexity Issues

> **Total Issues**: 12 (6 HIGH, 4 MEDIUM, 2 LOW)
> **Priority**: Phase 3 - Maintainability

## Overview

Complex functions are hard to test, maintain, and debug. Breaking them into smaller, focused functions improves code quality significantly.

## Issues Summary

### HIGH Severity (6)

| ID | File | Lines | Metric | Description |
|----|------|-------|--------|-------------|
| CQ-115 | api/app.py | 329-517 | 188 lines | run_research_task() |
| CQ-116 | pipeline/comprehensive_research.py | 163-820 | 600+ lines | research() method |
| CQ-117 | search/manager.py | 630-850 | 220 lines | search_distributed() |
| CQ-118 | agents/base_agent.py | 120-177 | 60 lines | _safe_generate() |
| CQ-119 | pipeline/stages/research.py | 790-833 | 43 lines | execute() method |
| CQ-120 | agents/specialists.py | 427-430 | N/A | Sequential async calls |

### MEDIUM Severity (4)

| ID | File | Description |
|----|------|-------------|
| CQ-121 | pipeline/orchestrator.py | Multiple nested try/except |
| CQ-122 | search/manager.py | 79-line nested provider_worker |
| CQ-123 | agents/deep_research.py | Manual string parsing |
| CQ-124 | agents/generic_agent.py | Phase-specific logic hardcoded |

### LOW Severity (2)

| ID | File | Description |
|----|------|-------------|
| CQ-125 | Various | Functions with >5 parameters |
| CQ-126 | Various | Deeply nested conditionals |

## Refactoring Strategies

### CQ-115: run_research_task() - 188 lines

**Current Structure**:
```python
async def run_research_task(task_id, company_name, ...):
    # Setup (30 lines)
    # Mode selection (40 lines)
    # Pipeline mode (50 lines)
    # Graph mode (40 lines)
    # Error handling (28 lines)
```

**Refactored Structure**:
```python
async def run_research_task(task_id, company_name, ...):
    context = await _setup_research_context(task_id, company_name, ...)
    try:
        result = await _execute_research(context)
        await _save_research_result(context, result)
        return result
    except Exception as e:
        await _handle_research_error(context, e)
        raise

async def _setup_research_context(...) -> ResearchContext:
    """Setup logging, database, and configuration."""
    pass

async def _execute_research(context: ResearchContext) -> ResearchResult:
    """Execute research based on mode."""
    if context.mode == "pipeline":
        return await _run_pipeline_research(context)
    elif context.mode == "graph":
        return await _run_graph_research(context)
    else:
        return await _run_direct_research(context)

async def _run_pipeline_research(context: ResearchContext) -> ResearchResult:
    """Execute pipeline mode research."""
    pass

async def _run_graph_research(context: ResearchContext) -> ResearchResult:
    """Execute graph mode research."""
    pass
```

### CQ-116: research() - 600+ lines

**Strategy**: Extract distinct phases into separate methods

```python
class ComprehensiveResearchPipeline:
    async def research(self, company: str, ...) -> ResearchResult:
        """Orchestrate research phases."""
        context = await self._initialize_research(company, ...)

        # Phase 1: Query generation
        queries = await self._generate_queries(context)

        # Phase 2: Search execution
        sources = await self._execute_searches(context, queries)

        # Phase 3: Content analysis
        analysis = await self._analyze_content(context, sources)

        # Phase 4: Report generation
        report = await self._generate_report(context, analysis)

        return report

    async def _initialize_research(self, ...) -> ResearchContext:
        """Initialize research context and configuration."""
        pass  # Extract ~50 lines

    async def _generate_queries(self, context) -> List[Query]:
        """Generate search queries for all sections."""
        pass  # Extract ~100 lines

    async def _execute_searches(self, context, queries) -> List[Source]:
        """Execute searches with fallbacks."""
        pass  # Extract ~150 lines

    async def _analyze_content(self, context, sources) -> Analysis:
        """Analyze and synthesize content."""
        pass  # Extract ~200 lines

    async def _generate_report(self, context, analysis) -> Report:
        """Generate final report."""
        pass  # Extract ~100 lines
```

### CQ-117: search_distributed() - 220 lines

**Current**: Monolithic with nested worker function

**Refactored**:
```python
class DistributedSearcher:
    """Handles distributed search across providers."""

    def __init__(self, providers: List[SearchProvider]):
        self.providers = providers

    async def search(self, queries: List[str]) -> List[SearchResult]:
        """Execute distributed search."""
        queue = self._create_query_queue(queries)
        workers = self._create_workers(queue)
        return await self._collect_results(workers)

    def _create_query_queue(self, queries) -> asyncio.Queue:
        """Create bounded queue with queries."""
        pass

    def _create_workers(self, queue) -> List[asyncio.Task]:
        """Create worker tasks for each provider."""
        pass

    async def _collect_results(self, workers) -> List[SearchResult]:
        """Collect and merge results from workers."""
        pass

class SearchWorker:
    """Individual search worker for a provider."""

    async def run(self, queue: asyncio.Queue, results: List):
        """Process queries from queue."""
        while True:
            query = await self._get_next_query(queue)
            if query is None:
                break
            result = await self._execute_query(query)
            await self._handle_result(result, results)
```

### CQ-120: Sequential Async Calls

**Problem**:
```python
# BAD - Sequential
result1 = await self._fetch_financials(query)
result2 = await self._fetch_news(query)
result3 = await self._fetch_social(query)
result4 = await self._fetch_web(query)
```

**Solution**:
```python
# GOOD - Concurrent
results = await asyncio.gather(
    self._fetch_financials(query),
    self._fetch_news(query),
    self._fetch_social(query),
    self._fetch_web(query),
    return_exceptions=True
)
financials, news, social, web = results
```

## Metrics Targets

| Metric | Current | Target |
|--------|---------|--------|
| Max function lines | 600+ | <50 |
| Max cyclomatic complexity | >15 | <10 |
| Max nesting depth | 6+ | <4 |
| Max parameters | 10+ | <5 |

## Verification Checklist

- [ ] No function exceeds 50 lines
- [ ] Cyclomatic complexity <10 per function
- [ ] Maximum nesting depth of 4
- [ ] Functions have <=5 parameters (use dataclass for more)
- [ ] Sequential async calls converted to gather()
- [ ] Each function has single responsibility
