# FE-004: Team & Talent Intelligence Research Phases

## Priority: High
## Category: Feature Enhancement
## Status: Backlog

## Summary

Add research phases to capture team dynamics, headcount trends, leadership stability, and employee sentiment for comprehensive organizational health assessment.

## Current Gap

The current system captures only ~30% of useful team/talent intelligence:
- No headcount trend analysis
- No hiring velocity metrics
- No executive turnover tracking
- No employee sentiment analysis
- No organizational health indicators

## Proposed New Phases

### 11-Team-Talent/ folder

```
11-Team-Talent/
├── 01-Headcount-Trends.md
├── 02-Leadership-Stability.md
└── 03-Employee-Sentiment.md
```

### Phase Definitions

#### 01-Headcount-Trends
**Description**: Hiring velocity, growth by function, team size
**Query Templates**:
- `{company_name} employee count headcount growth`
- `{company_name} hiring plans expansion`
- `{company_name} layoffs workforce reduction`
- `{company_name} linkedin employee growth`
- `{company_name} engineering team size`
- `{company_name} sales team expansion`

**Min Sources**: 4
**Priority**: 37

#### 02-Leadership-Stability
**Description**: Executive turnover, key departures, succession
**Query Templates**:
- `{company_name} executive turnover departure`
- `{company_name} CEO CFO CTO change`
- `{company_name} leadership transition`
- `{company_name} new executive hire`
- `{company_name} board changes appointments`
- `{company_name} founder departure`

**Min Sources**: 3
**Priority**: 38

#### 03-Employee-Sentiment
**Description**: Glassdoor reviews, culture, retention signals
**Query Templates**:
- `{company_name} glassdoor reviews rating`
- `{company_name} employee satisfaction culture`
- `{company_name} work life balance reviews`
- `{company_name} company culture employees`
- `{company_name} best places to work`
- `{company_name} employee retention turnover`

**Min Sources**: 4
**Priority**: 39

## Implementation Tasks

- [ ] Add phase definitions to `src/core/research_phases.py`
- [ ] Create Jinja2 templates in `src/templates/`
- [ ] Integrate LinkedIn company data (employee count trends)
- [ ] Integrate Glassdoor API for reviews/ratings
- [ ] Add historical comparison logic
- [ ] Add unit tests for new phases
- [ ] Document organizational health scoring

## Template Structure

```markdown
# Team & Talent Intelligence

**Company:** {{ company_name }}
**Date:** {{ generated_at }}
**Organizational Health Score:** {{ org_health_score }}/100

## Headcount Overview

### Current Size
- Total Employees: {{ total_employees }}
- YoY Growth: {{ yoy_growth }}%
- 3-Year CAGR: {{ employee_cagr }}%

### Headcount by Function
| Function | Count | % of Total | YoY Change |
|----------|-------|------------|------------|
{% for dept in departments %}
| {{ dept.name }} | {{ dept.count }} | {{ dept.pct }}% | {{ dept.change }} |
{% endfor %}

### Hiring Velocity
{{ hiring_velocity }}

### Recent Changes
{{ recent_changes }}

## Leadership Stability

### Current Leadership Team
| Name | Role | Tenure | Previous |
|------|------|--------|----------|
{% for exec in executives %}
| {{ exec.name }} | {{ exec.role }} | {{ exec.tenure }} | {{ exec.previous }} |
{% endfor %}

### Leadership Changes (Last 24 Months)
{{ leadership_changes }}

### Executive Turnover Rate
- C-Suite Turnover: {{ csuite_turnover }}%
- VP+ Turnover: {{ vp_turnover }}%
- Industry Benchmark: {{ benchmark_turnover }}%

### Succession Planning
{{ succession_status }}

## Employee Sentiment

### Glassdoor Metrics
| Metric | Score | Trend | Industry Avg |
|--------|-------|-------|--------------|
| Overall Rating | {{ overall_rating }}/5 | {{ rating_trend }} | {{ industry_rating }} |
| CEO Approval | {{ ceo_approval }}% | {{ ceo_trend }} | {{ industry_ceo }} |
| Recommend to Friend | {{ recommend }}% | {{ recommend_trend }} | {{ industry_recommend }} |
| Career Opportunities | {{ career_rating }}/5 | {{ career_trend }} | - |
| Compensation & Benefits | {{ comp_rating }}/5 | {{ comp_trend }} | - |
| Work-Life Balance | {{ wlb_rating }}/5 | {{ wlb_trend }} | - |
| Culture & Values | {{ culture_rating }}/5 | {{ culture_trend }} | - |

### Review Themes

#### Positive Themes
{{ positive_themes }}

#### Negative Themes
{{ negative_themes }}

### Sample Reviews
{{ sample_reviews }}

## Organizational Health Indicators

### Strengths
{{ org_strengths }}

### Concerns
{{ org_concerns }}

### Recommendations
{{ org_recommendations }}

## Sources
{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
```

## Data Sources to Integrate

1. **LinkedIn** - Employee count, growth trends, function breakdown
2. **Glassdoor** - Reviews, ratings, CEO approval
3. **Blind** - Anonymous employee feedback
4. **News** - Executive announcements, layoffs
5. **SEC Filings** - Executive compensation, departures

## Success Criteria

- Headcount trends for 70%+ of companies
- Glassdoor ratings captured when available
- Executive changes documented
- Organizational health score calculated
