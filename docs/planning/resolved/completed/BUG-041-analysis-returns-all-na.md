# BUG-041: AI Analysis Returns All N/A Values

## Priority: CRITICAL
## Category: Bug/AI Analysis
## Status: Backlog
## Discovered: 2025-11-28

## Summary

The AI analysis phase is returning "N/A" for all data fields even when source content is available, resulting in reports filled with placeholder values instead of actual analysis.

## Problem Statement

Every structured field in the analysis output is "N/A":

```markdown
## Market Overview
**TAM (Total Addressable Market):** N/A
**SAM (Serviceable Available Market):** N/A
**SOM (Serviceable Obtainable Market):** N/A

## Growth Projections
**CAGR:** N/A
**Forecast (2025-2030):** N/A

### Key Growth Drivers
- N/A

### Market Challenges
- N/A
```

This pattern repeats across Market, Financial, and Competitor reports.

## Evidence from All Reports

### Market Report
| Field | Value |
|-------|-------|
| TAM | N/A |
| SAM | N/A |
| SOM | N/A |
| CAGR | N/A |
| Forecast | N/A |
| Growth Drivers | N/A |
| Challenges | N/A |

### Financial Report
| Field | Value |
|-------|-------|
| Revenue | N/A |
| Revenue Growth | N/A |
| Profitability | N/A |
| Funding History | N/A |
| Stock Performance | N/A |

### Competitor Report
| Field | Value |
|-------|-------|
| Direct Competitors | N/A |
| Indirect Competitors | N/A |
| Emerging Threats | N/A |

## Root Cause Analysis

### Hypothesis 1: No Source Content Passed to AI

The log shows warnings:
```
15:58:32 - pipeline - WARNING - [analysis_market] No source content available for analysis
```

If `total_sources=0`, the AI has nothing to analyze.

### Hypothesis 2: Source Content Too Short/Filtered

Even when sources exist, they may be:
- Blocked pages (Cloudflare, CAPTCHA)
- Dictionary pages (irrelevant content)
- Too short (< 100 chars)

All get filtered, leaving nothing for analysis.

### Hypothesis 3: AI Prompt Not Extracting Data

The prompt may not be instructing the AI to extract specific data points, or the AI is being too conservative with "N/A" when data isn't explicit.

### Hypothesis 4: JSON Parsing Failures

The AI response may contain data but JSON parsing fails:
```
pipeline - ERROR - [analysis_competitor] Analysis failed: Expecting value: line 1 column 1 (char 0)
```

Empty response → empty data → all N/A.

## Evidence of Root Causes

### From Logs - No Sources:
```
[search_execution] Search completed total_sources=0
[analysis_market] No source content available for analysis
```

### From Logs - JSON Error:
```
[analysis_competitor] Analysis failed: Expecting value: line 1 column 1 (char 0)
```

### From Output - Dictionary Sources:
```
Sources:
- [personal是什么意思_personal的翻译](https://www.iciba.com/word?w=personal)
- [PERSONAL中文(简体)翻译](https://dictionary.cambridge.org/zhs/词典/英语-汉语-简体/personal)
```

Even when sources exist, they're irrelevant dictionaries.

## Flow Diagram

```
Search Query: "Personal Paraguay market share"
       │
       ▼
DuckDuckGo Returns: 3 results
       │
       ▼
Results Include: Dictionary sites, unrelated pages
       │
       ▼
Browser Fetches: Pages with "personal" word definitions
       │
       ▼
Content Filtering: Most filtered as < 100 chars or error pages
       │
       ▼
AI Receives: Empty or irrelevant content
       │
       ▼
AI Returns: All N/A (nothing to analyze)
       │
       ▼
Report Shows: N/A everywhere
```

## Proposed Solutions

### Solution 1: Ensure Minimum Sources Before Analysis

