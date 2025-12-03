"""
Glassdoor integration tool for Company Researcher.

INT-001: Provides employee sentiment, company reviews, and culture data.

This tool uses web scraping as Glassdoor has limited API access.
For production use, consider using RapidAPI's Glassdoor scraper or similar.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import quote_plus

from src.core.config import get_settings
from src.core.network.http_client import get_http_client

logger = logging.getLogger(__name__)


@dataclass
class GlassdoorReview:
    """Individual Glassdoor review data."""
    rating: float
    title: str
    pros: str
    cons: str
    advice_to_management: Optional[str] = None
    date: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    is_current_employee: bool = False


@dataclass
class GlassdoorCompanyData:
    """Glassdoor company overview data."""
    company_name: str
    overall_rating: Optional[float] = None
    recommend_to_friend: Optional[float] = None
    ceo_approval: Optional[float] = None
    ceo_name: Optional[str] = None
    total_reviews: int = 0
    headquarters: Optional[str] = None
    size: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None
    revenue: Optional[str] = None
    website: Optional[str] = None

    # Rating breakdowns
    culture_rating: Optional[float] = None
    diversity_rating: Optional[float] = None
    work_life_rating: Optional[float] = None
    senior_mgmt_rating: Optional[float] = None
    comp_benefits_rating: Optional[float] = None
    career_opp_rating: Optional[float] = None

    # Recent reviews
    reviews: List[GlassdoorReview] = None

    def __post_init__(self):
        if self.reviews is None:
            self.reviews = []


class GlassdoorTool:
    """
    Tool for retrieving Glassdoor company and review data.

    Note: Glassdoor has strict anti-scraping measures. This tool provides
    a framework that can be connected to:
    - RapidAPI Glassdoor scraper
    - Custom scraping solution
    - Glassdoor Partner API (if available)

    Usage:
        tool = GlassdoorTool()
        data = await tool.get_company_data("Apple")
        reviews = await tool.get_recent_reviews("Apple", limit=10)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Glassdoor tool.

        Args:
            api_key: API key for Glassdoor scraper service (e.g., RapidAPI)
        """
        # Use centralized settings (ARCH-004)
        settings = get_settings()
        self.api_key = api_key or settings.integrations.glassdoor_api_key
        self.rapidapi_host = settings.integrations.glassdoor_rapidapi_host
        self._http_client = get_http_client()

    async def get_company_data(self, company_name: str) -> Optional[GlassdoorCompanyData]:
        """
        Get company overview data from Glassdoor.

        Args:
            company_name: Name of the company to search

        Returns:
            GlassdoorCompanyData object or None if not found
        """
        if not self.api_key:
            logger.warning("Glassdoor API key not configured. Using search-based fallback.")
            return await self._fallback_company_search(company_name)

        try:
            # RapidAPI-style request
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.rapidapi_host,
            }

            url = f"https://{self.rapidapi_host}/company/{quote_plus(company_name)}"
            response = await self._http_client.get(
                url,
                rate_limit_key="glassdoor",
                headers=headers,
            )

            async with response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_company_response(data)
                else:
                    logger.warning(f"Glassdoor API error: {response.status}")
                    return await self._fallback_company_search(company_name)

        except Exception as e:
            logger.error(f"Error fetching Glassdoor data: {e}")
            return await self._fallback_company_search(company_name)

    async def get_recent_reviews(
        self,
        company_name: str,
        limit: int = 10,
    ) -> List[GlassdoorReview]:
        """
        Get recent reviews for a company.

        Args:
            company_name: Company name
            limit: Maximum number of reviews to return

        Returns:
            List of GlassdoorReview objects
        """
        if not self.api_key:
            logger.warning("Glassdoor API key not configured. Cannot fetch reviews.")
            return []

        try:
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.rapidapi_host,
            }

            url = f"https://{self.rapidapi_host}/reviews/{quote_plus(company_name)}"
            response = await self._http_client.get(
                url,
                rate_limit_key="glassdoor",
                headers=headers,
                params={"limit": limit},
            )

            async with response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_reviews_response(data)
                else:
                    logger.warning(f"Glassdoor reviews API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching Glassdoor reviews: {e}")
            return []

    async def get_salary_data(
        self,
        company_name: str,
        job_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get salary data for a company.

        Args:
            company_name: Company name
            job_title: Optional specific job title to filter

        Returns:
            Dictionary with salary information
        """
        if not self.api_key:
            return {"error": "API key not configured", "salaries": []}

        try:
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.rapidapi_host,
            }

            params = {}
            if job_title:
                params["job_title"] = job_title

            url = f"https://{self.rapidapi_host}/salaries/{quote_plus(company_name)}"
            response = await self._http_client.get(
                url,
                rate_limit_key="glassdoor",
                headers=headers,
                params=params,
            )

            async with response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"API error: {response.status}", "salaries": []}

        except Exception as e:
            return {"error": str(e), "salaries": []}

    async def _fallback_company_search(self, company_name: str) -> Optional[GlassdoorCompanyData]:
        """
        Fallback method using search queries to gather Glassdoor data.

        This generates a search-based result structure without actual scraping.
        """
        # Return a placeholder that indicates data should be gathered via search
        return GlassdoorCompanyData(
            company_name=company_name,
            overall_rating=None,
            total_reviews=0,
        )

    def _parse_company_response(self, data: Dict) -> GlassdoorCompanyData:
        """Parse API response into GlassdoorCompanyData."""
        return GlassdoorCompanyData(
            company_name=data.get("name", "Unknown"),
            overall_rating=self._safe_float(data.get("overallRating")),
            recommend_to_friend=self._safe_float(data.get("recommendToFriend")),
            ceo_approval=self._safe_float(data.get("ceoApproval")),
            ceo_name=data.get("ceoName"),
            total_reviews=data.get("numberOfReviews", 0),
            headquarters=data.get("headquarters"),
            size=data.get("size"),
            founded=data.get("founded"),
            industry=data.get("industry"),
            revenue=data.get("revenue"),
            website=data.get("website"),
            culture_rating=self._safe_float(data.get("cultureRating")),
            diversity_rating=self._safe_float(data.get("diversityRating")),
            work_life_rating=self._safe_float(data.get("workLifeRating")),
            senior_mgmt_rating=self._safe_float(data.get("seniorManagementRating")),
            comp_benefits_rating=self._safe_float(data.get("compBenefitsRating")),
            career_opp_rating=self._safe_float(data.get("careerOppRating")),
        )

    def _parse_reviews_response(self, data: Dict) -> List[GlassdoorReview]:
        """Parse API response into list of GlassdoorReview objects."""
        reviews = []
        for item in data.get("reviews", []):
            reviews.append(GlassdoorReview(
                rating=self._safe_float(item.get("rating", 0)),
                title=item.get("title", ""),
                pros=item.get("pros", ""),
                cons=item.get("cons", ""),
                advice_to_management=item.get("adviceToManagement"),
                date=item.get("date"),
                job_title=item.get("jobTitle"),
                location=item.get("location"),
                is_current_employee=item.get("isCurrentEmployee", False),
            ))
        return reviews

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def format_for_research(self, data: GlassdoorCompanyData) -> str:
        """
        Format Glassdoor data for inclusion in research context.

        Args:
            data: GlassdoorCompanyData object

        Returns:
            Formatted string for research context
        """
        lines = [f"## Glassdoor Data for {data.company_name}\n"]

        if data.overall_rating:
            lines.append(f"**Overall Rating:** {data.overall_rating}/5.0")
        if data.total_reviews:
            lines.append(f"**Total Reviews:** {data.total_reviews:,}")
        if data.recommend_to_friend:
            lines.append(f"**Recommend to Friend:** {data.recommend_to_friend}%")
        if data.ceo_approval:
            lines.append(f"**CEO Approval:** {data.ceo_approval}%")
            if data.ceo_name:
                lines.append(f"**CEO:** {data.ceo_name}")

        # Rating breakdown
        ratings = []
        if data.culture_rating:
            ratings.append(f"Culture: {data.culture_rating}/5")
        if data.work_life_rating:
            ratings.append(f"Work-Life: {data.work_life_rating}/5")
        if data.comp_benefits_rating:
            ratings.append(f"Comp & Benefits: {data.comp_benefits_rating}/5")
        if data.career_opp_rating:
            ratings.append(f"Career Opportunities: {data.career_opp_rating}/5")
        if data.senior_mgmt_rating:
            ratings.append(f"Senior Management: {data.senior_mgmt_rating}/5")

        if ratings:
            lines.append("\n**Rating Breakdown:**")
            for r in ratings:
                lines.append(f"- {r}")

        # Company info
        if data.industry or data.size or data.headquarters:
            lines.append("\n**Company Info:**")
            if data.industry:
                lines.append(f"- Industry: {data.industry}")
            if data.size:
                lines.append(f"- Size: {data.size}")
            if data.headquarters:
                lines.append(f"- HQ: {data.headquarters}")

        # Recent reviews summary
        if data.reviews:
            lines.append(f"\n**Recent Reviews ({len(data.reviews)}):**")
            for i, review in enumerate(data.reviews[:3], 1):
                lines.append(f"\n{i}. {review.title} ({review.rating}/5)")
                if review.pros:
                    lines.append(f"   Pros: {review.pros[:150]}...")
                if review.cons:
                    lines.append(f"   Cons: {review.cons[:150]}...")

        return "\n".join(lines)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
