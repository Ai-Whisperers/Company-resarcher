"""
Query Optimizer Service - Smart fallback queries and query improvement.

Handles:
- Generating fallback queries when searches return no results
- Simplifying complex queries
- Adding temporal context (year qualifiers)
- Removing overly specific terms
"""

import re
from typing import List, Optional
from datetime import datetime


def simplify_query(query: str) -> str:
    """
    Simplify a query by removing quotes and reducing complexity.

    Args:
        query: Original search query

    Returns:
        Simplified query string
    """
    # Remove quotes
    simplified = query.replace('"', '').replace("'", '')

    # Remove parentheses and their contents if complex
    simplified = re.sub(r'\([^)]*\)', '', simplified)

    # Normalize whitespace
    simplified = ' '.join(simplified.split())

    return simplified.strip()


def remove_company_quotes(query: str) -> str:
    """
    Remove quotes around company name but keep the name.

    Args:
        query: Query with quoted company name

    Returns:
        Query without quotes
    """
    # Pattern: "Company Name" -> Company Name
    return re.sub(r'"([^"]+)"', r'\1', query)


def add_year_context(query: str, year: Optional[int] = None) -> str:
    """
    Add current year to query for more recent results.

    Args:
        query: Original query
        year: Year to add (defaults to current year)

    Returns:
        Query with year context
    """
    if year is None:
        year = datetime.now().year

    # Don't add if year already present
    if str(year) in query or str(year - 1) in query:
        return query

    return f"{query} {year}"


def broaden_industry_terms(query: str) -> str:
    """
    Replace specific industry terms with broader alternatives.

    Args:
        query: Original query

    Returns:
        Query with broader terms
    """
    # Mapping of specific terms to broader alternatives
    broadening_map = {
        r'\btelecommunications\b': 'telecom',
        r'\btelecommunication\b': 'telecom',
        r'\bmobile network operator\b': 'mobile operator',
        r'\bMNO\b': 'mobile',
        r'\bfinancial services\b': 'finance',
        r'\bfinancial performance\b': 'financials',
        r'\bannual report\b': 'report',
        r'\bmarket share\b': 'market',
        r'\bcompetitive landscape\b': 'competitors',
        r'\bcompetitive analysis\b': 'competition',
    }

    result = query
    for pattern, replacement in broadening_map.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def extract_key_terms(query: str) -> List[str]:
    """
    Extract the most important terms from a query.

    Args:
        query: Original query

    Returns:
        List of key terms
    """
    # Remove quotes and normalize
    clean = query.replace('"', '').replace("'", '')

    # Split into words
    words = clean.split()

    # Filter out common stop words and short terms
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'vs', 'versus', 'about', 'overview', 'analysis', 'report',
    }

    key_terms = [
        w for w in words
        if len(w) > 2 and w.lower() not in stop_words
    ]

    return key_terms


def generate_fallback_queries(
    original_query: str,
    company_name: str,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    max_fallbacks: int = 3,
) -> List[str]:
    """
    Generate fallback queries when the original returns no results.

    Strategies:
    1. Remove quotes from company name
    2. Simplify the query
    3. Add current year for recency
    4. Broaden industry terms
    5. Use key terms only

    Args:
        original_query: The query that returned no results
        company_name: Company being researched
        country: Target country (optional)
        industry: Target industry (optional)
        max_fallbacks: Maximum number of fallback queries to generate

    Returns:
        List of fallback queries to try
    """
    fallbacks = []

    # Strategy 1: Remove quotes
    no_quotes = remove_company_quotes(original_query)
    if no_quotes != original_query and no_quotes not in fallbacks:
        fallbacks.append(no_quotes)

    # Strategy 2: Simplify query
    simplified = simplify_query(original_query)
    if simplified != original_query and simplified not in fallbacks:
        fallbacks.append(simplified)

    # Strategy 3: Add year context to simplified query
    with_year = add_year_context(simplified)
    if with_year != simplified and with_year not in fallbacks:
        fallbacks.append(with_year)

    # Strategy 4: Broaden industry terms
    broadened = broaden_industry_terms(simplified)
    if broadened != simplified and broadened not in fallbacks:
        fallbacks.append(broadened)

    # Strategy 5: Company name + key industry term only
    if industry:
        simple_industry = f"{company_name} {industry}"
        if simple_industry not in fallbacks:
            fallbacks.append(simple_industry)

    # Strategy 6: Company name + country only
    if country and country != "Global":
        simple_country = f"{company_name} {country}"
        if simple_country not in fallbacks:
            fallbacks.append(simple_country)

    # Strategy 7: Just company name with year
    company_year = f"{company_name} {datetime.now().year}"
    if company_year not in fallbacks:
        fallbacks.append(company_year)

    # Limit to max_fallbacks
    return fallbacks[:max_fallbacks]


def optimize_query_batch(
    queries: List[str],
    company_name: str,
    country: Optional[str] = None,
) -> List[str]:
    """
    Optimize a batch of queries by removing near-duplicates.

    Args:
        queries: List of queries to optimize
        company_name: Company being researched
        country: Target country

    Returns:
        Deduplicated and optimized query list
    """
    seen_normalized = set()
    optimized = []

    for query in queries:
        # Normalize for comparison
        normalized = query.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.replace('"', '').replace("'", '')

        # Skip if we've seen a very similar query
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            optimized.append(query)

    return optimized


def should_retry_query(
    query: str,
    result_count: int,
    min_results: int = 1,
) -> bool:
    """
    Determine if a query should be retried with fallbacks.

    Args:
        query: The executed query
        result_count: Number of results returned
        min_results: Minimum acceptable results

    Returns:
        True if query should be retried with fallbacks
    """
    return result_count < min_results
