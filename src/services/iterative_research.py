"""
Iterative Research Service - Keeps researching until all data gaps are filled.

This service implements a loop that:
1. Analyzes current research for N/A values
2. Generates targeted queries for missing data
3. Runs searches and scrapes results
4. Uses AI to extract specific data points
5. Updates the research documents
6. Repeats until no gaps remain or max iterations reached
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core.logger import setup_logger
from ..core.ai_client import get_ai_manager
from .gap_analyzer import GapAnalyzer, DataGap

logger = setup_logger("iterative_research")


@dataclass
class FillResult:
    """Result of attempting to fill a data gap."""
    gap: DataGap
    filled: bool
    value: Optional[str]
    source_url: Optional[str]
    confidence: float  # 0.0 to 1.0


@dataclass
class IterationResult:
    """Result of a single research iteration."""
    iteration: int
    gaps_before: int
    gaps_after: int
    gaps_filled: int
    fill_results: List[FillResult]
    duration_seconds: float


@dataclass
class IterativeResearchResult:
    """Final result of iterative research."""
    company: str
    initial_gaps: int
    final_gaps: int
    total_filled: int
    iterations_run: int
    iterations: List[IterationResult]
    success: bool  # True if all gaps filled


class IterativeResearchService:
    """
    Service that iteratively fills data gaps in research output.

    Usage:
        service = IterativeResearchService()
        result = await service.fill_gaps(
            company_name="Claro Paraguay",
            industry="telecommunications",
            max_iterations=5,
        )
    """

    def __init__(
        self,
        base_dir: str = "outputs",
        search_tool=None,
        browser_tool=None,
    ):
        self.base_dir = Path(base_dir).resolve()
        self.gap_analyzer = GapAnalyzer(base_dir)
        self.ai_client = None
        self._search_tool = search_tool
        self._browser_tool = browser_tool

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self.ai_client is None:
            self.ai_client = get_ai_manager()
        return self.ai_client

    async def _get_search_tool(self):
        """Lazy load search tool."""
        if self._search_tool is None:
            from ..tools import get_shared_search_tool
            self._search_tool = get_shared_search_tool()
        return self._search_tool

    async def _get_browser_tool(self):
        """Lazy load browser tool."""
        if self._browser_tool is None:
            from ..tools import get_shared_browser_tool
            self._browser_tool = get_shared_browser_tool()
        return self._browser_tool

    async def fill_gaps(
        self,
        company_name: str,
        industry: str = "telecommunications",
        max_iterations: int = 5,
        related_companies: Optional[List[str]] = None,
    ) -> IterativeResearchResult:
        """
        Iteratively research to fill all data gaps.

        Args:
            company_name: Company to fill gaps for
            industry: Industry context for queries
            max_iterations: Maximum research iterations
            related_companies: Other companies to cross-reference

        Returns:
            IterativeResearchResult with fill statistics
        """
        logger.info(f"Starting iterative gap filling for {company_name}")

        # Initial gap analysis
        initial_result = self.gap_analyzer.analyze_company(company_name)
        initial_gaps = initial_result.total_gaps

        if initial_gaps == 0:
            logger.info(f"No gaps found for {company_name}")
            return IterativeResearchResult(
                company=company_name,
                initial_gaps=0,
                final_gaps=0,
                total_filled=0,
                iterations_run=0,
                iterations=[],
                success=True,
            )

        logger.info(f"Found {initial_gaps} gaps to fill")

        iterations = []
        total_filled = 0
        current_gaps = initial_gaps

        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n--- Iteration {iteration}/{max_iterations} ---")
            start_time = datetime.now()

            # Run one iteration
            iter_result = await self._run_iteration(
                company_name=company_name,
                industry=industry,
                iteration=iteration,
                related_companies=related_companies or [],
            )

            iterations.append(iter_result)
            total_filled += iter_result.gaps_filled
            current_gaps = iter_result.gaps_after

            logger.info(
                f"Iteration {iteration}: Filled {iter_result.gaps_filled} gaps "
                f"({current_gaps} remaining)"
            )

            # Check if done
            if current_gaps == 0:
                logger.info("All gaps filled!")
                break

            # Check if no progress
            if iter_result.gaps_filled == 0:
                logger.warning("No gaps filled this iteration, stopping")
                break

        success = current_gaps == 0

        return IterativeResearchResult(
            company=company_name,
            initial_gaps=initial_gaps,
            final_gaps=current_gaps,
            total_filled=total_filled,
            iterations_run=len(iterations),
            iterations=iterations,
            success=success,
        )

    async def _run_iteration(
        self,
        company_name: str,
        industry: str,
        iteration: int,
        related_companies: List[str],
    ) -> IterationResult:
        """Run a single gap-filling iteration."""
        start_time = datetime.now()

        # Analyze current gaps
        gap_result = self.gap_analyzer.analyze_company(company_name)
        gaps_before = gap_result.total_gaps

        if gaps_before == 0:
            return IterationResult(
                iteration=iteration,
                gaps_before=0,
                gaps_after=0,
                gaps_filled=0,
                fill_results=[],
                duration_seconds=0.0,
            )

        # Generate targeted queries
        queries = self.gap_analyzer.generate_fill_queries(gap_result, industry)

        # First, try cross-referencing from related companies
        fill_results = []
        for gap in gap_result.gaps:
            if gap.can_infer_from_competitors and related_companies:
                value = self.gap_analyzer.find_cross_reference_data(
                    target_company=company_name,
                    target_field=gap.field_name,
                    other_companies=related_companies,
                )
                if value:
                    fill_results.append(FillResult(
                        gap=gap,
                        filled=True,
                        value=value,
                        source_url="cross-reference",
                        confidence=0.7,
                    ))

        # Then, run targeted searches for remaining gaps
        unfilled_gaps = [
            g for g in gap_result.gaps
            if not any(fr.gap.field_name == g.field_name and fr.filled for fr in fill_results)
        ]

        # Limit queries per iteration to avoid rate limits
        max_queries_per_iter = 10
        queries_to_run = [
            q for q in queries
            if any(g.field_name == q["target_field"] for g in unfilled_gaps)
        ][:max_queries_per_iter]

        if queries_to_run:
            search_results = await self._run_targeted_searches(queries_to_run)
            extracted = await self._extract_data_points(
                search_results,
                queries_to_run,
                company_name,
            )

            for query, value in extracted.items():
                if value:
                    # Find the gap this query was for
                    target_field = next(
                        (q["target_field"] for q in queries_to_run if q["query"] == query),
                        "Unknown"
                    )
                    matching_gap = next(
                        (g for g in unfilled_gaps if g.field_name == target_field),
                        None
                    )
                    if matching_gap:
                        fill_results.append(FillResult(
                            gap=matching_gap,
                            filled=True,
                            value=value,
                            source_url=query,
                            confidence=0.8,
                        ))

        # Update the research documents with filled values
        filled_count = sum(1 for fr in fill_results if fr.filled)
        if filled_count > 0:
            await self._update_documents(company_name, fill_results)

        # Re-analyze to get accurate gap count
        new_gap_result = self.gap_analyzer.analyze_company(company_name)

        duration = (datetime.now() - start_time).total_seconds()

        return IterationResult(
            iteration=iteration,
            gaps_before=gaps_before,
            gaps_after=new_gap_result.total_gaps,
            gaps_filled=filled_count,
            fill_results=fill_results,
            duration_seconds=duration,
        )

    async def _run_targeted_searches(
        self,
        queries: List[Dict[str, str]],
    ) -> Dict[str, List[Dict]]:
        """Run targeted searches for specific data."""
        search_tool = await self._get_search_tool()
        results = {}

        for query_info in queries:
            query = query_info["query"]
            try:
                search_results = await search_tool.search(query, max_results=3)
                results[query] = search_results
                logger.debug(f"Search '{query[:50]}...' returned {len(search_results)} results")
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
                results[query] = []

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        return results

    async def _extract_data_points(
        self,
        search_results: Dict[str, List[Dict]],
        queries: List[Dict[str, str]],
        company_name: str,
    ) -> Dict[str, Optional[str]]:
        """Use AI to extract specific data points from search results."""
        ai_client = await self._get_ai_client()
        extracted = {}

        for query_info in queries:
            query = query_info["query"]
            target_field = query_info["target_field"]
            results = search_results.get(query, [])

            if not results:
                extracted[query] = None
                continue

            # Build context from search results
            context = "\n\n".join([
                f"Source: {r.get('title', 'Unknown')}\n{r.get('snippet', '')}"
                for r in results[:3]
            ])

            prompt = f"""Extract the {target_field} for {company_name} from the following search results.

