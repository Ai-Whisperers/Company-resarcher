"""
FetchStage - Fetch content from URLs using the browser tool.

Converts search results into full page content.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ...core.result import Result, Ok, Err

from ..context import RequestContext
from ..stage import Stage, StageError, StageErrorCode

from .search import SearchOutput, SearchResult


# =============================================================================
# Input/Output Types
# =============================================================================


@dataclass
class FetchInput:
    """
    Input for the FetchStage.

    Can be constructed from SearchOutput or a list of URLs.

    Attributes:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent fetches
        source_metadata: Optional metadata about each URL's source
    """

    urls: List[str]
    max_concurrent: int = 5
    source_metadata: dict = field(default_factory=dict)  # url -> metadata

    @classmethod
    def from_search_output(
        cls,
        search_output: SearchOutput,
        max_concurrent: int = 5,
    ) -> "FetchInput":
        """Create FetchInput from SearchOutput."""
        urls = []
        metadata = {}

        for result in search_output.results:
            if result.url and result.url not in urls:
                urls.append(result.url)
                metadata[result.url] = {
                    "title": result.title,
                    "query": result.query,
                    "score": result.score,
                }

        return cls(
            urls=urls,
            max_concurrent=max_concurrent,
            source_metadata=metadata,
        )


@dataclass
class FetchedContent:
    """Content fetched from a URL."""

    url: str
    title: str
    content: str
    success: bool = True
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class FetchOutput:
    """
    Output from the FetchStage.

    Attributes:
        content: Successfully fetched content
        failed_urls: URLs that failed to fetch
        total_urls: Total URLs attempted
    """

    content: List[FetchedContent] = field(default_factory=list)
    failed_urls: List[str] = field(default_factory=list)
    total_urls: int = 0

    @property
    def successful_count(self) -> int:
        return len(self.content)

    @property
    def has_content(self) -> bool:
        return len(self.content) > 0


# =============================================================================
# FetchStage
# =============================================================================


class FetchStage(Stage[FetchInput, FetchOutput]):
    """
    Fetch content from URLs using the browser tool.

    This stage handles:
    1. Concurrent fetching with rate limiting
    2. Timeout budget awareness
    3. Graceful handling of fetch failures
    """

    @property
    def name(self) -> str:
        return "fetch"

    def validate_input(self, input: FetchInput) -> Optional[StageError]:
        """Validate fetch input."""
        if not input.urls:
            return StageError.invalid_input(
                message="No URLs provided",
                details={"urls": []},
            )
        return None

    async def execute(
        self,
        input: FetchInput,
        ctx: RequestContext,
    ) -> Result[FetchOutput, StageError]:
        """Fetch content from URLs."""
        import asyncio

        content: List[FetchedContent] = []
        failed_urls: List[str] = []

        ctx.logger.info(
            f"Fetching URLs",
            url_count=len(input.urls),
            max_concurrent=input.max_concurrent,
        )

        # Use semaphore for concurrency control
        semaphore = asyncio.Semaphore(input.max_concurrent)

        async def fetch_one(url: str) -> FetchedContent:
            async with semaphore:
                # Check cancellation
                if ctx.cancellation.is_cancelled:
                    return FetchedContent(
                        url=url,
                        title="",
                        content="",
                        success=False,
                        error_message="Cancelled",
                    )

                try:
                    result = await ctx.browser_tool.fetch_url(url)

                    # Handle different return types
                    if hasattr(result, "content"):
                        return FetchedContent(
                            url=url,
                            title=getattr(result, "title", url),
                            content=result.content,
                            success=True,
                            metadata=input.source_metadata.get(url, {}),
                        )
                    elif isinstance(result, dict):
                        return FetchedContent(
                            url=url,
                            title=result.get("title", url),
                            content=result.get("content", ""),
                            success=True,
                            metadata=input.source_metadata.get(url, {}),
                        )
                    else:
                        return FetchedContent(
                            url=url,
                            title=url,
                            content=str(result) if result else "",
                            success=bool(result),
                            metadata=input.source_metadata.get(url, {}),
                        )

                except Exception as e:
                    ctx.logger.warning(f"Failed to fetch URL", url=url, error=str(e))
                    return FetchedContent(
                        url=url,
                        title="",
                        content="",
                        success=False,
                        error_message=str(e),
                    )

        # Fetch all URLs concurrently
        tasks = [fetch_one(url) for url in input.urls]
        results = await asyncio.gather(*tasks)

        # Separate successes and failures
        for result in results:
            if result.success:
                content.append(result)
            else:
                failed_urls.append(result.url)

        output = FetchOutput(
            content=content,
            failed_urls=failed_urls,
            total_urls=len(input.urls),
        )

        ctx.logger.info(
            f"Fetch complete",
            succeeded=output.successful_count,
            failed=len(failed_urls),
        )

        if not output.has_content:
            return Err(
                StageError.search_error(
                    message=f"Failed to fetch any content from {len(input.urls)} URLs",
                    details={"failed_urls": failed_urls},
                    retryable=True,
                )
            )

        return Ok(output)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FetchStage",
    "FetchInput",
    "FetchOutput",
    "FetchedContent",
]
