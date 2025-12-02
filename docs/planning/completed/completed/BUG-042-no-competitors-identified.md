# BUG-042: No Competitors Identified in Competitor Analysis

## Priority: HIGH
## Category: Bug/Analysis Quality
## Status: Backlog
## Discovered: 2025-11-28

## Summary

The competitor analysis phase fails to identify any competitors for the target company, returning "N/A" for all competitor fields despite the fact that competitor information is publicly available.

## Problem Statement

For "Personal Paraguay" (a telecommunications company in Paraguay), the competitor report shows:

```markdown
## Direct Competitors
- N/A

## Indirect Competitors / Alternatives
- N/A

## Emerging Threats
- N/A
```

**Expected Results:**
- Direct Competitors: Tigo Paraguay, Claro Paraguay, Vox
- Indirect Competitors: WhatsApp (for messaging), Starlink (for internet)
- Emerging Threats: MVNOs, satellite internet providers

## Evidence

### From Competitor Report:
```markdown
# Competitor List

**Company:**
**Industry:**
**Date:** 2025-11-28 19:57:00.617042

## Direct Competitors
- N/A

## Indirect Competitors / Alternatives
- N/A

## Emerging Threats
- N/A
```

### Sources Retrieved (Irrelevant):
```markdown
- [Personal Paraguay | Internet Fibra + Flow | Planes | Celulares](https://personal.com.py/)
- [Why Invest in Paraguay | REDIEX](https://www.rediex.gov.py/en/por-que-invertir-en-paraguay/)
- [Why Paraguay is Latin America's Best Kept Investment Secret](https://www.civis.com.py/...)
- [Paraguay's Geopolitical Advantage: A Pro-Business Haven](https://expatmoney.com/...)
- [VOC's Rotor Market Growth Analysis](https://www.linkedin.com/...) - COMPLETELY UNRELATED
- [DRIVING FORCES... discount retailing industry](https://www.academia.edu/...) - WRONG INDUSTRY
```

## Root Cause Analysis

### 1. Query Design Flaw

Current competitor queries are too generic:
```python
queries = [
    f"{company_name} top competitors",
    f"{company_name} vs competitors comparison",
    f"{company_name} competitive advantage",
    f"industry key players",  # No company context at all!
]
```

The query `"industry key players"` has NO reference to Personal Paraguay or telecommunications.

### 2. Missing Industry Context

Queries don't include:
- Industry: "telecommunications"
- Geography: "Paraguay"
- Specific competitor names to look for

### 3. No Competitor Discovery Strategy

The system doesn't:
- Look at company's "About" page for competitor mentions
- Search industry reports
- Use specialized competitor databases (Crunchbase, CBInsights)

### 4. AI Prompt Doesn't Guide Discovery

The competitor analysis prompt may not instruct the AI to:
- Infer competitors from industry context
- Look for companies mentioned alongside the target
- Identify market share data

## Known Competitors (Ground Truth)

For Personal Paraguay, competitors are:

| Competitor | Type | Market Share |
|------------|------|--------------|
| Tigo Paraguay | Direct | ~50% |
| Claro Paraguay | Direct | ~25% |
| Personal Paraguay | Subject | ~20% |
| Vox (Copaco) | Direct | ~5% |

This information is readily available online but not being found.

## Proposed Solutions

### Solution 1: Industry-Aware Competitor Queries

```python
def generate_competitor_queries(company: CompanyProfile, context: CompanyContext) -> List[str]:
    queries = [
        # Direct competitor search
        f'"{company.name}" competitors',
        f'"{company.name}" vs',
        f'{company.name} alternative',

        # Industry-specific
        f'{context.industry} companies {context.geography}',
        f'{context.industry} market share {context.geography}',
        f'{context.geography} {context.industry} providers',

        # Competitor databases
        f'site:crunchbase.com {company.name} competitors',
        f'site:cbinsights.com {company.name} alternatives',

        # News about competition
        f'{company.name} competition news',
    ]
    return queries

# For Personal Paraguay:
# - "Personal Paraguay" competitors
# - telecommunications companies Paraguay
# - Paraguay mobile providers
# - site:crunchbase.com Personal Paraguay competitors
```

