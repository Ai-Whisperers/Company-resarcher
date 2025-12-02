"""
Search Query Builder (FEAT-003).

Provides a fluent interface for building advanced search queries with operators.

Usage:
    from src.tools.search_query_builder import QueryBuilder

    # Build a query with operators
    query = (QueryBuilder("Apple financial report")
        .site("sec.gov")
        .filetype("pdf")
        .exclude("10-K amendment")
        .build())

    # Result: "Apple financial report site:sec.gov filetype:pdf -10-K amendment"

Supported Operators:
    - site: Restrict to specific domain
    - filetype: Filter by file type (pdf, doc, xls, etc.)
    - intitle: Word must be in page title
    - inurl: Word must be in URL
    - intext: Word must be in page text
    - exclude: Exclude words/phrases
    - exact: Exact phrase match (quotes)
    - OR: Boolean OR between terms
    - date_range: Restrict by date (provider-specific)
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchQuery:
    """Structured search query with operators."""

    base_query: str
    sites: List[str] = field(default_factory=list)
    filetypes: List[str] = field(default_factory=list)
    intitle: List[str] = field(default_factory=list)
    inurl: List[str] = field(default_factory=list)
    intext: List[str] = field(default_factory=list)
    exact_phrases: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    or_terms: List[str] = field(default_factory=list)
    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None  # YYYY-MM-DD

    def to_string(self) -> str:
        """Convert structured query to search string."""
        parts = [self.base_query]

        # Add exact phrases in quotes
        for phrase in self.exact_phrases:
            parts.append(f'"{phrase}"')

        # Add site restrictions
        for site in self.sites:
            parts.append(f"site:{site}")

        # Add filetype filters
        for ft in self.filetypes:
            parts.append(f"filetype:{ft}")

        # Add intitle
        for term in self.intitle:
            parts.append(f"intitle:{term}")

        # Add inurl
        for term in self.inurl:
            parts.append(f"inurl:{term}")

        # Add intext
        for term in self.intext:
            parts.append(f"intext:{term}")

        # Add exclusions
        for term in self.exclusions:
            if ' ' in term:
                parts.append(f'-"{term}"')
            else:
                parts.append(f"-{term}")

        # Add OR terms
        if self.or_terms:
            or_clause = " OR ".join(self.or_terms)
            parts.append(f"({or_clause})")

        return " ".join(parts)


class QueryBuilder:
    """
    Fluent query builder for advanced search queries.

    Example:
        query = (QueryBuilder("Apple Inc")
            .site("sec.gov")
            .filetype("pdf")
            .intitle("10-K")
            .exclude("amendment")
            .build())
    """

    def __init__(self, base_query: str):
        """Initialize with base search query."""
        self._query = SearchQuery(base_query=base_query)

    def site(self, domain: str) -> "QueryBuilder":
        """Restrict search to specific domain."""
        # Clean domain
        domain = domain.replace("https://", "").replace("http://", "")
        domain = domain.rstrip("/")
        self._query.sites.append(domain)
        return self

    def sites(self, *domains: str) -> "QueryBuilder":
        """Restrict search to multiple domains (OR)."""
        for domain in domains:
            self.site(domain)
        return self

    def filetype(self, extension: str) -> "QueryBuilder":
        """Filter by file type (pdf, doc, xls, ppt, etc.)."""
        ext = extension.lower().lstrip(".")
        self._query.filetypes.append(ext)
        return self

    def filetypes(self, *extensions: str) -> "QueryBuilder":
        """Filter by multiple file types."""
        for ext in extensions:
            self.filetype(ext)
        return self

    def intitle(self, term: str) -> "QueryBuilder":
        """Require term in page title."""
        self._query.intitle.append(term)
        return self

    def inurl(self, term: str) -> "QueryBuilder":
        """Require term in URL."""
        self._query.inurl.append(term)
        return self

    def intext(self, term: str) -> "QueryBuilder":
        """Require term in page text."""
        self._query.intext.append(term)
        return self

    def exact(self, phrase: str) -> "QueryBuilder":
        """Require exact phrase match."""
        self._query.exact_phrases.append(phrase)
        return self

    def exclude(self, term: str) -> "QueryBuilder":
        """Exclude results containing term."""
        self._query.exclusions.append(term)
        return self

    def or_with(self, *terms: str) -> "QueryBuilder":
        """Add OR alternatives."""
        self._query.or_terms.extend(terms)
        return self

    def date_range(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> "QueryBuilder":
        """
        Restrict by date range (YYYY-MM-DD format).

        Note: Date filtering depends on search provider support.
        """
        if from_date:
            self._query.date_from = from_date
        if to_date:
            self._query.date_to = to_date
        return self

    def build(self) -> str:
        """Build the final query string."""
        return self._query.to_string()

    def build_structured(self) -> SearchQuery:
        """Return the structured SearchQuery object."""
        return self._query


# Convenience functions for common query patterns
def company_sec_filings(company_name: str, filing_type: str = "10-K") -> str:
    """Build query for SEC filings."""
    return (QueryBuilder(f"{company_name} {filing_type}")
            .site("sec.gov")
            .filetype("pdf")
            .build())


def company_press_releases(company_name: str) -> str:
    """Build query for press releases."""
    return (QueryBuilder(f"{company_name} press release")
            .or_with("announcement", "news")
            .exclude("spam")
            .build())


def company_linkedin(company_name: str) -> str:
    """Build query for LinkedIn company page."""
    return (QueryBuilder(f"{company_name}")
            .site("linkedin.com")
            .inurl("company")
            .build())


def company_glassdoor(company_name: str) -> str:
    """Build query for Glassdoor reviews."""
    return (QueryBuilder(f"{company_name} reviews")
            .site("glassdoor.com")
            .build())


def company_crunchbase(company_name: str) -> str:
    """Build query for Crunchbase profile."""
    return (QueryBuilder(f"{company_name}")
            .site("crunchbase.com")
            .inurl("organization")
            .build())


def financial_report(company_name: str, report_type: str = "annual") -> str:
    """Build query for financial reports."""
    return (QueryBuilder(f"{company_name} {report_type} report financial")
            .filetypes("pdf", "xls", "xlsx")
            .exclude("template")
            .exclude("sample")
            .build())


def news_articles(topic: str, source: Optional[str] = None) -> str:
    """Build query for news articles."""
    builder = QueryBuilder(topic)
    if source:
        builder.site(source)
    return builder.exclude("sponsored").exclude("advertisement").build()


__all__ = [
    "QueryBuilder",
    "SearchQuery",
    # Convenience functions
    "company_sec_filings",
    "company_press_releases",
    "company_linkedin",
    "company_glassdoor",
    "company_crunchbase",
    "financial_report",
    "news_articles",
]
