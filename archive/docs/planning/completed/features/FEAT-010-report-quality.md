# FEAT-010: Report Quality System

## Priority: Medium

## Category: Features / Report Quality

## Status: Backlog

## Summary

Implement report quality validation, scoring, and templates to ensure consistent high-quality outputs.

## Problem Areas

| Issue | Impact |
|-------|--------|
| No output validation | Inconsistent report structure |
| Boilerplate text in outputs | Low value sections |
| No quality metrics | Can't measure improvement |
| Missing required sections | Incomplete reports |

## Implementation Tasks

### A. Report Schema Validation

- [ ] Create `src/templates/report_schema.py`
- [ ] Define Pydantic models for report structure
- [ ] Validate section content length minimums
- [ ] Check for boilerplate text
- [ ] Ensure required sections present

```python
class ReportSection(BaseModel):
    title: str
    content: str = Field(min_length=100)
    sources: list[str] = Field(min_items=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @validator("content")
    def check_not_boilerplate(cls, v):
        boilerplate = ["information not available", "could not find"]
        if any(phrase in v.lower() for phrase in boilerplate):
            raise ValueError("Section contains boilerplate text")
        return v

class FullReport(BaseModel):
    company: str
    executive_summary: str = Field(min_length=200)
    sections: list[ReportSection] = Field(min_items=5)
```

### B. Quality Scoring System

- [ ] Create `src/services/report_scorer.py`
- [ ] Implement multi-dimensional scoring:
  - Completeness (expected sections present)
  - Source quality (authoritative sources used)
  - Depth (specific data vs generic statements)
  - Actionability (useful recommendations)
  - Freshness (recent sources used)
- [ ] Generate overall quality score
- [ ] Provide improvement suggestions

```python
scores = {
    "completeness": 0.85,
    "source_quality": 0.72,
    "depth": 0.68,
    "actionability": 0.75,
    "freshness": 0.90,
    "overall": 0.78
}
```

### C. Depth Indicators

- [ ] Detect specific percentages and numbers
- [ ] Detect financial figures ($XXM/B)
- [ ] Detect comparative analysis ("compared to")
- [ ] Detect causal reasoning ("because", "therefore")
- [ ] Score based on depth indicator density

### D. Source Bibliography

- [ ] Generate formatted source list
- [ ] Include access dates
- [ ] Categorize by type (primary, secondary, news)
- [ ] Flag potentially unreliable sources
- [ ] Link sources to specific claims

### E. Report Templates

- [ ] Create structured templates per report type
- [ ] Ensure consistent formatting
- [ ] Include placeholder guidance
- [ ] Support multiple output formats (MD, HTML, PDF)

## Quality Thresholds

| Metric | Minimum | Target |
|--------|---------|--------|
| Completeness | 0.70 | 0.90 |
| Source Quality | 0.60 | 0.80 |
| Depth | 0.50 | 0.75 |
| Actionability | 0.50 | 0.70 |
| Freshness | 0.70 | 0.90 |
| Overall | 0.60 | 0.80 |

## Acceptance Criteria

- [ ] All reports pass schema validation
- [ ] Quality scores generated for every report
- [ ] Reports below threshold flagged for review
- [ ] Boilerplate content automatically rejected
- [ ] Source bibliography included in all reports

## Technical Notes

- Integrate with existing template renderer
- Consider LLM-based quality assessment for nuanced scoring
- Track quality metrics over time for improvement
