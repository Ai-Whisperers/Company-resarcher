"""
Adaptive Query Strategy (PERF-017).

Adjusts search query strategy based on company profile/presence level.
For companies with limited online presence, uses broader, less specific queries.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from .logger import setup_logger
from .company_probe import CompanyPresence, RESEARCH_PROFILES

logger = setup_logger("adaptive_query_strategy")


class QueryStrategy(Enum):
    """Query strategy based on company presence."""
    FULL = "full"           # Full queries with exact match
    FOCUSED = "focused"     # Reduced queries, less specificity
    BASIC = "basic"         # Minimal queries, broad terms only


@dataclass
class QueryModification:
    """Result of query modification."""
    original: str
    modified: str
    strategy: QueryStrategy
    changes: List[str]


class AdaptiveQueryStrategy:
    """
    Adapts search queries based on company's online presence.

    For companies with limited presence:
    - Removes exact-match quotes (broadens search)
    - Removes redundant company name repetitions
    - Uses industry-generic terms instead of company-specific
    - Reduces number of queries per section

    Usage:
        strategy = AdaptiveQueryStrategy(presence=CompanyPresence.LIMITED)
        modified_queries = strategy.adapt_queries(queries, company="Vox Paraguay")
    """

    # Words that don't add value to limited-presence searches
    LOW_VALUE_TERMS = {
        "target", "customers", "customer segments", "b2b", "b2c",
        "smb", "small business", "enterprise", "demographics",
        "acquisition cost", "lifetime value", "persona",
    }

    # Fallback industry terms for specific verticals
    INDUSTRY_FALLBACKS = {
        "telecommunications": ["telecom", "mobile operator", "ISP", "carrier"],
        "mvno": ["mobile virtual", "telecom", "wireless"],
        "fintech": ["financial technology", "payments", "banking"],
        "ecommerce": ["online retail", "shopping", "marketplace"],
        "saas": ["software", "cloud", "platform"],
    }

    def __init__(
        self,
        presence: CompanyPresence,
        company: str = "",
        industry: str = "",
        country: str = "",
    ):
        self.presence = presence
        self.company = company
        self.industry = industry.lower()
        self.country = country

        # Get strategy from presence
        if presence == CompanyPresence.MINIMAL:
            self.strategy = QueryStrategy.BASIC
        elif presence == CompanyPresence.LIMITED:
            self.strategy = QueryStrategy.FOCUSED
        else:
            self.strategy = QueryStrategy.FULL

        # Get profile settings
        self.profile = RESEARCH_PROFILES.get(presence, RESEARCH_PROFILES[CompanyPresence.UNKNOWN])

        logger.info(
            f"Adaptive query strategy initialized: {self.strategy.value} "
            f"(presence={presence.value}, queries_per_section={self.profile['queries_per_section']})"
        )

    def adapt_queries(
        self,
        queries: List[str],
        max_queries: Optional[int] = None,
    ) -> List[str]:
        """
        Adapt a list of queries based on company presence.

        Args:
            queries: Original query list
            max_queries: Override max queries (uses profile default if None)

        Returns:
            Adapted query list
        """
        if self.strategy == QueryStrategy.FULL:
            return queries  # No modification needed

        # Determine max queries
        limit = max_queries or self.profile["queries_per_section"]

        adapted = []
        seen_bases = set()  # Avoid duplicate query bases

        for query in queries:
            modified = self._modify_query(query)

            # Skip if we've seen a similar query
            base = self._get_query_base(modified.modified)
            if base in seen_bases:
                continue
            seen_bases.add(base)

            adapted.append(modified.modified)

            if len(adapted) >= limit:
                break

        # Add industry fallback queries if we have too few
        if len(adapted) < 3 and self.industry:
            fallbacks = self._get_industry_fallback_queries()
            for fb in fallbacks:
                if fb not in adapted and len(adapted) < limit:
                    adapted.append(fb)

        logger.debug(
            f"Adapted {len(queries)} queries to {len(adapted)} "
            f"(strategy={self.strategy.value})"
        )

        return adapted

    def _modify_query(self, query: str) -> QueryModification:
        """Modify a single query based on strategy."""
        changes = []
        modified = query

        if self.strategy == QueryStrategy.BASIC:
            # Most aggressive simplification
            modified, c = self._remove_exact_match(modified)
            changes.extend(c)

            modified, c = self._remove_redundant_company(modified)
            changes.extend(c)

            modified, c = self._remove_low_value_terms(modified)
            changes.extend(c)

            modified, c = self._simplify_to_core(modified)
            changes.extend(c)

        elif self.strategy == QueryStrategy.FOCUSED:
            # Moderate simplification
            modified, c = self._remove_exact_match(modified)
            changes.extend(c)

            modified, c = self._remove_redundant_company(modified)
            changes.extend(c)

        # Clean up whitespace
        modified = " ".join(modified.split())

        return QueryModification(
            original=query,
            modified=modified,
            strategy=self.strategy,
            changes=changes,
        )

    def _remove_exact_match(self, query: str) -> Tuple[str, List[str]]:
        """Remove exact-match quotes to broaden search."""
        changes = []

        # Find quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        if quoted:
            # Remove quotes but keep the content
            modified = re.sub(r'"([^"]+)"', r'\1', query)
            changes.append(f"removed quotes from: {quoted}")
            return modified, changes

        return query, changes

    def _remove_redundant_company(self, query: str) -> Tuple[str, List[str]]:
        """Remove redundant company name mentions."""
        changes = []

        if not self.company:
            return query, changes

        # Count company name occurrences
        company_lower = self.company.lower()
        query_lower = query.lower()
        count = query_lower.count(company_lower)

        if count > 1:
            # Keep only first occurrence
            parts = query_lower.split(company_lower)
            modified = parts[0] + self.company + company_lower.join(parts[2:]) if len(parts) > 2 else query
            changes.append(f"reduced company name from {count} to 1 occurrence")
            return modified, changes

        return query, changes

    def _remove_low_value_terms(self, query: str) -> Tuple[str, List[str]]:
        """Remove low-value terms for limited companies."""
        changes = []
        query_lower = query.lower()

        removed = []
        for term in self.LOW_VALUE_TERMS:
            if term in query_lower:
                query = re.sub(re.escape(term), '', query, flags=re.IGNORECASE)
                removed.append(term)

        if removed:
            changes.append(f"removed low-value terms: {removed}")

        return query, changes

    def _simplify_to_core(self, query: str) -> Tuple[str, List[str]]:
        """Simplify query to core terms only."""
        changes = []

        # Extract just company name + one key term
        words = query.split()
        if len(words) > 5:
            # Keep company name and most important words
            core_words = []

            # Always include company name parts
            if self.company:
                for part in self.company.split():
                    if part.lower() in query.lower():
                        core_words.append(part)

            # Add country if present
            if self.country and self.country.lower() in query.lower():
                core_words.append(self.country)

            # Add one industry term
            for word in words:
                if word.lower() in ["revenue", "market", "news", "financials", "competitors"]:
                    core_words.append(word)
                    break

            if core_words:
                modified = " ".join(core_words)
                if len(modified) > len(query) * 0.3:  # Only if significant simplification
                    changes.append(f"simplified from {len(words)} to {len(core_words)} words")
                    return modified, changes

        return query, changes

    def _get_query_base(self, query: str) -> str:
        """Get base form of query for deduplication."""
        # Remove common words and normalize
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of"}
        words = query.lower().split()
        significant = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(sorted(significant[:3]))  # First 3 significant words, sorted

    def _get_industry_fallback_queries(self) -> List[str]:
        """Generate fallback queries based on industry."""
        fallbacks = []

        # Get industry-specific terms
        terms = []
        for key, values in self.INDUSTRY_FALLBACKS.items():
            if key in self.industry:
                terms.extend(values)

        if not terms:
            terms = ["company", "business", "market"]

        # Generate simple fallback queries
        for term in terms[:3]:
            if self.company:
                fallbacks.append(f"{self.company} {term}")
            if self.country:
                fallbacks.append(f"{term} {self.country}")

        return fallbacks

    def get_recommended_query_count(self, section: str) -> int:
        """Get recommended number of queries for a section."""
        base = self.profile["queries_per_section"]

        # Some sections are more likely to have results
        high_yield_sections = ["strategic_context", "competitive_landscape", "market_intelligence"]
        low_yield_sections = ["creative_inspiration", "investment_analysis"]

        if section in high_yield_sections:
            return base
        elif section in low_yield_sections:
            return max(1, base // 2)
        else:
            return base

    def should_skip_section(self, section: str) -> bool:
        """Check if a section should be skipped based on presence."""
        if self.strategy == QueryStrategy.FULL:
            return False

        sections_config = self.profile.get("sections", "all")
        if sections_config == "all":
            return False

        return section not in sections_config


# Factory function
def get_query_strategy(
    presence: CompanyPresence,
    company: str = "",
    industry: str = "",
    country: str = "",
) -> AdaptiveQueryStrategy:
    """Get adaptive query strategy for a company presence level."""
    return AdaptiveQueryStrategy(
        presence=presence,
        company=company,
        industry=industry,
        country=country,
    )


__all__ = [
    "AdaptiveQueryStrategy",
    "QueryStrategy",
    "QueryModification",
    "get_query_strategy",
]
