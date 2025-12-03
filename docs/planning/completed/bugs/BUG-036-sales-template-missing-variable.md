# BUG-005: Sales Template Missing Company Variable

## Priority: HIGH
## Category: Bug/Template
## Status: Backlog
## Discovered: 2025-11-28

## Summary

The Sales Strategy template (`05-Sales-Strategy.md`) fails to render because the `company` variable is not passed to the template context.

## Problem Statement

When generating the sales report, the template renderer throws an error:
```
template_renderer - ERROR - Template error in '05-Sales-Strategy.md': 'company' is undefined
```

The output file contains only:
```markdown
# Error rendering 05-Sales-Strategy.md

'company' is undefined
```

## Root Cause

The template expects a `company` variable but the pipeline stage doesn't include it in the context passed to the renderer.

### Template Expectation
```jinja2
# Sales Strategy for {{ company.name }}

...
{{ company.website }}
```

### Pipeline Stage (likely missing)
```python
context = {
    "analysis": analysis_result,
    "sources": sources,
    # Missing: "company": company_profile
}
```

## Impact

- Sales Strategy report not generated
- Missing sales intelligence data
- Incomplete research output

## Proposed Solution

### Fix 1: Pass company to template context

In the report generation stage:
```python
async def generate_report(self, phase: str, analysis: dict, sources: list, company: CompanyProfile):
    context = {
        "analysis": analysis,
        "sources": sources,
        "company": company,  # Add this
        "date": datetime.now(),
    }
    return self.renderer.render(f"{phase}.md", context)
```

### Fix 2: Make template defensive

Update template to handle missing company:
```jinja2
# Sales Strategy{% if company %} for {{ company.name }}{% endif %}

{% if company and company.website %}
Website: {{ company.website }}
{% endif %}
```

## Acceptance Criteria

- [ ] Sales Strategy report renders without errors
- [ ] Company name appears in report header
- [ ] All 5 research phases produce valid output files

## Files to Modify

- `src/pipeline/stages/report_generation.py` - Pass company to context
- `src/templates/05-Sales-Strategy.md` - Verify variable usage
- `src/core/template_renderer.py` - Consider adding default context

## Investigation Steps

1. Check which templates use `company` variable
2. Verify all pipeline stages pass consistent context
3. Add tests for template rendering with all required variables

## Related Issues

- Review all templates for similar missing variable issues
