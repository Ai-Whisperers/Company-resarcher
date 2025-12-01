# FE-009: Company Context Enrichment Before Research

## Priority: HIGH
## Category: Feature Enhancement
## Status: Backlog
## Created: 2025-11-28

## Summary

Add a pre-research phase that fetches the company website and extracts key context (industry, products, parent company, geography) to improve search query relevance.

## Problem Statement

Currently, research begins immediately with generic queries like `"{company_name} market share"`. This leads to:
- Wrong industry context (telecom vs personal care)
- Missing parent company relationships
- Geographic ambiguity
- Irrelevant search results (dictionaries, wrong industries)

## Proposed Solution

### Phase 0: Company Enrichment

Before running research phases, extract context from the company website:

```python
# src/services/company_enricher.py

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class CompanyContext:
    """Enriched company information extracted from website."""
    name: str
    industry: str  # "telecommunications", "retail", "fintech"
    industry_keywords: List[str]  # ["mobile", "operator", "cellular"]
    products_services: List[str]  # ["mobile plans", "fiber internet", "TV"]
    parent_company: Optional[str]  # "Telecom Argentina"
    geography: str  # "Paraguay"
    company_type: str  # "subsidiary", "public", "startup"
    competitors_mentioned: List[str]  # ["Tigo", "Claro"]
    year_founded: Optional[int]
    employee_count_estimate: Optional[str]


class CompanyEnricher:
    """Extract company context from website before research."""

    def __init__(self, browser: BrowserTool, ai_client: AIClient):
        self.browser = browser
        self.ai = ai_client

    async def enrich(self, company: CompanyProfile) -> CompanyContext:
        """
        Fetch company website and extract context.

        Steps:
        1. Fetch homepage
        2. Fetch about/company page if exists
        3. Extract context via AI
        4. Validate and return
        """
        # Fetch main page
        homepage = await self.browser.fetch(company.url)

        # Try to find about page
        about_content = await self._fetch_about_page(company.url)

        # Extract context via AI
        context = await self._extract_context(
            company_name=company.name,
            homepage=homepage,
            about_page=about_content
        )

        return context

    async def _extract_context(self, company_name: str, homepage: str, about_page: str) -> CompanyContext:
        prompt = f"""
        Analyze this company website content and extract key information.

        Company: {company_name}

        Homepage Content:
        {homepage[:5000]}

        About Page Content:
        {about_page[:3000] if about_page else "Not available"}

        Extract and return as JSON:
        {{
            "industry": "the primary industry (e.g., telecommunications, retail, fintech)",
            "industry_keywords": ["3-5 keywords for search queries"],
            "products_services": ["main products or services offered"],
            "parent_company": "parent company name if mentioned, null otherwise",
            "geography": "primary operating country/region",
            "company_type": "public|private|subsidiary|startup",
            "competitors_mentioned": ["any competitors mentioned on site"],
            "year_founded": null or year,
            "employee_count_estimate": "small|medium|large|enterprise"
        }}
        """

        response = await self.ai.generate(prompt)
        return CompanyContext(**parse_json(response))
```

### Integration with Pipeline

```python
# src/pipeline/orchestrator.py

async def conduct_research(self, company_name: str, url: str):
    # Step 0: Enrich company context
    company = CompanyProfile(name=company_name, url=url)

    enricher = CompanyEnricher(self.browser, self.ai)
    context = await enricher.enrich(company)

    logger.info(f"Company context: industry={context.industry}, "
                f"parent={context.parent_company}, geo={context.geography}")

    # Step 1-N: Run research phases with context
    for phase in self.phases:
        await phase.run(company, context)  # Pass context to phases
```

### Query Generation with Context

```python
# src/pipeline/stages/query_generation.py

def generate_queries(company: CompanyProfile, context: CompanyContext, phase: str) -> List[str]:
    base_queries = PHASE_QUERIES[phase]

    # Substitute with context
    queries = []
    for template in base_queries:
        query = template.format(
            company=company.name,
            industry=context.industry,
            keywords=" ".join(context.industry_keywords[:2]),
            geography=context.geography,
            parent=context.parent_company or "",
        )
        queries.append(query)

    return queries

# Example output for Personal Paraguay:
# "Personal Paraguay telecommunications mobile operator market share Paraguay"
# "Personal Paraguay vs Tigo Claro competitors Paraguay mobile"
# "Telecom Argentina subsidiary Personal Paraguay financial"
```

## Implementation Steps

1. Create `CompanyEnricher` service
2. Add enrichment phase to orchestrator
3. Update query templates to use context
4. Add context to pipeline state
5. Add caching for repeated research

## Acceptance Criteria

- [ ] Company website is fetched before research starts
- [ ] Industry is correctly identified
- [ ] Search queries include industry context
- [ ] Parent company relationship captured
- [ ] Geographic context included in queries
- [ ] Results are relevant to actual company

## Files to Create/Modify

- New: `src/services/company_enricher.py`
- Modify: `src/pipeline/orchestrator.py`
- Modify: `src/pipeline/stages/query_generation.py`
- Modify: `src/core/types.py` - Add CompanyContext model

## Expected Improvement

| Metric | Before | After |
|--------|--------|-------|
| Relevant search results | 10-20% | 80-90% |
| Industry context accuracy | 0% | 95% |
| Competitor identification | 0% | 70% |
| Time to first result | 2s | 5s (adds enrichment) |

## Related Issues

- BUG-004: Wrong company context in search queries
- FE-008: Company Type Detection & Adaptive Research
