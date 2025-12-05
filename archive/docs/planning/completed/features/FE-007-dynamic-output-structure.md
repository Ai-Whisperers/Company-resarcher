# FE-007: Dynamic Output Structure Based on Available Data

## Priority: Medium
## Category: Feature Enhancement
## Status: Backlog

## Summary

Modify the output generation system to dynamically create folders and files based on the data actually found during research, rather than generating all pre-defined folders regardless of content quality.

## Current Behavior

- All 24+ research phases run regardless of data availability
- Empty or sparse reports are generated when data isn't found
- Fixed folder structure even when sections are irrelevant
- No data quality thresholds for report generation

## Proposed Behavior

- Generate reports only when sufficient quality data is found
- Create folders dynamically based on successful research phases
- Include data quality scores in output
- Provide "data gaps" summary showing what couldn't be found

## Implementation Design

### 1. Data Quality Thresholds

```python
# src/core/quality_thresholds.py

QUALITY_THRESHOLDS = {
    "min_sources": 2,           # Minimum sources to generate report
    "min_content_length": 500,  # Minimum characters of useful content
    "min_confidence": 0.6,      # Minimum AI confidence score
    "required_fields_pct": 0.5, # % of template fields that must be filled
}

def should_generate_report(phase_result: PhaseResult) -> bool:
    """Determine if phase has enough quality data for report."""
    return (
        len(phase_result.sources) >= QUALITY_THRESHOLDS["min_sources"]
        and len(phase_result.content) >= QUALITY_THRESHOLDS["min_content_length"]
        and phase_result.confidence >= QUALITY_THRESHOLDS["min_confidence"]
    )
```

### 2. Dynamic Folder Creation

```python
# src/core/output_manager.py (enhanced)

class DynamicOutputManager:
    def save_research_output(self, company_name: str, results: ResearchResults):
        """Save only phases with sufficient data quality."""

        generated_reports = []
        skipped_phases = []

        for phase in results.phases:
            if should_generate_report(phase):
                self._save_phase_report(company_name, phase)
                generated_reports.append(phase.name)
            else:
                skipped_phases.append({
                    "phase": phase.name,
                    "reason": self._get_skip_reason(phase),
                    "sources_found": len(phase.sources),
                })

        # Generate summary of what was/wasn't found
        self._save_research_summary(company_name, generated_reports, skipped_phases)
```

### 3. Research Summary Report

Create a new `00-Research-Summary.md` that shows:

```markdown
# Research Summary: {{ company_name }}

**Date:** {{ generated_at }}
**Total Phases Attempted:** {{ total_phases }}
**Reports Generated:** {{ generated_count }}
**Data Gaps:** {{ gap_count }}

## Successfully Generated Reports

| Report | Sources | Confidence | Quality |
|--------|---------|------------|---------|
{% for report in generated_reports %}
| {{ report.name }} | {{ report.sources }} | {{ report.confidence }}% | {{ report.quality }} |
{% endfor %}

## Data Gaps (Reports Not Generated)

| Phase | Reason | Sources Found | Recommendation |
|-------|--------|---------------|----------------|
{% for gap in data_gaps %}
| {{ gap.phase }} | {{ gap.reason }} | {{ gap.sources }} | {{ gap.recommendation }} |
{% endfor %}

## Data Quality Score

**Overall Score:** {{ overall_quality_score }}/100

### Score Breakdown
- Source Diversity: {{ source_diversity }}/25
- Content Depth: {{ content_depth }}/25
- Data Recency: {{ data_recency }}/25
- Coverage Completeness: {{ coverage }}/25

## Recommended Follow-up Research

{{ followup_recommendations }}
```

### 4. Conditional Phase Execution

```python
# src/pipeline/smart_orchestrator.py

class SmartOrchestrator:
    """Orchestrator that adapts research based on company type."""

    def determine_relevant_phases(self, company: CompanyProfile) -> List[str]:
        """Select phases based on company characteristics."""

        phases = ["strategic_context", "market_intelligence"]  # Always run

        if company.is_public:
            phases.extend(["financials", "sec_filings", "stock_analysis"])
        elif company.has_funding:
            phases.extend(["funding_history", "investor_analysis"])

        if company.industry in ["tech", "saas", "software"]:
            phases.extend(["tech_stack", "patents", "github_activity"])

        if company.employee_count and company.employee_count > 50:
            phases.extend(["glassdoor", "leadership", "org_structure"])

        return phases
```

### 5. Output Structure Options

**Option A: Flat Structure (Simpler)**
```
output/Personal Paraguay/
├── 00-Research-Summary.md
├── 01-Company-Overview.md
├── 02-Market-Intelligence.md
├── 03-Competitive-Landscape.md
├── 04-Key-People.md
└── 99-Sources/
    └── Source-Log.md
```

**Option B: Categorized Structure (Current, but dynamic)**
```
output/Personal Paraguay/
├── 00-Research-Summary.md
├── 00-Strategic-Context/
│   ├── Company-Overview.md
│   └── Key-People.md
├── 01-Market-Intelligence/
│   └── Market-Size-Growth.md
├── 03-Competitive-Landscape/
│   ├── Competitor-List.md
│   └── Pricing-Analysis.md
└── 99-Sources/
    └── Source-Log.md
```

**Option C: Quality-Tiered Structure**
```
output/Personal Paraguay/
├── 00-Research-Summary.md
├── high-confidence/           # >80% confidence
│   ├── Company-Overview.md
│   └── Competitor-List.md
├── medium-confidence/         # 60-80% confidence
│   ├── Market-Intelligence.md
│   └── Key-People.md
├── low-confidence/            # <60% confidence (for review)
│   └── Financials.md
└── 99-Sources/
    └── Source-Log.md
```

## Configuration

```python
# src/core/config.py

class OutputConfig:
    output_mode: str = "dynamic"  # "dynamic" | "static" | "quality_tiered"
    min_quality_threshold: float = 0.6
    generate_summary: bool = True
    include_low_quality: bool = False  # Include reports below threshold
    quality_folder_structure: bool = False  # Use Option C
```

## Migration Path

1. **Phase 1**: Add quality scoring without changing output
2. **Phase 2**: Add Research Summary report
3. **Phase 3**: Make folder generation conditional
4. **Phase 4**: Add smart phase selection

## Success Criteria

- Reports only generated when quality threshold met
- Research Summary shows complete picture
- Data gaps clearly documented
- Quality scores visible to users
- Configuration allows static mode for backwards compatibility
