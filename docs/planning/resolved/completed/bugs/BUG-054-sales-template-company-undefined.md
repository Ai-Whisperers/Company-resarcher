# BUG-054: Sales Template "company" Variable Undefined

## Summary
The sales template (05-Sales-Strategy.md) throws a Jinja2 error: `'company' is undefined`. This causes the sales report to fail or render with errors.

## Severity
**MEDIUM** - Sales report generation fails, but other reports work

## Symptoms
### Log Evidence
```
15:58:37 - template_renderer - ERROR - Template error in '05-Sales-Strategy.md': 'company' is undefined
```

### Impact
- Sales strategy report not generated
- Pipeline completes but with incomplete output
- Missing critical sales insights

## Root Cause Analysis

### 1. Template Expects `company` Variable
The sales template likely uses:
```jinja2
# Sales Strategy for {{ company.name }}

## Company Overview
{{ company.description }}
```

But the template context only provides different variable names.

### 2. Inconsistent Variable Naming Across Templates
Different templates may use different variable names:
- Some use `company`
- Some use `company_name`
- Some use `company_info`

### 3. Template Context Not Populated Correctly
```python
# src/pipeline/stages/report_generation.py
context = {
    "company_name": company.name,  # But template expects "company"
    "analysis": analysis_result,
    # Missing: "company": company
}
```

## Affected Files
- `src/templates/05-Sales-Strategy.md` - Template file
- `src/pipeline/stages/report_generation.py` - Context building
- `src/utils/template_renderer.py` - Template rendering

## Investigation Required
1. Read the sales template to see what variables it expects
2. Check what context variables are passed to templates
3. Compare with other working templates

## Proposed Solutions

### Solution 1: Add Missing Variable to Context
```python
# src/pipeline/stages/report_generation.py
def build_template_context(
    company: CompanyInfo,
    analysis: AnalysisResult,
    sources: List[Source]
) -> dict:
    return {
        # Add both for compatibility
        "company": company,
        "company_name": company.name,
        "company_url": company.url,
        "company_info": company,  # Alias

        "analysis": analysis,
        "sources": sources,
    }
```

### Solution 2: Standardize Template Variables
Create a template variable specification:
```python
# src/templates/__init__.py
TEMPLATE_VARIABLES = {
    "company": "CompanyInfo object",
    "analysis": "AnalysisResult object",
    "sources": "List[Source]",
    "report_type": "str (market, financial, etc.)",
}
```

Update ALL templates to use consistent variable names.

### Solution 3: Add Template Validation
```python
# src/utils/template_renderer.py
def validate_template_variables(template_name: str, context: dict) -> List[str]:
    """Check if all required variables are in context."""
    required = {
        "01-Market-Analysis.md": ["company", "analysis"],
        "02-Financial-Overview.md": ["company", "analysis"],
        "05-Sales-Strategy.md": ["company", "analysis"],
    }

    missing = []
    for var in required.get(template_name, []):
        if var not in context or context[var] is None:
            missing.append(var)

    return missing
```

### Solution 4: Fix Template with Fallback
```jinja2
{# 05-Sales-Strategy.md #}
{% set company_name = company.name if company else company_name %}
{% set company_url = company.url if company else company_url %}

# Sales Strategy for {{ company_name }}
```

## Test Cases
```python
def test_sales_template_renders():
    renderer = TemplateRenderer()
    context = {
        "company": CompanyInfo(name="Test", url="https://test.com"),
        "analysis": {...},
    }
    result = renderer.render("05-Sales-Strategy.md", context)
    assert "Test" in result
    assert "'company' is undefined" not in result

def test_all_templates_have_required_vars():
    templates = glob("src/templates/*.md")
    for template in templates:
        context = build_template_context(mock_company, mock_analysis, [])
        result = renderer.render(template, context)
        assert "undefined" not in result.lower()
```

## Acceptance Criteria
- [ ] Sales template renders without "undefined" error
- [ ] All templates use consistent variable names
- [ ] Template context includes all required variables
- [ ] Template validation catches missing variables before render
- [ ] Sales report is generated successfully

## Related Issues
- BUG-036: Sales template missing variable (similar issue)
- Template consistency

## Labels
`medium`, `bug`, `template`, `sales`
