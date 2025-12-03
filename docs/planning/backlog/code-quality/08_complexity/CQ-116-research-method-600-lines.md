# CQ-116: research() Method Exceeds 600 Lines

## Metadata
- **Severity**: HIGH
- **Category**: Complexity
- **File**: [src/pipeline/comprehensive_research.py](src/pipeline/comprehensive_research.py#L163-L820)
- **Lines**: 163-820 (657 lines)
- **Effort**: XL
- **Status**: Open

## Problem

The `research()` method in `ComprehensiveResearchPipeline` is over 600 lines long, making it:
- Impossible to understand at a glance
- Very difficult to test individual components
- Prone to bugs due to complex control flow
- Hard to modify without breaking something

## Current Structure

```python
async def research(self, company: str, ...) -> ResearchResult:
    # Lines 163-220: Setup and initialization (~57 lines)
    # Lines 221-350: Query generation (~129 lines)
    # Lines 351-500: Search execution with fallbacks (~149 lines)
    # Lines 501-650: Content analysis and synthesis (~149 lines)
    # Lines 651-750: Report generation (~99 lines)
    # Lines 751-820: Cleanup and return (~69 lines)
```

## Solution

Break into focused methods following Single Responsibility Principle:

### New Structure

```python
class ComprehensiveResearchPipeline:
    """Orchestrates comprehensive company research."""

    async def research(
        self,
        company: str,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        **kwargs
    ) -> ResearchResult:
        """
        Execute comprehensive research on a company.

        This method orchestrates the research pipeline through distinct phases:
        1. Initialize research context
        2. Generate search queries
        3. Execute searches
        4. Analyze content
        5. Generate report

        Args:
            company: Company name to research
            industry: Optional industry context
            country: Optional country context
            **kwargs: Additional configuration options

        Returns:
            ResearchResult with report and metadata
        """
        # Phase 1: Initialize
        context = await self._initialize_research(company, industry, country, **kwargs)

        try:
            # Phase 2: Generate queries
            queries = await self._generate_queries(context)

            # Phase 3: Execute searches
            sources = await self._execute_searches(context, queries)

            # Phase 4: Analyze content
            analysis = await self._analyze_content(context, sources)

            # Phase 5: Generate report
            report = await self._generate_report(context, analysis)

            return ResearchResult(
                success=True,
                report=report,
                sources=sources,
                metadata=context.metadata
            )

        except Exception as e:
            return await self._handle_research_error(context, e)

        finally:
            await self._cleanup(context)

    # =========================================================================
    # Phase 1: Initialization
    # =========================================================================

    async def _initialize_research(
        self,
        company: str,
        industry: Optional[str],
        country: Optional[str],
        **kwargs
    ) -> ResearchContext:
        """
        Initialize research context with configuration and state.

        Creates the research context, validates inputs, and sets up
        logging and tracking for the research session.
        """
        context = ResearchContext(
            company=company,
            industry=industry or await self._detect_industry(company),
            country=country or "global",
            start_time=datetime.now(timezone.utc),
            config=self._build_config(**kwargs)
        )

        self._log_research_start(context)
        await self._setup_tracking(context)

        return context

    # =========================================================================
    # Phase 2: Query Generation
    # =========================================================================

    async def _generate_queries(self, context: ResearchContext) -> QueryPlan:
        """
        Generate search queries for all research sections.

        Returns a QueryPlan containing queries organized by section,
        with priorities and fallback strategies.
        """
        sections = self._get_research_sections(context)
        query_plan = QueryPlan()

        for section in sections:
            section_queries = await self._generate_section_queries(
                context, section
            )
            query_plan.add_section(section.name, section_queries)

        return query_plan

    async def _generate_section_queries(
        self,
        context: ResearchContext,
        section: ResearchSection
    ) -> List[Query]:
        """Generate queries for a specific research section."""
        prompt = self._build_query_prompt(context, section)
        response = await self.ai.generate(prompt)
        return self._parse_query_response(response, section)

    # =========================================================================
    # Phase 3: Search Execution
    # =========================================================================

    async def _execute_searches(
        self,
        context: ResearchContext,
        query_plan: QueryPlan
    ) -> List[ResearchSource]:
        """
        Execute all searches with rate limiting and fallbacks.

        Runs searches concurrently within rate limits, handles failures
        with automatic fallback to alternative providers.
        """
        all_sources = []

        for section_name, queries in query_plan.sections.items():
            sources = await self._execute_section_searches(
                context, section_name, queries
            )
            all_sources.extend(sources)

        return self._deduplicate_sources(all_sources)

    async def _execute_section_searches(
        self,
        context: ResearchContext,
        section: str,
        queries: List[Query]
    ) -> List[ResearchSource]:
        """Execute searches for a single section."""
        semaphore = asyncio.Semaphore(context.config.max_concurrent_queries)

        async def search_with_limit(query: Query) -> List[ResearchSource]:
            async with semaphore:
                return await self._search_with_fallback(context, query)

        tasks = [search_with_limit(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return self._flatten_search_results(results, queries)

    async def _search_with_fallback(
        self,
        context: ResearchContext,
        query: Query
    ) -> List[ResearchSource]:
        """Execute search with automatic fallback on failure."""
        for attempt in range(context.config.max_fallback_attempts):
            try:
                return await self.search_tool.search(query.text)
            except SearchError as e:
                if attempt == context.config.max_fallback_attempts - 1:
                    context.log_warning(f"Search failed after retries: {query}")
                    return []
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    # =========================================================================
    # Phase 4: Content Analysis
    # =========================================================================

    async def _analyze_content(
        self,
        context: ResearchContext,
        sources: List[ResearchSource]
    ) -> ContentAnalysis:
        """
        Analyze and synthesize content from all sources.

        Performs content extraction, relevance scoring, and synthesis
        to create structured analysis for report generation.
        """
        # Group sources by section
        grouped = self._group_sources_by_section(sources)

        # Analyze each section
        section_analyses = {}
        for section, section_sources in grouped.items():
            section_analyses[section] = await self._analyze_section(
                context, section, section_sources
            )

        return ContentAnalysis(sections=section_analyses)

    async def _analyze_section(
        self,
        context: ResearchContext,
        section: str,
        sources: List[ResearchSource]
    ) -> SectionAnalysis:
        """Analyze content for a specific section."""
        # Extract key information
        extracted = await self._extract_key_info(sources, section)

        # Score relevance
        scored = self._score_relevance(extracted, context)

        # Synthesize findings
        synthesis = await self._synthesize_findings(scored, section)

        return SectionAnalysis(
            section=section,
            findings=synthesis,
            sources=sources,
            confidence=self._calculate_confidence(scored)
        )

    # =========================================================================
    # Phase 5: Report Generation
    # =========================================================================

    async def _generate_report(
        self,
        context: ResearchContext,
        analysis: ContentAnalysis
    ) -> Report:
        """
        Generate final report from analysis.

        Creates structured report with executive summary, detailed sections,
        and source citations.
        """
        # Generate section reports
        sections = []
        for section_name, section_analysis in analysis.sections.items():
            section_report = await self._generate_section_report(
                context, section_name, section_analysis
            )
            sections.append(section_report)

        # Generate executive summary
        summary = await self._generate_executive_summary(context, sections)

        return Report(
            company=context.company,
            summary=summary,
            sections=sections,
            generated_at=datetime.now(timezone.utc)
        )

    # =========================================================================
    # Error Handling & Cleanup
    # =========================================================================

    async def _handle_research_error(
        self,
        context: ResearchContext,
        error: Exception
    ) -> ResearchResult:
        """Handle research errors with proper logging and partial results."""
        context.log_error(f"Research failed: {error}")

        return ResearchResult(
            success=False,
            error=str(error),
            partial_results=context.partial_results,
            metadata=context.metadata
        )

    async def _cleanup(self, context: ResearchContext) -> None:
        """Clean up resources after research completion."""
        await context.flush_metrics()
        context.log_completion()
```

## Benefits

1. **Testability**: Each method can be unit tested independently
2. **Readability**: Clear phase separation
3. **Maintainability**: Changes isolated to specific methods
4. **Reusability**: Methods can be overridden in subclasses
5. **Debugging**: Easier to identify which phase failed

## Migration Steps

1. Create `ResearchContext` and `QueryPlan` dataclasses
2. Extract Phase 1 (`_initialize_research`) and test
3. Extract Phase 2 (`_generate_queries`) and test
4. Extract Phase 3 (`_execute_searches`) and test
5. Extract Phase 4 (`_analyze_content`) and test
6. Extract Phase 5 (`_generate_report`) and test
7. Update main `research()` method
8. Run full integration tests

## Testing

```python
class TestComprehensiveResearchPipeline:
    """Tests for refactored pipeline."""

    async def test_initialize_research(self):
        """Test context initialization."""
        pipeline = ComprehensiveResearchPipeline(...)
        context = await pipeline._initialize_research("Acme Corp")
        assert context.company == "Acme Corp"
        assert context.start_time is not None

    async def test_generate_queries(self):
        """Test query generation."""
        pipeline = ComprehensiveResearchPipeline(...)
        context = ResearchContext(company="Test")
        queries = await pipeline._generate_queries(context)
        assert len(queries.sections) > 0

    async def test_search_with_fallback(self):
        """Test fallback behavior."""
        pipeline = ComprehensiveResearchPipeline(...)
        # First call fails, second succeeds
        pipeline.search_tool.search = AsyncMock(
            side_effect=[SearchError(), [ResearchSource(...)]]
        )
        result = await pipeline._search_with_fallback(context, query)
        assert len(result) > 0
```

## Related Issues

- CQ-115: run_research_task() also needs refactoring
- CQ-117: search_distributed() has similar issues
