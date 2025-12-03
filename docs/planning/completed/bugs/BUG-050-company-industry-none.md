# BUG-050: Company Industry is None - Causes Poor Query Generation

## Summary
The `company.industry` field is `None` throughout the research pipeline, leading to generic and ineffective search queries. This results in poor search results that don't target the company's actual business sector.

## Severity
**HIGH** - Significantly degrades search query quality and research relevance

## Symptoms
### Query Generation Without Industry
```
15:58:31 - pipeline - INFO - [query_generation_market] Generated 4 queries for market
```

Queries generated:
```
"industry market size and growth"          # "industry" is literal, not the actual industry
"Personal Paraguay target audience demographics"
"Personal Paraguay industry trends"         # Again, "industry" is literal
"Personal Paraguay market share industry"   # And again
```

### Expected Queries (with industry=telecommunications)
```
"telecommunications market size and growth Paraguay"
"Personal Paraguay telecommunications market share"
"Paraguay mobile network industry trends"
```

### Impact on Results
- Generic queries return irrelevant results
- Missing industry-specific competitor identification
- Market analysis lacks sector context
- Financial analysis misses industry benchmarks

## Root Cause Analysis

### 1. Industry Not Extracted from Website
The initial website scrape doesn't extract or infer the company's industry:
```python
# src/pipeline/stages/initial_scrape.py
# No industry detection logic
```

### 2. Industry Not Provided in Input
The CLI/API doesn't accept or require industry input:
```python
# main.py
parser.add_argument("--name", required=True)
parser.add_argument("--url", required=True)
# Missing: --industry argument
```

### 3. Query Templates Use Literal "industry"
```python
# When company.industry is None:
queries = [
    f"{company.industry} market size",  # Becomes "None market size"
    f"industry market size",             # Fallback uses literal "industry"
]
```

## Affected Files
- `main.py` - CLI argument parsing
- `src/api/routes.py` - API input handling
- `src/core/types.py` - CompanyInfo model
- `src/pipeline/stages/initial_scrape.py` - Website analysis
- `src/pipeline/stages/query_generation.py` - Query building

## Proposed Solutions

### Solution 1: Add Industry CLI/API Parameter (Quick Fix)
```python
# main.py
parser.add_argument(
    "--industry",
    type=str,
    help="Company industry (e.g., 'telecommunications', 'retail')"
)

# Usage:
# python main.py --name "Personal Paraguay" --url "https://personal.com.py" --industry "telecommunications"
```

### Solution 2: AI-Based Industry Detection (Recommended)
```python
# src/pipeline/stages/industry_detection.py
async def detect_industry(company_name: str, website_content: str) -> str:
    """Use AI to detect company industry from website content."""

    prompt = f"""Analyze this company's website content and identify their primary industry.

Company: {company_name}
Website Content (first 2000 chars):
{website_content[:2000]}

Return ONLY the industry name in 1-3 words. Examples:
- Telecommunications
- E-commerce
- Financial Services
- Healthcare
- Manufacturing
- Retail
- Software/Technology
- Hospitality

Industry:"""

    response = await ai_client.generate(prompt)
    return response.strip()
```

### Solution 3: Domain-Based Industry Inference
```python
# src/utils/industry_inference.py
DOMAIN_INDUSTRY_MAP = {
    # Telecom indicators
    "personal.com": "Telecommunications",
    "movistar": "Telecommunications",
    "claro": "Telecommunications",
    "tigo": "Telecommunications",

    # Banking
    "banco": "Banking",
    "bank": "Banking",

    # Keywords in domain
    "tech": "Technology",
    "soft": "Software",
    "pharma": "Pharmaceuticals",
    "health": "Healthcare",
}

def infer_industry_from_domain(url: str) -> Optional[str]:
    """Infer industry from domain name patterns."""
    domain = tldextract.extract(url).domain.lower()
    for pattern, industry in DOMAIN_INDUSTRY_MAP.items():
        if pattern in domain:
            return industry
    return None
```

### Solution 4: Query Template Improvement
```python
# src/pipeline/stages/query_generation.py
def generate_queries(company: CompanyInfo, research_type: str) -> List[str]:
    # Skip industry-dependent queries if industry is unknown
    if company.industry:
        industry_queries = [
            f"{company.industry} market size",
            f"{company.industry} trends 2024",
        ]
    else:
        # Fallback: Use company-specific queries only
        industry_queries = [
            f"{company.name} business sector",
            f"what industry is {company.name}",
        ]

    return industry_queries + company_specific_queries
```

### Solution 5: Website Metadata Extraction
```python
# src/tools/browser_tool.py
async def extract_industry_metadata(page) -> Optional[str]:
    """Extract industry from meta tags or structured data."""

    # Check meta tags
    industry_meta = await page.evaluate("""
        () => {
            const meta = document.querySelector('meta[property="og:type"]');
            return meta ? meta.content : null;
        }
    """)

    # Check Schema.org data
    schema_data = await page.evaluate("""
        () => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (const script of scripts) {
                const data = JSON.parse(script.textContent);
                if (data['@type'] === 'Organization' && data.industry) {
                    return data.industry;
                }
            }
            return null;
        }
    """)

    return industry_meta or schema_data
```

## Implementation Priority

1. **Add --industry CLI parameter** - Immediate fix, allows manual override
2. **AI-based detection** - Most accurate, uses website content
3. **Fix query templates** - Handle None gracefully
4. **Domain inference** - Quick heuristic for common industries

## Test Cases
```python
async def test_industry_detection():
    content = "Personal is the leading mobile network operator in Paraguay..."
    industry = await detect_industry("Personal Paraguay", content)
    assert "telecom" in industry.lower() or "mobile" in industry.lower()

def test_query_with_industry():
    company = CompanyInfo(
        name="Personal Paraguay",
        url="https://personal.com.py",
        industry="Telecommunications"
    )
    queries = generate_queries(company, "market")
    assert "Telecommunications" in " ".join(queries)

def test_query_without_industry_no_literal():
    company = CompanyInfo(
        name="Test Company",
        url="https://example.com",
        industry=None
    )
    queries = generate_queries(company, "market")
    # Should NOT contain literal "industry" or "None"
    for query in queries:
        assert "industry" not in query.lower() or company.name in query
        assert "none" not in query.lower()
```

## Acceptance Criteria
- [ ] Industry can be provided via CLI --industry argument
- [ ] Industry is automatically detected from website content
- [ ] Query templates use actual industry name (not literal "industry")
- [ ] Graceful handling when industry cannot be determined
- [ ] CompanyInfo.industry is populated before query generation
- [ ] No queries contain "None" as a literal string

## Related Issues
- BUG-049: Wrong country results (related context issue)
- Query quality affects all research types

## Labels
`high`, `bug`, `pipeline`, `query-generation`, `data-quality`
