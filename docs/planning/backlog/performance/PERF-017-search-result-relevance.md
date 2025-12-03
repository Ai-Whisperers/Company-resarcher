# PERF-017: Search Result Relevance Scoring

## Problem

Search results include many irrelevant pages that waste browser fetch time. The current BUG-049 filter catches some foreign sources but doesn't prevent the browser from attempting to fetch them first.

## Evidence from Logs

```
# These get fetched BEFORE being filtered:
22:40:05 - marketing_execution/02-Content-Plan.md: Filtered 20 irrelevant foreign sources (BUG-049)
22:40:23 - investment_analysis/03-Market-Opportunity.md: Filtered 15 irrelevant foreign sources (BUG-049)
22:40:35 - creative_inspiration/03-Viral-Campaigns.md: Filtered 20 irrelevant foreign sources (BUG-049)
```

55 sources were fetched and THEN filtered = 55 × ~30s = ~27 minutes wasted.

## Impact

- Browser fetches irrelevant pages before filtering
- Each irrelevant fetch wastes 15-60 seconds
- Filter happens too late in the pipeline

## Proposed Solution

### 1. Pre-Fetch Relevance Filter

Move relevance filtering BEFORE browser fetch:

```python
class SearchResultFilter:
    def __init__(self, company: str, country: str, industry: str):
        self.company = company
        self.country = country
        self.industry = industry

    def pre_filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Filter search results BEFORE fetching."""
        filtered = []
        for result in results:
            score = self.calculate_relevance(result)
            if score >= 0.3:  # Minimum relevance threshold
                filtered.append(result)
            else:
                logger.debug(f"Pre-filtered irrelevant: {result.url} (score: {score})")
        return filtered

    def calculate_relevance(self, result: SearchResult) -> float:
        score = 0.0

        # Title/description mentions company
        if self.company.lower() in result.title.lower():
            score += 0.4
        if self.company.lower() in result.description.lower():
            score += 0.2

        # Domain relevance
        domain = extract_domain(result.url)
        if domain.endswith(f'.{self.country[:2].lower()}'):  # Country TLD
            score += 0.2
        if domain in BLOCKED_DOMAINS:
            score -= 0.5

        # Language/region indicators
        if any(lang in result.url for lang in ['/es/', '/py/', '/spanish/']):
            score += 0.1
        if any(lang in result.url for lang in ['/zh/', '/cn/', '/de/', '/ru/']):
            score -= 0.3

        return max(0, min(1, score))
```

### 2. Early URL Validation

Check URL relevance before adding to fetch queue:

```python
def should_fetch_url(url: str, context: ResearchContext) -> bool:
    """Quick check if URL is worth fetching."""
    domain = extract_domain(url)

    # Blocked domains
    if domain in BLOCKED_DOMAINS:
        return False

    # Wrong language/region
    if any(pattern in url for pattern in ['/zh-cn/', '/zh-tw/', '/de-de/', '/ru-ru/']):
        return False

    # Known problematic patterns
    if any(pattern in url for pattern in [
        'zhidao.baidu.com',
        'photovoltaikforum.com',
        '/question/',  # Often Q&A sites
    ]):
        return False

    return True
```

### 3. Search Query Context

Include country/language in search queries to improve results:

```python
def build_contextual_query(base_query: str, context: ResearchContext) -> str:
    """Add context to search query for better results."""
    parts = [base_query]

    # Add country context
    if context.country:
        parts.append(context.country)

    # Add language hint for Spanish-speaking countries
    if context.country in ["Paraguay", "Argentina", "Chile", "Mexico"]:
        # DuckDuckGo region parameter
        parts.append("site:.py OR site:.com")  # Prefer local domains

    return " ".join(parts)
```

## Files to Modify

- `src/tools/search_tool.py`
- `src/pipeline/comprehensive_research.py`
- `src/core/url_validator.py`
- New: `src/core/relevance_filter.py`

## Acceptance Criteria

- [ ] Irrelevant URLs filtered BEFORE browser fetch
- [ ] Relevance score calculated for each search result
- [ ] Search queries include country/language context
- [ ] Logging shows pre-filter decisions
- [ ] Significant reduction in browser fetch attempts

## Priority

**HIGH** - Prevents wasted fetches at the source.

## Estimate

3-4 hours implementation + testing
