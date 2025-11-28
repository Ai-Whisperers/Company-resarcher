"""
SearchStage - Execute web searches with typed inputs/outputs.

This stage demonstrates the pipeline pattern:
1. Typed input (SearchInput)
2. Typed output (SearchOutput)
3. Uses RequestContext for dependencies (no globals)
4. Returns Result for explicit error handling
5. Supports partial success (some queries may fail)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...core.result import Result, Ok, Err

from ..context import RequestContext
from ..stage import Stage, StageError, StageErrorCode


# =============================================================================
# Input/Output Types
# =============================================================================


@dataclass
class SearchInput:
    """
    Input for the SearchStage.

    Attributes:
        queries: List of search queries to execute
        max_results_per_query: Maximum results per query (1-20)
        require_all: If True, fail if any query fails. If False, allow partial success.
    """

    queries: List[str]
    max_results_per_query: int = 5
    require_all: bool = False

    def __post_init__(self):
        # Clamp max_results to valid range
        self.max_results_per_query = max(1, min(20, self.max_results_per_query))


@dataclass
class SearchResult:
    """A single search result."""

    url: str
    title: str
    content: str
    score: float = 0.0
    query: str = ""  # The query that produced this result


@dataclass
class FailedQuery:
    """Information about a failed query."""

    query: str
    error_code: str
    error_message: str
    retryable: bool = False


@dataclass
class SearchOutput:
    """
    Output from the SearchStage.

    Supports partial success - some queries may succeed while others fail.

    Attributes:
        results: All successful search results
        failed_queries: Queries that failed with error details
        total_queries: Total number of queries attempted
        successful_queries: Number of queries that succeeded
    """

    results: List[SearchResult] = field(default_factory=list)
    failed_queries: List[FailedQuery] = field(default_factory=list)
    total_queries: int = 0
    successful_queries: int = 0

    @property
    def has_results(self) -> bool:
        """Check if any results were found."""
        return len(self.results) > 0

    @property
    def has_failures(self) -> bool:
        """Check if any queries failed."""
        return len(self.failed_queries) > 0

    @property
    def all_failed(self) -> bool:
        """Check if all queries failed."""
        return self.successful_queries == 0 and self.total_queries > 0


# =============================================================================
# SearchStage
# =============================================================================


class SearchStage(Stage[SearchInput, SearchOutput]):
    """
    Execute web searches using the search tool from context.

    This stage:
    1. Validates input queries
    2. Executes searches with timeout budget awareness
    3. Handles partial failures gracefully
    4. Returns typed SearchOutput with results and failures

    Example:
        stage = SearchStage()
        input = SearchInput(
            queries=["Company X news", "Company X financials"],
            max_results_per_query=5,
        )
        result = await stage.run(input, ctx)

        if result.is_ok:
            output = result.unwrap().output
            for r in output.results:
                print(f"{r.title}: {r.url}")
    """

    @property
    def name(self) -> str:
        return "search"

    def validate_input(self, input: SearchInput) -> Optional[StageError]:
        """Validate search input."""
        if not input.queries:
            return StageError.invalid_input(
                message="No queries provided",
                details={"queries": []},
            )

        # Check for empty queries
        empty_queries = [q for q in input.queries if not q or not q.strip()]
        if empty_queries:
            return StageError.invalid_input(
                message=f"{len(empty_queries)} empty queries provided",
                details={"empty_count": len(empty_queries)},
            )

        return None

    async def execute(
        self,
        input: SearchInput,
        ctx: RequestContext,
    ) -> Result[SearchOutput, StageError]:
        """
        Execute search queries.

        Args:
            input: Search parameters
            ctx: Request context with search tool

        Returns:
            Ok(SearchOutput) with results, or Err(StageError) on complete failure
        """
        results: List[SearchResult] = []
        failed_queries: List[FailedQuery] = []

        ctx.logger.info(
            f"Executing searches",
            query_count=len(input.queries),
            max_results=input.max_results_per_query,
        )

        for query in input.queries:
            # Check cancellation before each query
            if ctx.cancellation.is_cancelled:
                return Err(
                    StageError.cancelled(self.name, ctx.cancellation.reason)
                )

            # Check timeout budget
            if not ctx.timeout_budget.has_time_remaining(min_required=5.0):
                ctx.logger.warning(
                    "Timeout budget low, stopping search early",
                    remaining=f"{ctx.timeout_budget.remaining():.1f}s",
                    completed_queries=len(results) + len(failed_queries),
                )
                break

            # Execute search using context's search tool
            query_results = await self._execute_query(
                query, input.max_results_per_query, ctx
            )

            if query_results.is_ok:
                search_results = query_results.unwrap()
                results.extend(search_results)
                ctx.logger.debug(
                    f"Query succeeded",
                    query=query[:50],
                    result_count=len(search_results),
                )
            else:
                error = query_results.unwrap_err()
                failed_queries.append(error)
                ctx.logger.warning(
                    f"Query failed",
                    query=query[:50],
                    error=error.error_message,
                )

                # If require_all, fail immediately
                if input.require_all:
                    return Err(
                        StageError.search_error(
                            message=f"Required query failed: {query}",
                            details={"query": query, "error": error.error_message},
                            retryable=error.retryable,
                        )
                    )

        # Build output
        output = SearchOutput(
            results=results,
            failed_queries=failed_queries,
            total_queries=len(input.queries),
            successful_queries=len(input.queries) - len(failed_queries),
        )

        # Check if we have any results
        if output.all_failed:
            return Err(
                StageError.search_error(
                    message=f"All {len(input.queries)} queries failed",
                    details={
                        "failed_queries": [f.query for f in failed_queries],
                        "errors": [f.error_message for f in failed_queries],
                    },
                    retryable=any(f.retryable for f in failed_queries),
                )
            )

        # Partial success is OK
        if output.has_failures:
            ctx.logger.warning(
                f"Partial search success",
                succeeded=output.successful_queries,
                failed=len(failed_queries),
            )

        return Ok(output)

    async def _execute_query(
        self,
        query: str,
        max_results: int,
        ctx: RequestContext,
    ) -> Result[List[SearchResult], FailedQuery]:
        """Execute a single search query."""
        try:
            # Use search_safe if available (returns Result)
            if hasattr(ctx.search_tool, "search_safe"):
                result = await ctx.search_tool.search_safe(query, max_results)

                if result.is_ok:
                    raw_results = result.unwrap()
                    return Ok(self._parse_results(raw_results, query))
                else:
                    error = result.unwrap_err()
                    return Err(
                        FailedQuery(
                            query=query,
                            error_code=str(error.code) if hasattr(error, "code") else "UNKNOWN",
                            error_message=str(error),
                            retryable=getattr(error, "recoverable", False),
                        )
                    )
            else:
                # Fall back to regular search
                raw_results = await ctx.search_tool.search(query, max_results)

                if not raw_results:
                    return Err(
                        FailedQuery(
                            query=query,
                            error_code="NO_RESULTS",
                            error_message="No results found",
                            retryable=False,
                        )
                    )

                return Ok(self._parse_results(raw_results, query))

        except Exception as e:
            return Err(
                FailedQuery(
                    query=query,
                    error_code="EXCEPTION",
                    error_message=str(e),
                    retryable=True,  # Unknown errors might be transient
                )
            )

    def _parse_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: str,
    ) -> List[SearchResult]:
        """Parse raw search results into typed SearchResult objects."""
        results = []
        for raw in raw_results:
            results.append(
                SearchResult(
                    url=raw.get("url", ""),
                    title=raw.get("title", "No Title"),
                    content=raw.get("content", ""),
                    score=raw.get("score", 0.0),
                    query=query,
                )
            )
        return results

    def can_retry(self, error: StageError) -> bool:
        """Search errors are usually retryable."""
        if error.code == StageErrorCode.CANCELLED:
            return False
        if error.code == StageErrorCode.TIMEOUT_BUDGET_EXHAUSTED:
            return False
        return error.retryable


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SearchStage",
    "SearchInput",
    "SearchOutput",
    "SearchResult",
    "FailedQuery",
]
