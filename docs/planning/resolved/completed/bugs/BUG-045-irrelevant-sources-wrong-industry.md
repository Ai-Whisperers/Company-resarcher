# BUG-045: Irrelevant Sources from Wrong Industries

## Priority: HIGH
## Category: Bug/Search Quality
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Search results include sources completely unrelated to the target company or its industry. Reports cite pages about "VOC's Rotor Market", "Discount Retailing", "Artificial Intelligence Market", and "Logistics Market" when researching a telecommunications company.

## Problem Statement

For "Personal Paraguay" (a telecommunications company), reports include:

### Completely Unrelated Sources:
| Source | Actual Topic | Expected Topic |
|--------|--------------|----------------|
| VOC's Rotor Market Growth Analysis | Industrial rotors | Telecommunications |
| Discount Retailing Industry DRIVING FORCES | Retail | Telecommunications |
| Artificial Intelligence - Worldwide | AI Market | Paraguay telecom |
| Logistics Market Size | Logistics | Mobile services |
| Diagnostic Testing Market | Healthcare | Telecommunications |

### From Competitor Report:
```markdown
- [VOC's Rotor Market Growth Analysis, Market Dynamics, Key Players](https://www.linkedin.com/pulse/vocs-rotor-market-growth-analysis-dynamics-key-players-zlxwf)
- [DRIVING FORCES... discount retailing industry](https://www.academia.edu/3837427/...)
```

### From Market Report:
```markdown
- [Artificial Intelligence - Worldwide | Market Forecast](https://www.statista.com/outlook/tmo/artificial-intelligence/worldwide)
- [Logistics Market Size to Hit Around USD 23.14 Tn By 2034](https://www.precedenceresearch.com/logistics-market)
```

## Root Cause Analysis

### 1. Generic Query Terms Without Context

Queries like `"industry key players"` return results about ANY industry:
```python
# Current query
"industry key players"

# Returns: Rotor industry, Retail industry, AI industry...
# Should be: "telecommunications industry key players Paraguay"
```

### 2. No Industry Filtering

Search doesn't filter by industry keywords:
- No telecom-related terms required
- No Paraguay/South America context
- Generic business terms match any industry

### 3. Word "Personal" Causes Confusion

"Personal" matches:
- Personal care products
- Personal finance
- Personal branding
- Personal assistants

Instead of "Personal Paraguay" the telecom company.

### 4. Missing Semantic Relevance Check

No validation that search results are semantically related to:
- The company's industry
- The company's geography
- The company's products/services

## Evidence: Source-to-Query Mapping

| Query | Irrelevant Result | Why Matched |
|-------|-------------------|-------------|
| "industry key players" | VOC's Rotor Market | Contains "industry" and "key players" |
| "industry market size and growth" | Logistics Market | Contains "market size and growth" |
| "Personal Paraguay target audience" | Diagnostic Testing Market | Contains "market" |
| "Personal Paraguay market share" | AI Market | Contains "market" |

## Proposed Solutions

### Solution 1: Industry-Specific Queries

```python
# src/pipeline/stages/research.py

def generate_queries(company: CompanyProfile, context: CompanyContext, phase: str) -> List[str]:
    # Always include industry context
    industry = context.industry or await infer_industry(company)
    geo = context.geography or company.country

    templates = {
        "market": [
            f'"{company.name}" {industry} market share {geo}',
            f'{industry} market size {geo}',
            f'{company.name} {industry} position',
        ],
        "competitor": [
            f'{industry} companies {geo}',
            f'{company.name} competitors {industry}',
            f'{geo} {industry} market players',
        ],
    }

    return templates.get(phase, [])

# For Personal Paraguay:
# - "Personal Paraguay" telecommunications market share Paraguay
# - telecommunications companies Paraguay
# - Paraguay mobile operators market players
```

### Solution 2: Post-Search Relevance Filtering

```python
# src/services/relevance_filter.py

class RelevanceFilter:
    """Filter search results by relevance to company/industry."""

    def __init__(self, company: CompanyProfile, context: CompanyContext):
        self.company_name = company.name.lower()
        self.industry_keywords = [
            context.industry.lower(),
            *[kw.lower() for kw in context.industry_keywords],
        ]
        self.geography = context.geography.lower()

    def is_relevant(self, result: SearchResult) -> bool:
        """Check if result is relevant to the company."""
        text = f"{result.title} {result.snippet}".lower()

        # Must mention company OR industry
        mentions_company = self.company_name in text
        mentions_industry = any(kw in text for kw in self.industry_keywords)

        if not mentions_company and not mentions_industry:
            return False

        # Bonus: Check for geography match
        mentions_geo = self.geography in text

        return True

    def filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        return [r for r in results if self.is_relevant(r)]
```

