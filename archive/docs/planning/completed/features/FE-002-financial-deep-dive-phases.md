# FE-002: Financial Deep-Dive Research Phases

## Priority: High
## Category: Feature Enhancement
## Status: Backlog

## Summary

Add comprehensive financial intelligence phases to capture unit economics, revenue breakdowns, cash flow analysis, and margin trends for investment analysis.

## Current Gap

The current system captures only ~15% of useful financial intelligence:
- No unit economics (CAC, LTV, LTV/CAC ratio)
- No revenue breakdown by product/geography/customer
- No cash flow or burn rate analysis
- No margin trend analysis
- No customer concentration metrics

## Proposed New Phases

### 09-Financial-Deep-Dive/ folder

```
09-Financial-Deep-Dive/
├── 01-Unit-Economics.md
├── 02-Revenue-Breakdown.md
├── 03-Cash-Flow-Analysis.md
└── 04-Margin-Trends.md
```

### Phase Definitions

#### 01-Unit-Economics
**Description**: CAC, LTV, payback period, net revenue retention
**Query Templates**:
- `{company_name} customer acquisition cost CAC`
- `{company_name} lifetime value LTV metrics`
- `{company_name} churn rate retention`
- `{company_name} net revenue retention NRR`
- `{company_name} payback period unit economics`
- `{company_name} sales efficiency magic number`

**Min Sources**: 4
**Priority**: 29

#### 02-Revenue-Breakdown
**Description**: Revenue by product, geography, customer type
**Query Templates**:
- `{company_name} revenue breakdown segments`
- `{company_name} revenue by product line`
- `{company_name} revenue by geography region`
- `{company_name} customer segmentation revenue`
- `{company_name} recurring revenue ARR MRR`
- `{company_name} enterprise vs SMB revenue`

**Min Sources**: 4
**Priority**: 30

#### 03-Cash-Flow-Analysis
**Description**: Operating cash, burn rate, runway
**Query Templates**:
- `{company_name} cash flow statement operating`
- `{company_name} burn rate monthly runway`
- `{company_name} free cash flow generation`
- `{company_name} working capital trends`
- `{company_name} cash position liquidity`

**Min Sources**: 3
**Priority**: 31

#### 04-Margin-Trends
**Description**: Gross, operating, net margins over time
**Query Templates**:
- `{company_name} gross margin trends`
- `{company_name} operating margin EBITDA`
- `{company_name} net profit margin history`
- `{company_name} margin expansion improvement`
- `{company_name} cost structure analysis`

**Min Sources**: 3
**Priority**: 32

## Implementation Tasks

- [ ] Add phase definitions to `src/core/research_phases.py`
- [ ] Create Jinja2 templates in `src/templates/`
- [ ] Integrate SEC EDGAR API for public companies
- [ ] Add Crunchbase/PitchBook data source (if available)
- [ ] Add unit tests for new phases
- [ ] Document new output structure

## Template Structure

```markdown
# Financial Deep-Dive

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Unit Economics

| Metric | Value | Industry Benchmark | Trend |
|--------|-------|-------------------|-------|
| Customer Acquisition Cost (CAC) | {{ cac }} | {{ cac_benchmark }} | {{ cac_trend }} |
| Lifetime Value (LTV) | {{ ltv }} | {{ ltv_benchmark }} | {{ ltv_trend }} |
| LTV/CAC Ratio | {{ ltv_cac_ratio }} | >3x healthy | {{ ltv_cac_trend }} |
| Payback Period | {{ payback_months }} months | {{ payback_benchmark }} | {{ payback_trend }} |
| Net Revenue Retention | {{ nrr }}% | >100% healthy | {{ nrr_trend }} |
| Churn Rate | {{ churn }}% | {{ churn_benchmark }} | {{ churn_trend }} |

## Revenue Breakdown

### By Product/Service
{{ revenue_by_product }}

### By Geography
{{ revenue_by_geography }}

### By Customer Segment
{{ revenue_by_segment }}

### Revenue Quality
- Recurring vs One-time: {{ recurring_ratio }}
- Customer Concentration (Top 10): {{ top_10_concentration }}%

## Cash Flow Analysis

### Operating Cash Flow
{{ operating_cash_flow }}

### Burn Rate & Runway
- Monthly Burn Rate: {{ monthly_burn }}
- Cash Runway: {{ runway_months }} months
- Last Funding: {{ last_funding_date }}

### Working Capital
{{ working_capital_analysis }}

## Margin Trends (3-Year)

| Year | Gross Margin | Operating Margin | Net Margin |
|------|--------------|------------------|------------|
{% for year in margin_years %}
| {{ year.year }} | {{ year.gross }}% | {{ year.operating }}% | {{ year.net }}% |
{% endfor %}

### Margin Analysis
{{ margin_analysis }}

## Investment Signals

### Positive Indicators
{{ positive_signals }}

### Risk Indicators
{{ risk_signals }}

## Sources
{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
```

## Data Sources to Integrate

1. **SEC EDGAR** - 10-K, 10-Q filings for public companies
2. **Crunchbase** - Funding, valuation, investors
3. **PitchBook** - Private company financials
4. **Yahoo Finance** - Stock data, analyst estimates
5. **Company IR pages** - Investor presentations, earnings calls

## Success Criteria

- Captures unit economics for 60%+ of researched companies
- Revenue breakdown available for public companies
- Cash flow metrics for funded startups
- 3-year margin trend analysis
