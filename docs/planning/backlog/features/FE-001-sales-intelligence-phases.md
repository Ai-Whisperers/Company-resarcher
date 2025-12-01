# FE-001: Sales Intelligence Research Phases

## Priority: High
## Category: Feature Enhancement
## Status: Backlog

## Summary

Add dedicated research phases to capture B2B sales-ready intelligence that helps identify budget signals, buying process indicators, and stakeholder mapping.

## Current Gap

The current system captures only ~15% of useful sales intelligence:
- No budget availability indicators
- No buying process signals
- No stakeholder/decision-maker mapping
- No vendor consolidation detection
- No technology adoption readiness assessment

## Proposed New Phases

### 08-Sales-Intelligence/ folder

```
08-Sales-Intelligence/
├── 01-Budget-Signals.md
├── 02-Buying-Process.md
├── 03-Stakeholder-Map.md
└── 04-Technology-Readiness.md
```

### Phase Definitions

#### 01-Budget-Signals
**Description**: Funding, hiring budgets, tech spend announcements
**Query Templates**:
- `{company_name} funding announcement 2024 2025`
- `{company_name} budget allocation technology`
- `{company_name} hiring budget expansion`
- `{company_name} investment plans capital expenditure`
- `{company_name} revenue growth budget increase`

**Min Sources**: 3
**Priority**: 25

#### 02-Buying-Process
**Description**: RFPs, vendor evaluations, procurement cycles
**Query Templates**:
- `{company_name} RFP request for proposal`
- `{company_name} vendor selection evaluation`
- `{company_name} procurement process timeline`
- `{company_name} technology purchasing decisions`
- `{industry} enterprise buying cycle {country}`

**Min Sources**: 3
**Priority**: 26

#### 03-Stakeholder-Map
**Description**: Decision makers, influencers, budget owners
**Query Templates**:
- `{company_name} procurement manager director`
- `{company_name} CTO CIO technology leadership`
- `{company_name} VP director purchasing`
- `{company_name} decision makers executives linkedin`
- `{company_name} department heads budget authority`

**Min Sources**: 4
**Priority**: 27

#### 04-Technology-Readiness
**Description**: Current stack, modernization plans, integration needs
**Query Templates**:
- `{company_name} technology stack infrastructure`
- `{company_name} digital transformation initiative`
- `{company_name} modernization cloud migration`
- `{company_name} software systems currently using`
- `{company_name} technology roadmap plans`

**Min Sources**: 3
**Priority**: 28

## Implementation Tasks

- [ ] Add phase definitions to `src/core/research_phases.py`
- [ ] Create Jinja2 templates in `src/templates/`
- [ ] Add unit tests for new phases
- [ ] Test with sample companies
- [ ] Document new output structure

## Template Structure

```markdown
# Budget & Buying Signals

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Budget Health Indicators

### Recent Funding/Investment
{{ funding_signals }}

### Hiring & Growth Signals
{{ hiring_signals }}

### Technology Spend Indicators
{{ tech_spend_signals }}

## Buying Process Intelligence

### Active Procurement Signals
{{ procurement_signals }}

### Vendor Evaluation Activity
{{ vendor_activity }}

### Budget Cycle Timing
{{ budget_timing }}

## Key Stakeholders

| Name | Title | Authority Level | Contact |
|------|-------|-----------------|---------|
{% for person in stakeholders %}
| {{ person.name }} | {{ person.title }} | {{ person.authority }} | {{ person.contact }} |
{% endfor %}

## Technology Readiness Assessment

### Current State
{{ current_tech_state }}

### Modernization Plans
{{ modernization_plans }}

### Integration Opportunities
{{ integration_opportunities }}

## Sources
{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
```

## Success Criteria

- Captures 3+ budget signals per company
- Identifies key decision makers with titles
- Detects active buying/procurement activity
- Assesses technology readiness level