### Solution 2: Two-Phase Competitor Discovery

```python
async def discover_competitors(company: CompanyProfile, ctx: RequestContext):
    # Phase 1: Direct search for competitors
    direct_queries = [
        f'"{company.name}" competitors',
        f'{company.name} vs',
    ]
    phase1_sources = await search(direct_queries)

    # Phase 2: Industry landscape search
    industry = await infer_industry(company)
    landscape_queries = [
        f'{industry} market share {company.country}',
        f'{industry} companies {company.country}',
    ]
    phase2_sources = await search(landscape_queries)

    # Phase 3: Extract competitor names from sources
    competitor_names = await extract_competitor_names(
        phase1_sources + phase2_sources,
        company.name
    )

    # Phase 4: Research each competitor
    for comp_name in competitor_names[:5]:
        comp_data = await research_competitor(comp_name)

    return competitor_analysis
```

### Solution 3: Pre-defined Industry Competitor Templates

```python
INDUSTRY_COMPETITORS = {
    "telecommunications": {
        "search_terms": ["mobile operator", "telecom", "carrier", "ISP"],
        "data_sources": ["GSMA", "TeleGeography", "Statista"],
        "common_players": ["Vodafone", "Telefonica", "America Movil", "Tigo"],
    },
    "banking": {
        "search_terms": ["bank", "financial institution", "fintech"],
        "data_sources": ["Bloomberg", "S&P Global"],
        "common_players": ["JPMorgan", "HSBC", "Citibank"],
    },
}

def get_industry_search_hints(industry: str) -> dict:
    return INDUSTRY_COMPETITORS.get(industry.lower(), {})
```

### Solution 4: Competitor Extraction from Company Website

```python
async def extract_competitors_from_website(url: str) -> List[str]:
    """Extract competitor names mentioned on company website."""
    pages_to_check = [
        url,
        f"{url}/about",
        f"{url}/about-us",
        f"{url}/company",
    ]

    competitor_patterns = [
        r"competitors?\s+(?:include|are|such as)\s+([^.]+)",
        r"compared to\s+([^,]+)",
        r"unlike\s+([^,]+)",
        r"vs\.?\s+([^,]+)",
    ]

    # Also look for company names that appear near comparison words
    # ...
```

## Files to Modify

1. `src/pipeline/stages/research.py` - Improve competitor query generation
2. `src/prompts/competitor_analysis.txt` - Better extraction instructions
3. `src/agents/specialists.py` - CompetitorAgent improvements
4. New: `src/services/competitor_discovery.py` - Multi-phase discovery

## Acceptance Criteria

- [ ] At least 3 competitors identified for known companies
- [ ] Competitors are relevant to the same industry
- [ ] Market share data included when available
- [ ] Competitor strengths/weaknesses analyzed
- [ ] Sources are from business/industry sites, not dictionaries

## Testing Plan

1. **Personal Paraguay** - Should find: Tigo, Claro, Vox
2. **Coca-Cola** - Should find: PepsiCo, Dr Pepper, Nestlé
3. **Tesla** - Should find: Ford, GM, Rivian, BYD
4. **Unknown startup** - Should gracefully indicate limited data

## Competitor Data Sources to Integrate

| Source | Type | Access |
|--------|------|--------|
| Crunchbase | Database | API (paid) |
| CBInsights | Database | API (paid) |
| LinkedIn | Social | Scraping |
| Wikipedia | Encyclopedia | Free |
| Industry Reports | Research | Various |
| News Sites | News | Free |

## Related Issues

- BUG-035: Wrong company context
- BUG-039: Dictionary sites in results
- FE-009: Company context enrichment
- FE-010: Source quality filtering

## Notes

Competitor identification is one of the most valuable parts of company research. Without this working, the tool loses significant value for sales teams who need to understand competitive landscape.
