"""
USPTO Patent Search Tool using the free PatentsView API.

Provides patent portfolio analysis for companies including:
- Patent counts and trends
- Technology classifications
- Innovation velocity metrics
- Key inventors

API Documentation: https://patentsview.org/apis/api-endpoints
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import aiohttp

from ...core.logging import setup_logger

logger = setup_logger("patent_tool")

# PatentsView API base URL (free, no API key required)
PATENTSVIEW_API_URL = "https://api.patentsview.org/patents/query"
PATENTSVIEW_ASSIGNEES_URL = "https://api.patentsview.org/assignees/query"

# Request timeout
REQUEST_TIMEOUT = 30


@dataclass
class Patent:
    """Represents a single patent."""

    patent_id: str
    title: str
    abstract: str
    date: str
    inventors: List[str]
    classifications: List[str]
    citation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patent_id": self.patent_id,
            "title": self.title,
            "abstract": self.abstract[:500] if self.abstract else "",
            "date": self.date,
            "inventors": self.inventors[:5],  # Limit to top 5
            "classifications": self.classifications[:5],
            "citation_count": self.citation_count,
        }


@dataclass
class PatentMetrics:
    """Aggregated patent metrics for a company."""

    total_patents: int = 0
    patents_last_5_years: int = 0
    patents_last_year: int = 0
    top_classifications: List[Dict[str, Any]] = field(default_factory=list)
    top_inventors: List[Dict[str, Any]] = field(default_factory=list)
    innovation_velocity: float = 0.0  # Patents per year (last 5 years)
    recent_patents: List[Patent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_patents": self.total_patents,
            "patents_last_5_years": self.patents_last_5_years,
            "patents_last_year": self.patents_last_year,
            "innovation_velocity": round(self.innovation_velocity, 2),
            "top_classifications": self.top_classifications,
            "top_inventors": self.top_inventors,
            "recent_patents": [p.to_dict() for p in self.recent_patents[:10]],
        }


class PatentSearchTool:
    """
    Tool for searching USPTO patents via the free PatentsView API.

    Features:
    - Search patents by company/assignee name
    - Get patent counts and trends
    - Analyze technology classifications
    - Identify key inventors
    - Calculate innovation metrics

    Usage:
        tool = PatentSearchTool()
        metrics = await tool.get_patent_metrics("Apple Inc")
        patents = await tool.search_patents("Apple Inc", limit=20)
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_cache_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key for a query."""
        key_str = f"{query}:{str(sorted(params.items()))}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _make_request(
        self,
        url: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Make API request to PatentsView."""
        try:
            session = await self._get_session()

            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"PatentsView API returned status {response.status}"
                    )
                    return None

        except asyncio.TimeoutError:
            logger.error("PatentsView API request timed out")
            return None
        except Exception as e:
            logger.error(f"PatentsView API error: {e}")
            return None

    async def search_patents(
        self,
        assignee_name: str,
        limit: int = 25,
        start_date: Optional[str] = None,
    ) -> List[Patent]:
        """
        Search patents by assignee (company) name.

        Args:
            assignee_name: Company name to search for
            limit: Maximum number of patents to return
            start_date: Optional start date filter (YYYY-MM-DD)

        Returns:
            List of Patent objects
        """
        # Build query
        query_criteria = [
            {"_contains": {"assignee_organization": assignee_name}}
        ]

        if start_date:
            query_criteria.append(
                {"_gte": {"patent_date": start_date}}
            )

        query = {"_and": query_criteria} if len(query_criteria) > 1 else query_criteria[0]

        payload = {
            "q": query,
            "f": [
                "patent_id",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "inventor_first_name",
                "inventor_last_name",
                "cpc_subgroup_id",
                "citedby_patent_number",
            ],
            "o": {
                "per_page": min(limit, 100),
                "page": 1,
            },
            "s": [{"patent_date": "desc"}],
        }

        # Check cache
        cache_key = self._get_cache_key(assignee_name, {"limit": limit, "start": start_date})
        if cache_key in self._cache:
            logger.debug(f"Cache hit for patent search: {assignee_name}")
            return self._cache[cache_key]

        result = await self._make_request(PATENTSVIEW_API_URL, payload)

        if not result or "patents" not in result:
            return []

        patents = []
        for p in result.get("patents", []):
            # Extract inventors
            inventors = []
            if p.get("inventors"):
                for inv in p["inventors"][:10]:
                    name = f"{inv.get('inventor_first_name', '')} {inv.get('inventor_last_name', '')}".strip()
                    if name:
                        inventors.append(name)

            # Extract classifications
            classifications = []
            if p.get("cpcs"):
                classifications = list(set(
                    cpc.get("cpc_subgroup_id", "")
                    for cpc in p["cpcs"][:10]
                    if cpc.get("cpc_subgroup_id")
                ))

            # Count citations
            citation_count = len(p.get("citedby_patents", []) or [])

            patent = Patent(
                patent_id=p.get("patent_id", ""),
                title=p.get("patent_title", ""),
                abstract=p.get("patent_abstract", ""),
                date=p.get("patent_date", ""),
                inventors=inventors,
                classifications=classifications,
                citation_count=citation_count,
            )
            patents.append(patent)

        # Cache results
        self._cache[cache_key] = patents
        logger.info(f"Found {len(patents)} patents for '{assignee_name}'")

        return patents

    async def get_patent_count(
        self,
        assignee_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> int:
        """
        Get total patent count for an assignee.

        Args:
            assignee_name: Company name
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Total patent count
        """
        query_criteria = [
            {"_contains": {"assignee_organization": assignee_name}}
        ]

        if start_date:
            query_criteria.append({"_gte": {"patent_date": start_date}})
        if end_date:
            query_criteria.append({"_lte": {"patent_date": end_date}})

        query = {"_and": query_criteria} if len(query_criteria) > 1 else query_criteria[0]

        payload = {
            "q": query,
            "f": ["patent_id"],
            "o": {"per_page": 1, "page": 1},
        }

        result = await self._make_request(PATENTSVIEW_API_URL, payload)

        if result:
            return result.get("total_patent_count", 0)
        return 0

    async def get_patent_metrics(self, assignee_name: str) -> PatentMetrics:
        """
        Get comprehensive patent metrics for a company.

        Args:
            assignee_name: Company name to analyze

        Returns:
            PatentMetrics with aggregated statistics
        """
        metrics = PatentMetrics()

        current_year = datetime.now().year
        five_years_ago = f"{current_year - 5}-01-01"
        one_year_ago = f"{current_year - 1}-01-01"

        # Get counts in parallel
        total_task = self.get_patent_count(assignee_name)
        five_year_task = self.get_patent_count(assignee_name, start_date=five_years_ago)
        one_year_task = self.get_patent_count(assignee_name, start_date=one_year_ago)
        recent_patents_task = self.search_patents(assignee_name, limit=25)

        results = await asyncio.gather(
            total_task,
            five_year_task,
            one_year_task,
            recent_patents_task,
            return_exceptions=True,
        )

        # Process results
        if not isinstance(results[0], Exception):
            metrics.total_patents = results[0]

        if not isinstance(results[1], Exception):
            metrics.patents_last_5_years = results[1]
            metrics.innovation_velocity = metrics.patents_last_5_years / 5.0

        if not isinstance(results[2], Exception):
            metrics.patents_last_year = results[2]

        if not isinstance(results[3], Exception):
            metrics.recent_patents = results[3]

            # Analyze classifications from recent patents
            classification_counts: Dict[str, int] = {}
            inventor_counts: Dict[str, int] = {}

            for patent in metrics.recent_patents:
                for cls in patent.classifications:
                    classification_counts[cls] = classification_counts.get(cls, 0) + 1
                for inv in patent.inventors:
                    inventor_counts[inv] = inventor_counts.get(inv, 0) + 1

            # Top classifications
            metrics.top_classifications = [
                {"classification": k, "count": v}
                for k, v in sorted(
                    classification_counts.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ]

            # Top inventors
            metrics.top_inventors = [
                {"name": k, "patent_count": v}
                for k, v in sorted(
                    inventor_counts.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ]

        logger.info(
            f"Patent metrics for '{assignee_name}': "
            f"{metrics.total_patents} total, "
            f"{metrics.patents_last_5_years} in last 5 years"
        )

        return metrics

    async def analyze_innovation(self, assignee_name: str) -> Dict[str, Any]:
        """
        Analyze innovation trends and provide insights.

        Args:
            assignee_name: Company name

        Returns:
            Dictionary with innovation analysis
        """
        metrics = await self.get_patent_metrics(assignee_name)

        # Calculate trends
        trend = "stable"
        if metrics.patents_last_year > 0 and metrics.patents_last_5_years > 0:
            yearly_avg = metrics.patents_last_5_years / 5
            if metrics.patents_last_year > yearly_avg * 1.2:
                trend = "increasing"
            elif metrics.patents_last_year < yearly_avg * 0.8:
                trend = "decreasing"

        # Determine innovation score (0-100)
        innovation_score = min(100, int(
            (metrics.innovation_velocity * 5) +  # Weight velocity
            (len(metrics.top_classifications) * 3) +  # Diversity bonus
            (metrics.patents_last_year * 2)  # Recent activity bonus
        ))

        return {
            "company": assignee_name,
            "metrics": metrics.to_dict(),
            "innovation_trend": trend,
            "innovation_score": innovation_score,
            "analysis": {
                "total_portfolio": metrics.total_patents,
                "recent_activity": f"{metrics.patents_last_year} patents in the last year",
                "velocity": f"{metrics.innovation_velocity:.1f} patents/year (5-year avg)",
                "technology_focus": [
                    c["classification"] for c in metrics.top_classifications[:3]
                ],
                "key_inventors": [
                    i["name"] for i in metrics.top_inventors[:3]
                ],
            },
        }


# Convenience function for one-off searches
async def search_company_patents(
    company_name: str,
    limit: int = 25,
) -> Dict[str, Any]:
    """
    Convenience function to search patents for a company.

    Args:
        company_name: Company name to search
        limit: Maximum patents to return

    Returns:
        Dictionary with patents and metrics
    """
    tool = PatentSearchTool()
    try:
        analysis = await tool.analyze_innovation(company_name)
        return analysis
    finally:
        await tool.close()