```python
# src/pipeline/stages/research.py - AnalysisStage

async def execute(self, input: SearchOutput, ctx: RequestContext):
    usable_sources = [s for s in input.sources if s.is_usable()]

    if len(usable_sources) < 3:
        ctx.logger.warning(
            f"Only {len(usable_sources)} usable sources. "
            f"Minimum 3 required for reliable analysis."
        )
        # Option A: Return error
        # return Err(StageError("Insufficient sources for analysis"))

        # Option B: Try additional searches
        additional = await self._fetch_additional_sources(ctx)
        usable_sources.extend(additional)

    if not usable_sources:
        return Ok(AnalysisOutput(
            company=input.company,
            research_type=self._research_type,
            data={"error": "No usable sources found"},
            sources=[],
        ))

    # Proceed with analysis...
```

### Solution 2: Improve AI Prompt for Partial Data

```python
ANALYSIS_PROMPT = """
Analyze the following sources about {company_name}.

IMPORTANT INSTRUCTIONS:
1. Extract any available data, even if incomplete
2. For missing data, explain WHY it's unavailable (e.g., "Not found in sources")
3. Never return just "N/A" - provide context
4. If sources are irrelevant, state "Sources do not contain relevant information"
5. Make reasonable inferences where appropriate, clearly labeled as inferences

Sources:
{source_content}

Return JSON with the following structure:
{{
    "market_size": {{"value": "...", "source": "...", "confidence": "high/medium/low"}},
    "growth_rate": {{"value": "...", "source": "...", "confidence": "..."}},
    ...
}}
"""
```

### Solution 3: Retry with Alternative Queries

```python
async def _fetch_with_retry(self, queries: List[str], ctx: RequestContext):
    sources = await self._search(queries)

    if len(sources) < 3:
        # Try alternative queries
        alt_queries = self._generate_alternative_queries(queries, ctx.company)
        additional = await self._search(alt_queries)
        sources.extend(additional)

    return sources

def _generate_alternative_queries(self, failed_queries, company):
    """Generate alternative queries when primary queries fail."""
    return [
        f'"{company.name}" site:linkedin.com',
        f'"{company.name}" site:crunchbase.com',
        f'{company.name} {company.industry} news',
        f'{company.name} company profile',
    ]
```

### Solution 4: Source Quality Threshold

```python
class SourceQualityChecker:
    MIN_CONTENT_LENGTH = 500  # Require substantial content
    MIN_RELEVANCE_SCORE = 0.3
    REQUIRED_COMPANY_MENTIONS = 2

    def is_quality_source(self, source: ResearchSource, company_name: str) -> bool:
        if len(source.content) < self.MIN_CONTENT_LENGTH:
            return False

        mentions = source.content.lower().count(company_name.lower())
        if mentions < self.REQUIRED_COMPANY_MENTIONS:
            return False

        return True
```

## Files to Modify

1. `src/pipeline/stages/research.py` - Add source quality checks
2. `src/prompts/market_analysis.txt` - Improve prompts
3. `src/prompts/financial_analysis.txt` - Improve prompts
4. `src/prompts/competitor_analysis.txt` - Improve prompts
5. New: `src/services/source_quality.py` - Quality checking

## Acceptance Criteria

- [ ] Reports contain actual data, not just N/A
- [ ] When data unavailable, explanation is provided
- [ ] Minimum source threshold enforced before analysis
- [ ] Alternative queries tried when primary fails
- [ ] AI confidence levels included in output

## Testing Plan

1. Run with company that has abundant online data (e.g., "Apple Inc")
2. Verify actual market data is extracted
3. Run with obscure company
4. Verify graceful degradation with explanations
5. Test prompt improvements with various source qualities

## Related Issues

- BUG-038: Search fallback not triggering
- BUG-039: Dictionary sites in results
- BUG-035: Wrong company context
- FE-009: Company context enrichment
- FE-010: Source quality filtering

## Impact

**Without Fix:** Research tool produces empty reports that provide no value to users.

**Severity:** CRITICAL - Core functionality is broken.
