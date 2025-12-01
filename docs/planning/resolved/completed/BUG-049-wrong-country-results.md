# BUG-049: Wrong Country Results (Argentina vs Paraguay)

## Summary
Search queries for "Personal Paraguay" are returning results for Personal Argentina (personal.com.ar) instead of Personal Paraguay (personal.com.py). This is a fundamental search quality issue that undermines the entire research output.

## Severity
**CRITICAL** - Returns completely wrong company data, making research output unreliable

## Symptoms
### Evidence from competitor.md
```markdown
- Personal Paraguay competitor telecommunications Argentina → returns personal.com.ar (WRONG)
- Sources contain: "Personal Argentina" references
```

### Log Evidence
```
19:33:08 - browser_tool - INFO - Navigating to: https://www.personal.com.ar/...
```
When researching Personal Paraguay (personal.com.py), but visiting personal.com.ar (Argentina).

### Output File Evidence
Reports contain mixed data from both Paraguay and Argentina operations, leading to:
- Incorrect market size figures (Argentina is much larger)
- Wrong competitor lists (different market)
- Incorrect regulatory context
- Misleading financial data

## Root Cause Analysis

### 1. Ambiguous Company Names
"Personal" is a common brand name used across multiple Latin American countries:
- Personal Paraguay: personal.com.py
- Personal Argentina: personal.com.ar
- Personal Colombia: (if exists)

### 2. Query Generation Lacks Geographic Specificity
Current query generation templates:
```python
queries = [
    f"{company_name} competitors in {industry}",  # Missing country
    f"{company_name} market analysis",             # Missing country
]
```

### 3. No URL-Based Country Extraction
The system doesn't extract country from the target URL:
- `personal.com.py` → Paraguay (TLD .py)
- `personal.com.ar` → Argentina (TLD .ar)

### 4. Search Results Not Filtered by Domain
Results from wrong country domains are not filtered out.

## Affected Files
- `src/pipeline/stages/query_generation.py` - Query templates lack country context
- `src/tools/search/` - All providers lack country filtering
- `src/pipeline/context.py` - Company context doesn't include country
- `src/core/types.py` - CompanyInfo missing country field

## Proposed Solutions

### Solution 1: Extract Country from URL TLD (Recommended)
```python
# src/utils/url_utils.py
import tldextract

COUNTRY_TLD_MAP = {
    "py": "Paraguay",
    "ar": "Argentina",
    "br": "Brazil",
    "mx": "Mexico",
    "co": "Colombia",
    "cl": "Chile",
    "pe": "Peru",
    "uy": "Uruguay",
    "ec": "Ecuador",
    "ve": "Venezuela",
    # Add more as needed
}

def extract_country_from_url(url: str) -> Optional[str]:
    """Extract country from URL's TLD."""
    ext = tldextract.extract(url)
    tld = ext.suffix.split(".")[-1]  # Handle .com.py → py
    return COUNTRY_TLD_MAP.get(tld.lower())

# Example usage
url = "https://www.personal.com.py"
country = extract_country_from_url(url)  # Returns "Paraguay"
```

### Solution 2: Add Country to CompanyInfo
```python
# src/core/types.py
class CompanyInfo(BaseModel):
    name: str
    url: str
    industry: Optional[str] = None
    country: Optional[str] = None  # NEW - extracted from URL or provided

    @classmethod
    def from_url(cls, name: str, url: str):
        country = extract_country_from_url(url)
        return cls(name=name, url=url, country=country)
```

### Solution 3: Update Query Templates with Country
```python
# src/pipeline/stages/query_generation.py
def generate_queries(company: CompanyInfo, research_type: str) -> List[str]:
    country_context = f" {company.country}" if company.country else ""

    templates = {
        "competitor": [
            f"{company.name}{country_context} competitors",
            f"{company.name} top competitors in{country_context}",
            f"telecommunications companies in{country_context}",
        ],
        "market": [
            f"{company.name}{country_context} market share",
            f"telecommunications market{country_context}",
        ]
    }
```

### Solution 4: Filter Results by URL TLD
```python
# src/tools/search/base.py
def filter_by_country(
    results: List[SearchResult],
    target_country_tld: str
) -> List[SearchResult]:
    """Prioritize results from target country domain."""
    target_results = []
    other_results = []

    for result in results:
        ext = tldextract.extract(result.url)
        tld = ext.suffix.split(".")[-1]
        if tld == target_country_tld:
            target_results.append(result)
        else:
            other_results.append(result)

    # Return target country results first, then others
    return target_results + other_results
```

### Solution 5: Add site: Operator to Queries
```python
def add_site_restriction(query: str, target_url: str) -> str:
    """Add site restriction for company-specific queries."""
    domain = tldextract.extract(target_url).registered_domain
    return f"{query} site:{domain}"

# Example: "Personal Paraguay competitors" → "Personal Paraguay competitors site:personal.com.py"
```

## Implementation Priority

1. **Extract country from URL** - Immediate value, low effort
2. **Add country to queries** - Direct fix for search quality
3. **Filter results by TLD** - Removes wrong-country noise
4. **Add site: operator** - For company-specific queries

## Test Cases
```python
async def test_country_extraction():
    assert extract_country_from_url("https://personal.com.py") == "Paraguay"
    assert extract_country_from_url("https://personal.com.ar") == "Argentina"
    assert extract_country_from_url("https://example.com") is None  # .com is global

async def test_queries_include_country():
    company = CompanyInfo.from_url("Personal", "https://personal.com.py")
    queries = generate_queries(company, "competitor")
    assert any("Paraguay" in q for q in queries)

async def test_no_wrong_country_results():
    company = CompanyInfo.from_url("Personal", "https://personal.com.py")
    results = await search_manager.search("Personal competitors")
    # Verify no .ar domains in top results when researching .py company
    for result in results[:5]:
        assert ".com.ar" not in result.url
```

## Acceptance Criteria
- [ ] Country extracted automatically from company URL TLD
- [ ] Generated queries include country context
- [ ] Search results prioritize correct country domain
- [ ] No Argentina results when researching Paraguay (and vice versa)
- [ ] Works for all Latin American countries with specific TLDs
- [ ] Graceful fallback for .com domains (no country filtering)

## Impact Analysis
**High Impact Fix** - This affects the fundamental accuracy of all research outputs. Without country-aware searching, the entire competitive analysis and market research is unreliable for multi-country brands.

## Related Issues
- BUG-050: Company industry is None (related context issue)
- BUG-048: DuckDuckGo Chinese results (search quality)

## Labels
`critical`, `bug`, `search`, `localization`, `data-quality`
