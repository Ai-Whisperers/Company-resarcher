# BUG-004: Wrong Company Context in Search Queries

## Priority: CRITICAL
## Category: Bug/Search Quality
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Search queries are too generic, causing the system to research the wrong topics. "Personal Paraguay" is interpreted as the English word "personal" or "personal care" industry instead of the telecommunications company.

## Problem Statement

The query generation does not include sufficient context about:
1. The company's industry (telecommunications/mobile operator)
2. The company's parent company (Telecom Argentina)
3. Geographic specificity (Paraguay mobile market)

## Evidence from Research Output

### Competitor Report Sources (Completely Wrong):
```markdown
- [PERSONAL中文(简体)翻译：剑桥词典](https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal)
- [Personal（英文单词）_百度百科](https://baike.baidu.com/item/Personal/19655771)
- ['Industry' Season 4 First Look...](https://www.elle.com/culture/movies-tv/...)
```

### Market Report Sources (Wrong Industry):
```markdown
- Statista "beauty-personal-care" instead of telecommunications
- Personal care industry analysis instead of telecom market
```

### Missing Expected Results:
- No mention of Tigo Paraguay (main competitor)
- No mention of Claro Paraguay (competitor)
- No mention of VOX (competitor)
- No Telecom Argentina financial data
- No CONATEL (Paraguay telecom regulator) data

## Root Cause

The query generation in research phases uses templates like:
- `"{company_name} market share industry"`
- `"{company_name} top competitors"`

Without industry context, search engines interpret "Personal" as:
1. The English adjective
2. Personal care/hygiene products
3. Generic personal services

## Proposed Solutions

### Option A: Pre-Research Company Enrichment
Before running research phases, fetch the company website and extract:
- Industry classification
- Product/service descriptions
- Parent company information

```python
class CompanyEnricher:
    async def enrich(self, company: CompanyProfile) -> CompanyProfile:
        # Fetch website
        content = await browser.fetch(company.url)

        # Extract industry via AI
        industry = await ai.classify_industry(content)

        # Update profile
        company.industry = industry  # "telecommunications"
        company.keywords = ["mobile operator", "telecom", "cellular"]
        return company
```

### Option B: Industry-Aware Query Templates
```python
QUERY_TEMPLATES = {
    "market": [
        "{company_name} {industry} market share",
        "{company_name} {industry} industry trends {country}",
        "{parent_company} subsidiary {company_name} market",
    ],
    "competitor": [
        "{company_name} vs {industry} competitors {country}",
        "{country} {industry} market players",
        "{company_name} competitive landscape {industry}",
    ]
}
```

### Option C: Negative Keywords Filter
Add exclusion terms to search queries:
```python
query = f"{company_name} Paraguay -dictionary -translation -definition -beauty -cosmetics"
```

### Option D: Search Result Validation
Post-filter results that don't match expected context:
```python
def is_relevant(result, company_profile):
    irrelevant_patterns = [
        r"dictionary", r"翻译", r"词典", r"definition",
        r"beauty", r"cosmetics", r"personal care"
    ]
    for pattern in irrelevant_patterns:
        if re.search(pattern, result.title, re.I):
            return False
    return True
```

## Implementation Recommendation

Implement in phases:
1. **Quick Fix**: Add negative keywords to queries (Option C)
2. **Medium Term**: Add result validation (Option D)
3. **Long Term**: Implement company enrichment (Option A)

## Acceptance Criteria

- [ ] Search results are relevant to the actual company
- [ ] No dictionary/translation sites in results
- [ ] Industry context included in queries
- [ ] Competitor analysis finds actual telecom competitors
- [ ] Market analysis covers telecom market, not personal care

## Files to Modify

- `src/core/research_phases.py` - Update query templates
- `src/pipeline/stages/query_generation.py` - Add context awareness
- `src/core/types.py` - Add industry field to CompanyProfile
- New: `src/services/company_enricher.py` - Pre-research enrichment

## Test Cases

```python
def test_telecom_company_queries():
    company = CompanyProfile(
        name="Personal Paraguay",
        url="https://www.personal.com.py",
        industry="telecommunications"
    )
    queries = generate_queries(company, "competitor")

    # Should include industry context
    assert any("telecom" in q or "mobile" in q for q in queries)

    # Should not return dictionary results
    results = await search(queries[0])
    assert not any("dictionary" in r.url for r in results)
```

## Related Issues

- FE-008: Company Type Detection & Adaptive Research
- FE-009: Company Context Enrichment Before Research
