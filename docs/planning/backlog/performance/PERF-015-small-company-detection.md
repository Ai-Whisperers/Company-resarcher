# PERF-015: Early Detection of Small/Defunct Companies

## Problem

The comprehensive research runs 234 queries for ALL companies equally, regardless of their online presence. Small/defunct companies like Vox Paraguay waste 30-60 minutes on queries that return nothing.

## Evidence from Logs

```
# Most Vox Paraguay sections returned 0 sources:
22:40:04 - brand_strategy/02-Messaging-Framework.md: 0 sources from 5 queries
22:40:05 - marketing_execution/02-Content-Plan.md: 0 sources from 4 queries
22:40:05 - target_audience/02-Customer-Journey.md: 0 sources from 6 queries
22:40:22 - data_room/03-Funding-History.md: 0 sources from 5 queries
22:40:35 - sales_intelligence/03-Decision-Makers.md: 0 sources from 5 queries
```

Compare to major companies:
- Tigo Paraguay: 259 sources
- Claro Paraguay: 161 sources
- Vox Paraguay: ~20 sources (mostly duplicates)

## Impact

- 30-60 minutes wasted on dead/small companies
- Hundreds of timeout errors
- Resource waste on impossible queries

## Proposed Solution

### 1. Pre-Research Probe

Before full research, run a quick probe to assess online presence:

```python
async def probe_company_presence(company: str, website: str) -> CompanyPresence:
    """Quick assessment of company's online presence."""
    probe_queries = [
        f'"{company}" company',
        f'"{company}" news',
        f'site:{extract_domain(website)}',
    ]

    results_count = 0
    for query in probe_queries:
        results = await quick_search(query, timeout=10, max_results=5)
        results_count += len(results)

    if results_count < 5:
        return CompanyPresence.MINIMAL
    elif results_count < 15:
        return CompanyPresence.LIMITED
    else:
        return CompanyPresence.SUBSTANTIAL
```

### 2. Adaptive Research Depth

Based on probe results, adjust research scope:

```python
RESEARCH_PROFILES = {
    CompanyPresence.SUBSTANTIAL: {
        "queries_per_section": 10,
        "sections": ["all"],
        "max_sources_per_section": 30,
    },
    CompanyPresence.LIMITED: {
        "queries_per_section": 5,
        "sections": ["strategic_context", "market_intelligence", "competitive_landscape"],
        "max_sources_per_section": 15,
    },
    CompanyPresence.MINIMAL: {
        "queries_per_section": 3,
        "sections": ["strategic_context", "competitive_landscape"],
        "max_sources_per_section": 10,
        "skip_detailed_sections": True,
    },
}
```

### 3. Dynamic Section Skipping

During research, skip sections if first queries return nothing:

```python
async def should_skip_section(self, section: str, first_results: List) -> bool:
    """Skip section if first 2 queries return no relevant results."""
    if len(first_results) == 0:
        logger.info(f"Skipping {section} - no results from initial queries")
        return True

    # Check if results are actually relevant
    relevant = [r for r in first_results if self.is_relevant_result(r)]
    if len(relevant) == 0:
        logger.info(f"Skipping {section} - no relevant results")
        return True

    return False
```

### 4. Company Status Detection

Detect if company is defunct/absorbed:

```python
DEFUNCT_INDICATORS = [
    "was acquired by",
    "merged with",
    "absorbed by",
    "ceased operations",
    "went bankrupt",
    "no longer operating",
]

async def detect_company_status(company: str) -> CompanyStatus:
    """Check if company is still operating."""
    results = await search(f'"{company}" status')

    for result in results:
        content = result.content.lower()
        for indicator in DEFUNCT_INDICATORS:
            if indicator in content:
                return CompanyStatus.DEFUNCT

    return CompanyStatus.ACTIVE
```

## Files to Modify

- `src/pipeline/comprehensive_research.py`
- New: `src/core/company_probe.py`
- New: `src/core/research_profiles.py`

## Acceptance Criteria

- [ ] Quick probe runs before full research (< 30s)
- [ ] Small companies get reduced research scope
- [ ] Defunct companies detected and noted
- [ ] Sections skipped if first queries return nothing
- [ ] Logging shows adaptive decisions

## Priority

**MEDIUM** - Significant time savings for edge cases.

## Estimate

4-5 hours implementation + testing
