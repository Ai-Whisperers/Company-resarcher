"""
Enhanced Search Fallback (PERF-020).

Provides intelligent search query fallback strategies when primary queries fail.
Works with the SearchTool to automatically retry with modified queries.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from ..logging import setup_logger

logger = setup_logger("search_fallback")


class FallbackStrategy(Enum):
    """Types of fallback strategies."""
    REMOVE_QUOTES = "remove_quotes"         # Remove exact-match quotes
    BROADEN_TERMS = "broaden_terms"         # Use broader/simpler terms
    TRANSLATE = "translate"                  # Try Spanish/English variants
    SIMPLIFY = "simplify"                   # Keep only core terms
    ALTERNATIVE = "alternative"             # Use completely different query


@dataclass
class FallbackResult:
    """Result of a fallback attempt."""
    original_query: str
    fallback_query: str
    strategy: FallbackStrategy
    success: bool
    results_count: int = 0


class SearchFallbackManager:
    """
    Manages intelligent fallback strategies for failed searches.

    When a search returns no results or times out, this manager
    generates alternative queries that are more likely to succeed.

    Usage:
        fallback = SearchFallbackManager()

        results = await search(query)
        if not results:
            for fallback_query in fallback.get_fallbacks(query):
                results = await search(fallback_query)
                if results:
                    break
    """

    # Common terms to simplify
    VERBOSE_TO_SIMPLE = {
        "target customers": "customers",
        "customer segments": "customers",
        "market positioning": "positioning",
        "brand differentiation": "brand",
        "competitive landscape": "competitors",
        "financial performance": "revenue",
        "revenue growth": "revenue",
        "market share": "market",
        "digital marketing": "marketing",
        "social media marketing": "marketing",
        "unique selling proposition": "USP",
    }

    # Terms to remove as they rarely help
    NOISE_TERMS = {
        "2024", "2025", "latest", "recent", "new",
        "analysis", "report", "study", "research",
        "comprehensive", "detailed", "complete",
    }

    # Spanish-English translation pairs for common terms
    TRANSLATIONS = {
        "empresa": "company",
        "compañía": "company",
        "ingresos": "revenue",
        "mercado": "market",
        "competidores": "competitors",
        "clientes": "customers",
        "noticias": "news",
        "financiero": "financial",
        "productos": "products",
        "servicios": "services",
    }

    def __init__(
        self,
        company: str = "",
        country: str = "",
        max_fallbacks: int = 3,
    ):
        self.company = company
        self.country = country
        self.max_fallbacks = max_fallbacks
        self._attempted_queries: set = set()

    def get_fallbacks(
        self,
        query: str,
        strategies: Optional[List[FallbackStrategy]] = None,
    ) -> List[str]:
        """
        Generate fallback queries for a failed search.

        Args:
            query: Original query that failed
            strategies: Specific strategies to use (or auto-detect)

        Returns:
            List of alternative queries to try
        """
        if strategies is None:
            strategies = self._detect_strategies(query)

        fallbacks = []

        for strategy in strategies:
            fallback = self._apply_strategy(query, strategy)
            if fallback and fallback not in self._attempted_queries and fallback != query:
                fallbacks.append(fallback)
                self._attempted_queries.add(fallback)

            if len(fallbacks) >= self.max_fallbacks:
                break

        logger.debug(f"Generated {len(fallbacks)} fallback queries for: {query[:50]}...")
        return fallbacks

    def _detect_strategies(self, query: str) -> List[FallbackStrategy]:
        """Detect which fallback strategies are applicable."""
        strategies = []

        # If query has quotes, try without them first
        if '"' in query:
            strategies.append(FallbackStrategy.REMOVE_QUOTES)

        # If query has verbose terms, simplify
        query_lower = query.lower()
        if any(term in query_lower for term in self.VERBOSE_TO_SIMPLE):
            strategies.append(FallbackStrategy.BROADEN_TERMS)

        # If query is long, try simplification
        if len(query.split()) > 5:
            strategies.append(FallbackStrategy.SIMPLIFY)

        # Always try an alternative as last resort
        strategies.append(FallbackStrategy.ALTERNATIVE)

        return strategies

    def _apply_strategy(
        self,
        query: str,
        strategy: FallbackStrategy,
    ) -> Optional[str]:
        """Apply a specific fallback strategy to a query."""
        if strategy == FallbackStrategy.REMOVE_QUOTES:
            return self._remove_quotes(query)
        elif strategy == FallbackStrategy.BROADEN_TERMS:
            return self._broaden_terms(query)
        elif strategy == FallbackStrategy.TRANSLATE:
            return self._translate(query)
        elif strategy == FallbackStrategy.SIMPLIFY:
            return self._simplify(query)
        elif strategy == FallbackStrategy.ALTERNATIVE:
            return self._create_alternative(query)

        return None

    def _remove_quotes(self, query: str) -> str:
        """Remove exact-match quotes from query."""
        return re.sub(r'"([^"]+)"', r'\1', query)

    def _broaden_terms(self, query: str) -> str:
        """Replace verbose terms with simpler ones."""
        result = query.lower()
        for verbose, simple in self.VERBOSE_TO_SIMPLE.items():
            result = result.replace(verbose, simple)

        # Also remove noise terms
        for noise in self.NOISE_TERMS:
            result = re.sub(r'\b' + noise + r'\b', '', result, flags=re.IGNORECASE)

        return " ".join(result.split())  # Clean up whitespace

    def _translate(self, query: str) -> str:
        """Translate Spanish terms to English or vice versa."""
        result = query
        for es, en in self.TRANSLATIONS.items():
            if es in query.lower():
                result = re.sub(es, en, result, flags=re.IGNORECASE)
            elif en in query.lower():
                result = re.sub(en, es, result, flags=re.IGNORECASE)

        return result

    def _simplify(self, query: str) -> str:
        """Simplify query to core terms only."""
        words = query.split()

        # Keep company name if present
        core = []
        if self.company:
            for part in self.company.split():
                if part.lower() in query.lower():
                    core.append(part)

        # Add country if present
        if self.country:
            core.append(self.country)

        # Add one meaningful word from query
        meaningful = ["revenue", "market", "news", "competitors", "customers", "products"]
        for word in words:
            if word.lower() in meaningful:
                core.append(word)
                break

        # If we found meaningful terms, use them
        if len(core) >= 2:
            return " ".join(core)

        # Otherwise just take first few significant words
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of"}
        significant = [w for w in words if w.lower() not in stop_words and len(w) > 2]
        return " ".join(significant[:4])

    def _create_alternative(self, query: str) -> str:
        """Create a completely different but related query."""
        # Extract what seems to be the intent
        query_lower = query.lower()

        # Determine query category and create alternative
        if any(term in query_lower for term in ["revenue", "financial", "profit", "earnings"]):
            if self.company:
                return f"{self.company} company financials"
            return f"company financials {self.country}"

        elif any(term in query_lower for term in ["competitor", "competition", "versus", "vs"]):
            if self.company:
                return f"{self.company} competitors"
            return f"top companies {self.country}"

        elif any(term in query_lower for term in ["customer", "client", "user", "buyer"]):
            if self.company:
                return f"{self.company} customers"
            return f"market customers {self.country}"

        elif any(term in query_lower for term in ["news", "recent", "latest", "update"]):
            if self.company:
                return f"{self.company} news"
            return f"news {self.country}"

        # Generic fallback
        if self.company:
            return f"{self.company} {self.country}"
        return query[:50]  # Just truncate as last resort

    def record_success(self, original: str, fallback: str, strategy: FallbackStrategy) -> None:
        """Record a successful fallback for analytics."""
        logger.info(
            f"Fallback success: '{original[:30]}...' -> '{fallback[:30]}...' "
            f"({strategy.value})"
        )

    def reset(self) -> None:
        """Reset attempted queries for a new research session."""
        self._attempted_queries.clear()


# Convenience function
def get_fallback_queries(
    query: str,
    company: str = "",
    country: str = "",
    max_fallbacks: int = 3,
) -> List[str]:
    """
    Get fallback queries for a failed search.

    Args:
        query: Original query that failed
        company: Company name for context
        country: Country for context
        max_fallbacks: Maximum number of fallbacks

    Returns:
        List of alternative queries
    """
    manager = SearchFallbackManager(
        company=company,
        country=country,
        max_fallbacks=max_fallbacks,
    )
    return manager.get_fallbacks(query)


__all__ = [
    "SearchFallbackManager",
    "FallbackStrategy",
    "FallbackResult",
    "get_fallback_queries",
]
