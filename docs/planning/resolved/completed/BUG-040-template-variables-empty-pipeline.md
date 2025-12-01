# BUG-040: Template Variables Empty in Pipeline Stages

## Priority: HIGH
## Category: Bug/Template Rendering
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Multiple template variables (`company.name`, `industry`, etc.) are rendering as empty strings or "None" in generated reports, even when the data should be available from the pipeline context.

## Problem Statement

Reports show empty or placeholder values for key template variables:

```markdown
# Financials
**Company:**
**Date:** 2025-11-28 19:56:53.977430

# Competitor List
**Company:**
**Industry:**

# Brand Positioning
**Company:**
```

Only the Sales report correctly shows `**Company:** Personal Paraguay`.

## Evidence from Output Files

### Market Report (01-Market.md template)
```markdown
**Industry:** None
**Region:**
```

### Financial Report (02-Financials.md template)
```markdown
**Company:**
```

### Competitor Report (03-Competitors.md template)
```markdown
**Company:**
**Industry:**
```

### Brand Report (04-Brand.md template)
```markdown
**Company:**
```

### Sales Report (05-Sales-Strategy.md template) - WORKING
```markdown
# Sales Strategy: Personal Paraguay
```

## Root Cause Analysis

### Two Different Code Paths

The system has two different rendering paths:

#### Path 1: Pipeline Stages (research.py) - BROKEN
```python
# src/pipeline/stages/research.py - ReportGenerationStage.execute()

template_context = {
    **input.data,  # Only AI-generated data
    "company": input.company,  # Added in fix, but may not reach all templates
    "agent_name": f"{self._research_type.title()}Analyst",
    "timestamp": "N/A",
    "sources": [...],
}
```

**Problem:** The `input.data` dictionary from AI response may not include all required fields.

#### Path 2: BaseAgent._render() - FIXED
```python
# src/agents/base_agent.py - _render()

data["company"] = company  # Explicitly added
data["agent_name"] = self.agent_name
data["timestamp"] = data.get("timestamp", "N/A")
```

### Template Variable Mapping

| Template Variable | Where It Should Come From | Current Status |
|-------------------|---------------------------|----------------|
| `company.name` | `CompanyProfile.name` | Empty in 4/5 reports |
| `company.industry` | `CompanyProfile.industry` | Empty/None |
| `industry` | Top-level variable | Not passed |
| `region` | Should be extracted from company | Not passed |
| `agent_name` | Generated from research type | Working |
| `timestamp` | Current datetime | Working |
| `sources` | Filtered ResearchSource list | Working |

## Affected Templates

### 01-Market.md
```jinja2
**Industry:** {{ industry }}
**Region:** {{ region }}
```
- `industry` not in context
- `region` not in context

### 02-Financials.md
```jinja2
**Company:** {{ company.name if company else '' }}
```
- `company` may be None or missing `.name`

### 03-Competitors.md
```jinja2
**Company:** {{ company.name if company else '' }}
**Industry:** {{ company.industry if company else '' }}
```
- Same issues

### 04-Brand.md
```jinja2
**Company:** {{ company.name if company else '' }}
```
- Same issue

### 05-Sales-Strategy.md
```jinja2
# Sales Strategy: {{ company.name }}
```
- Working because SalesAgent uses BaseAgent._render() which was fixed

## Proposed Solutions

### Solution 1: Standardize Template Context (Recommended)

Create a helper function to build consistent template context:

```python
# src/core/template_context.py

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from .types import CompanyProfile, ResearchSource

@dataclass
class TemplateContext:
    """Standardized context for all templates."""
    company: CompanyProfile
    research_type: str
    sources: List[ResearchSource]
    data: Dict[str, Any]  # AI-generated data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        # Filter usable sources
        usable_sources = [s for s in self.sources if s.is_usable()]

        return {
            # Company info (always available)
            "company": self.company,
            "company_name": self.company.name,
            "industry": self.company.industry or "Unknown",
            "region": self.company.country or "Global",

            # Metadata
            "agent_name": f"{self.research_type.title()}Analyst",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "research_type": self.research_type,

            # Sources
            "sources": [
                {"title": s.title, "url": s.url, "source_type": s.source_type}
                for s in usable_sources
            ],

            # AI-generated data (spread last so it can override defaults)
            **self.data,
        }
```

### Solution 2: Fix ReportGenerationStage

```python
# src/pipeline/stages/research.py

async def execute(self, input: AnalysisOutput, ctx: RequestContext):
    # Build complete template context
    usable_sources = [s for s in input.sources if s.is_usable()]

    template_context = {
        # Company info (CRITICAL - must be first-class)
        "company": input.company,
        "company_name": input.company.name,
        "industry": input.company.industry or "N/A",
        "region": input.company.country or "Global",

        # Metadata
        "agent_name": f"{self._research_type.title()}Analyst",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),

        # Sources
        "sources": [
            {"title": s.title, "url": s.url, "source_type": s.source_type}
            for s in usable_sources
        ],

        # AI data last (can override above)
        **input.data,
    }

    markdown_content = renderer.render(template_name, **template_context)
```

### Solution 3: Update Templates with Defaults

Add fallback defaults in templates:

```jinja2
**Company:** {{ company.name | default('Unknown Company', true) }}
**Industry:** {{ company.industry | default(industry, true) | default('Unknown Industry', true) }}
**Region:** {{ region | default(company.country, true) | default('Global', true) }}
```

## Files to Modify

1. `src/pipeline/stages/research.py` - Fix ReportGenerationStage context
2. `src/templates/01-Market.md` - Add fallback defaults
3. `src/templates/02-Financials.md` - Add fallback defaults
4. `src/templates/03-Competitors.md` - Add fallback defaults
5. `src/templates/04-Brand.md` - Add fallback defaults
6. New: `src/core/template_context.py` - Standardized context builder

## Acceptance Criteria

- [ ] All reports show company name correctly
- [ ] Industry is displayed (or "Unknown" if not available)
- [ ] Region/Country is displayed
- [ ] No empty `**Company:** ` lines in any report
- [ ] No "None" values visible in reports
- [ ] All 5 report types render consistently

## Testing Plan

1. Run research for "Personal Paraguay"
2. Verify all 5 reports have company name
3. Check no "None" or empty strings appear
4. Test with company that has industry specified
5. Test with company that has no industry (should show "Unknown")

## Related Issues

- BUG-036: Sales template missing company variable (FIXED)
- BUG-041: Company name missing from most reports
- TECH-026: Execute research cycle too long

## Notes

This is partially fixed by the BUG-036 fix, but that fix only applies to the `BaseAgent._render()` path. The pipeline stages use a different code path (`ReportGenerationStage`) that needs the same fix applied.
