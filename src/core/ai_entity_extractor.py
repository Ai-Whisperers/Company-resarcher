"""
AI Entity Extractor - Extracts structured entities from unstructured content.

Uses AI for Named Entity Recognition (NER) to extract:
- People (executives, founders, board members)
- Companies (competitors, partners, subsidiaries)
- Financial figures (revenue, profit, market size)
- Locations (headquarters, offices, markets)
- Products/Services
- Dates and Events

Benefits:
- Better data organization
- Enables cross-referencing across sources
- Structured data for analysis
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import re

from .logger import setup_logger
from .ai_client import get_ai_manager

logger = setup_logger("ai_entity_extractor")


class EntityType(Enum):
    """Types of entities we extract."""
    PERSON = "person"
    COMPANY = "company"
    FINANCIAL = "financial"
    LOCATION = "location"
    PRODUCT = "product"
    DATE = "date"
    EVENT = "event"
    METRIC = "metric"


@dataclass
class Person:
    """Extracted person entity."""
    name: str
    role: str = ""
    company: str = ""
    contact: str = ""
    source: str = ""


@dataclass
class Company:
    """Extracted company entity."""
    name: str
    relationship: str = ""  # competitor, partner, subsidiary, parent
    industry: str = ""
    country: str = ""
    source: str = ""


@dataclass
class Financial:
    """Extracted financial figure."""
    metric: str  # revenue, profit, valuation, etc.
    value: str  # The actual value
    normalized_value: Optional[float] = None  # Normalized to number
    currency: str = "USD"
    period: str = ""  # 2024, Q3 2024, FY2023
    context: str = ""  # Additional context
    source: str = ""


@dataclass
class EntityExtractionResult:
    """Complete extraction result from a source."""
    source_url: str
    source_title: str

    people: List[Person] = field(default_factory=list)
    companies: List[Company] = field(default_factory=list)
    financials: List[Financial] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    events: List[Dict[str, str]] = field(default_factory=list)

    def has_entities(self) -> bool:
        """Check if any entities were extracted."""
        return bool(
            self.people or self.companies or self.financials or
            self.locations or self.products or self.events
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_url": self.source_url,
            "source_title": self.source_title,
            "people": [{"name": p.name, "role": p.role, "company": p.company} for p in self.people],
            "companies": [{"name": c.name, "relationship": c.relationship} for c in self.companies],
            "financials": [{"metric": f.metric, "value": f.value, "period": f.period} for f in self.financials],
            "locations": self.locations,
            "products": self.products,
            "events": self.events,
        }


class AIEntityExtractor:
    """
    Uses AI to extract structured entities from text content.
    """

    MAX_CONTENT_LENGTH = 5000

    def __init__(
        self,
        target_company: str,
        industry: str,
        country: str = "Global",
    ):
        self.target_company = target_company
        self.industry = industry
        self.country = country
        self._ai_client = None
        self._cache: Dict[str, EntityExtractionResult] = {}

    async def _get_ai_client(self):
        """Lazy load AI client."""
        if self._ai_client is None:
            self._ai_client = get_ai_manager()
        return self._ai_client

    async def extract_entities(
        self,
        content: str,
        source_url: str = "",
        source_title: str = "",
    ) -> EntityExtractionResult:
        """
        Extract all entities from content.

        Args:
            content: Text content to analyze
            source_url: URL of the source
            source_title: Title of the source

        Returns:
            EntityExtractionResult with all extracted entities
        """
        # Check cache
        cache_key = f"{source_url}:{hash(content[:500])}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not content or len(content) < 50:
            return EntityExtractionResult(
                source_url=source_url,
                source_title=source_title,
            )

        # Truncate content
        truncated = content[:self.MAX_CONTENT_LENGTH]

        prompt = f"""Extract structured entities from this content about {self.target_company} ({self.industry}) in {self.country}.

Source: {source_title}
URL: {source_url}

Content:
{truncated}

Extract and return JSON:
{{
    "people": [
        {{
            "name": "Full Name",
            "role": "CEO|CFO|Director|etc",
            "company": "Company they work for"
        }}
    ],
    "companies": [
        {{
            "name": "Company Name",
            "relationship": "competitor|partner|subsidiary|parent|customer|supplier",
            "industry": "Their industry"
        }}
    ],
    "financials": [
        {{
            "metric": "revenue|profit|market_cap|funding|market_share|subscribers|etc",
            "value": "Original value with units (e.g., $500M, 2.5 million users)",
            "normalized_value": 500000000,
            "currency": "USD|PYG|ARS|etc",
            "period": "2024|Q3 2024|FY2023",
            "context": "Brief context about this figure"
        }}
    ],
    "locations": ["City, Country", "Region"],
    "products": ["Product/Service 1", "Product/Service 2"],
    "events": [
        {{
            "event": "Event description",
            "date": "When it happened",
            "significance": "Why it matters"
        }}
    ]
}}