### Solution 3: Industry Keyword Blocklist

```python
# src/tools/search/filters.py

# Keywords that indicate wrong industry results
IRRELEVANT_INDUSTRY_PATTERNS = [
    # Healthcare when not healthcare company
    r"diagnostic\s+testing",
    r"medical\s+device",
    r"pharmaceutical",

    # Manufacturing when not manufacturing company
    r"rotor\s+market",
    r"industrial\s+equipment",
    r"manufacturing\s+sector",

    # Retail when not retail company
    r"discount\s+retail",
    r"grocery\s+market",
    r"e-commerce\s+platform",

    # Other unrelated
    r"cryptocurrency",
    r"nft\s+market",
    r"real\s+estate\s+investment",
]

def is_irrelevant_industry(text: str, target_industry: str) -> bool:
    """Check if text indicates a different industry."""
    text_lower = text.lower()

    for pattern in IRRELEVANT_INDUSTRY_PATTERNS:
        if re.search(pattern, text_lower):
            # Unless target industry matches
            if target_industry.lower() not in text_lower:
                return True

    return False
```

### Solution 4: Semantic Similarity Check

```python
# src/services/semantic_relevance.py

from sentence_transformers import SentenceTransformer

class SemanticRelevanceChecker:
    """Use embeddings to check semantic relevance."""

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def compute_relevance(self, company_description: str, result_text: str) -> float:
        """Compute semantic similarity between company and result."""
        embeddings = self.model.encode([company_description, result_text])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return similarity

    def filter_by_relevance(
        self,
        results: List[SearchResult],
        company_description: str,
        threshold: float = 0.3
    ) -> List[SearchResult]:
        """Keep only results above relevance threshold."""
        return [
            r for r in results
            if self.compute_relevance(company_description, r.snippet) >= threshold
        ]
```

### Solution 5: Source Domain Allowlist for Industries

```python
# src/tools/search/industry_sources.py

INDUSTRY_SOURCES = {
    "telecommunications": [
        "telegeography.com",
        "gsma.com",
        "lightreading.com",
        "fiercewireless.com",
        "rcrwireless.com",
        "telecomtv.com",
    ],
    "banking": [
        "bloomberg.com",
        "ft.com",
        "americanbanker.com",
        "bankingdive.com",
    ],
    "technology": [
        "techcrunch.com",
        "theverge.com",
        "wired.com",
        "arstechnica.com",
    ],
}

def get_industry_site_filter(industry: str) -> str:
    """Get site filter for industry-specific search."""
    sources = INDUSTRY_SOURCES.get(industry.lower(), [])
    if sources:
        return " OR ".join(f"site:{s}" for s in sources[:5])
    return ""

# Query becomes:
# "Personal Paraguay" (site:telegeography.com OR site:gsma.com OR ...)
```

## Files to Create/Modify

1. `src/services/relevance_filter.py` - New relevance filtering
2. `src/tools/search/industry_sources.py` - Industry source lists
3. `src/pipeline/stages/research.py` - Improve query generation
4. `src/tools/search/filters.py` - Add industry blocklist

## Acceptance Criteria

- [ ] All sources in report are related to target company/industry
- [ ] No sources from completely different industries
- [ ] Relevance score tracked for each source
- [ ] Irrelevant sources logged and counted
- [ ] At least 80% of sources pass relevance check

## Testing Plan

1. **Personal Paraguay (Telecom)** - No retail, healthcare, manufacturing sources
2. **JPMorgan (Banking)** - No telecom, healthcare sources
3. **Tesla (Automotive)** - No banking, retail sources
4. Verify filtering doesn't remove too many relevant results

## Metrics to Track

- % of sources filtered as irrelevant
- Average relevance score of included sources
- Industry match rate
- Geography match rate

## Related Issues

- BUG-035: Wrong company context
- BUG-039: Dictionary sites in results
- BUG-042: No competitors identified
- FE-009: Company context enrichment
- FE-010: Source quality filtering

## Notes

This issue is related to BUG-039 (dictionary sites) but focuses on industry mismatches rather than dictionary/translation sites. Both need to be addressed for quality research output.