SEARCH RESULTS:
{context}

INSTRUCTIONS:
- Extract only the specific {target_field} value
- If found, return ONLY the value (no explanation)
- If not found or unclear, return "NOT_FOUND"
- Be precise with numbers, percentages, dates, etc.

{target_field} for {company_name}:"""

            try:
                response = await ai_client.generate(
                    prompt=prompt,
                    system="You are a data extraction assistant. Extract specific values from search results.",
                    max_tokens=100,
                    temperature=0.1,
                )

                value = response.strip()
                if value and value != "NOT_FOUND" and "not found" not in value.lower():
                    extracted[query] = value
                    logger.info(f"Extracted {target_field}: {value}")
                else:
                    extracted[query] = None

            except Exception as e:
                logger.warning(f"AI extraction failed: {e}")
                extracted[query] = None

        return extracted

    async def _update_documents(
        self,
        company_name: str,
        fill_results: List[FillResult],
    ) -> None:
        """Update research documents with filled values."""
        # Sanitize to match output_manager.py naming
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        safe_name = re.sub(r'[\s_]+', '_', safe_name).strip('_.')
        company_dir = self.base_dir / safe_name

        # Group fills by file
        fills_by_file: Dict[str, List[FillResult]] = {}
        for fr in fill_results:
            if fr.filled and fr.value:
                if fr.gap.file_path not in fills_by_file:
                    fills_by_file[fr.gap.file_path] = []
                fills_by_file[fr.gap.file_path].append(fr)

        # Update each file
        for file_path, fills in fills_by_file.items():
            try:
                path = Path(file_path)
                if not path.exists():
                    continue

                content = path.read_text(encoding="utf-8")

                for fr in fills:
                    # Replace N/A with actual value
                    # Pattern: field_name | N/A or **field_name:** N/A
                    patterns = [
                        (rf'(\|\s*\*\*{re.escape(fr.gap.field_name)}\*\*\s*\|)\s*N/A\s*\|',
                         rf'\1 {fr.value} |'),
                        (rf'(\*\*{re.escape(fr.gap.field_name)}:\*\*)\s*N/A',
                         rf'\1 {fr.value}'),
                        (rf'({re.escape(fr.gap.field_name)}[^|]*\|)[^|]*N/A[^|]*\|',
                         rf'\1 {fr.value} |'),
                    ]

                    for pattern, replacement in patterns:
                        content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
                        if count > 0:
                            logger.debug(f"Replaced {fr.gap.field_name} with {fr.value}")
                            break

                path.write_text(content, encoding="utf-8")
                logger.info(f"Updated {path.name} with {len(fills)} values")

            except Exception as e:
                logger.error(f"Failed to update {file_path}: {e}")


async def fill_market_gaps(
    batch_path: str,
    max_iterations: int = 3,
) -> Dict[str, IterativeResearchResult]:
    """
    Fill gaps for all companies in a market.

    Args:
        batch_path: Path to market folder with YAML profiles
        max_iterations: Max iterations per company

    Returns:
        Dict mapping company name to fill result
    """
    from pathlib import Path
    import yaml

    batch_dir = Path(batch_path)
    results = {}

    # Load company names from profiles
    company_names = []
    for yaml_file in batch_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue
        with open(yaml_file, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
            company_names.append(profile.get("company", {}).get("name", yaml_file.stem))

    # Load market config for industry
    industry = "telecommunications"
    market_yaml = batch_dir / "_market.yaml"
    if market_yaml.exists():
        with open(market_yaml, "r", encoding="utf-8") as f:
            market_config = yaml.safe_load(f)
            industry = market_config.get("market", {}).get("industry", industry)

    # Fill gaps for each company
    service = IterativeResearchService()

    for company in company_names:
        logger.info(f"\n{'='*60}")
        logger.info(f"Filling gaps for: {company}")
        logger.info(f"{'='*60}\n")

        result = await service.fill_gaps(
            company_name=company,
            industry=industry,
            max_iterations=max_iterations,
            related_companies=company_names,
        )
        results[company] = result

        # Print summary
        print(f"\n{company}: {result.initial_gaps} -> {result.final_gaps} gaps "
              f"({result.total_filled} filled in {result.iterations_run} iterations)")

    return results