IMPORTANT:
- Only extract explicitly mentioned entities
- For financials, always include the original value format AND try to normalize to a number
- For relationships, be specific about how companies are related to {self.target_company}
- Include context for financial figures (what period, what scope)"""

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.generate(
                prompt=prompt,
                system="You are a precise entity extractor. Extract only what's explicitly stated. Return valid JSON only.",
                max_tokens=1500,
                temperature=0.1,
            )

            result = self._parse_extraction(response, source_url, source_title)
            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return EntityExtractionResult(
                source_url=source_url,
                source_title=source_title,
            )

    async def extract_from_multiple(
        self,
        sources: List[Dict[str, str]],
        max_concurrent: int = 5,
    ) -> List[EntityExtractionResult]:
        """
        Extract entities from multiple sources concurrently.

        Args:
            sources: List of dicts with url, title, content
            max_concurrent: Max concurrent extractions

        Returns:
            List of EntityExtractionResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_semaphore(source: Dict[str, str]) -> EntityExtractionResult:
            async with semaphore:
                return await self.extract_entities(
                    content=source.get("content", ""),
                    source_url=source.get("url", ""),
                    source_title=source.get("title", ""),
                )

        return await asyncio.gather(
            *[extract_with_semaphore(s) for s in sources],
            return_exceptions=False,
        )

    def merge_extractions(
        self,
        extractions: List[EntityExtractionResult],
    ) -> EntityExtractionResult:
        """
        Merge multiple extractions, deduplicating entities.

        Args:
            extractions: List of extraction results

        Returns:
            Merged EntityExtractionResult
        """
        merged = EntityExtractionResult(
            source_url="merged",
            source_title=f"Merged from {len(extractions)} sources",
        )

        seen_people = set()
        seen_companies = set()
        seen_financials = set()
        seen_locations = set()
        seen_products = set()

        for extraction in extractions:
            # Merge people
            for person in extraction.people:
                key = f"{person.name}:{person.role}".lower()
                if key not in seen_people:
                    seen_people.add(key)
                    merged.people.append(person)

            # Merge companies
            for company in extraction.companies:
                key = company.name.lower()
                if key not in seen_companies:
                    seen_companies.add(key)
                    merged.companies.append(company)

            # Merge financials (more complex - keep all but note duplicates)
            for fin in extraction.financials:
                key = f"{fin.metric}:{fin.period}".lower()
                if key not in seen_financials:
                    seen_financials.add(key)
                    merged.financials.append(fin)

            # Merge locations
            for loc in extraction.locations:
                if loc.lower() not in seen_locations:
                    seen_locations.add(loc.lower())
                    merged.locations.append(loc)

            # Merge products
            for prod in extraction.products:
                if prod.lower() not in seen_products:
                    seen_products.add(prod.lower())
                    merged.products.append(prod)

            # Merge events (keep all)
            merged.events.extend(extraction.events)

        return merged

    def _parse_extraction(
        self,
        response: str,
        source_url: str,
        source_title: str,
    ) -> EntityExtractionResult:
        """Parse AI response into EntityExtractionResult."""
        result = EntityExtractionResult(
            source_url=source_url,
            source_title=source_title,
        )

        try:
            # Extract JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                return result

            # Parse people
            for p in data.get("people", []):
                if p.get("name"):
                    result.people.append(Person(
                        name=p["name"],
                        role=p.get("role", ""),
                        company=p.get("company", ""),
                        source=source_url,
                    ))

            # Parse companies
            for c in data.get("companies", []):
                if c.get("name"):
                    result.companies.append(Company(
                        name=c["name"],
                        relationship=c.get("relationship", ""),
                        industry=c.get("industry", ""),
                        source=source_url,
                    ))

            # Parse financials
            for f in data.get("financials", []):
                if f.get("metric") and f.get("value"):
                    result.financials.append(Financial(
                        metric=f["metric"],
                        value=f["value"],
                        normalized_value=self._parse_number(f.get("normalized_value")),
                        currency=f.get("currency", "USD"),
                        period=f.get("period", ""),
                        context=f.get("context", ""),
                        source=source_url,
                    ))

            # Parse simple lists
            result.locations = [str(l) for l in data.get("locations", []) if l]
            result.products = [str(p) for p in data.get("products", []) if p]
            result.events = data.get("events", [])

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse extraction: {e}")

        return result

    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse a number from various formats."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove common formatting
            cleaned = re.sub(r'[,$\s]', '', value)
            try:
                return float(cleaned)
            except ValueError:
                pass
        return None

    def get_competitors(
        self,
        extractions: List[EntityExtractionResult],
    ) -> List[Company]:
        """Get all competitor companies from extractions."""
        merged = self.merge_extractions(extractions)
        return [c for c in merged.companies if c.relationship == "competitor"]

    def get_executives(
        self,
        extractions: List[EntityExtractionResult],
    ) -> List[Person]:
        """Get all executives from extractions."""
        merged = self.merge_extractions(extractions)
        executive_roles = {"ceo", "cfo", "cto", "coo", "president", "director", "vp", "chief"}
        return [
            p for p in merged.people
            if any(role in p.role.lower() for role in executive_roles)
        ]

    def get_financial_metrics(
        self,
        extractions: List[EntityExtractionResult],
        metric_type: str = None,
    ) -> List[Financial]:
        """Get financial metrics, optionally filtered by type."""
        merged = self.merge_extractions(extractions)
        if metric_type:
            return [f for f in merged.financials if metric_type.lower() in f.metric.lower()]
        return merged.financials


# Module-level instance
_extractor: Optional[AIEntityExtractor] = None


def get_entity_extractor(
    target_company: str,
    industry: str,
    country: str = "Global",
) -> AIEntityExtractor:
    """Get or create an entity extractor."""
    global _extractor
    if _extractor is None or _extractor.target_company != target_company:
        _extractor = AIEntityExtractor(
            target_company=target_company,
            industry=industry,
            country=country,
        )
    return _extractor


def reset_entity_extractor():
    """Reset the extractor."""
    global _extractor
    _extractor = None


__all__ = [
    "AIEntityExtractor",
    "EntityExtractionResult",
    "EntityType",
    "Person",
    "Company",
    "Financial",
    "get_entity_extractor",
    "reset_entity_extractor",
]
