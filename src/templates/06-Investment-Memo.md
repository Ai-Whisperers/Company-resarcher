# Investment Memo: {{ company.name }}

**Agent:** {{ agent_name }}
**Date:** {{ timestamp }}
**Industry:** {{ company.industry | default('N/A') }}
**Country:** {{ company.country | default('Global') }}

---

## Executive Summary

{% if executive_summary %}
| Attribute | Assessment |
|-----------|------------|
| **Recommendation** | {{ executive_summary.recommendation | default('N/A') }} |
| **Conviction Level** | {{ executive_summary.conviction_level | default('N/A') }} |
| **Price Target** | {{ executive_summary.price_target | default('N/A') }} |

**Investment Thesis:**
{{ executive_summary.thesis_summary | default('No thesis available.') }}
{% else %}
No executive summary available.
{% endif %}

---

{% if valuation_analysis %}
## Valuation Analysis

| Metric | Value |
|--------|-------|
| **Current Valuation** | {{ valuation_analysis.current_valuation | default('N/A') }} |
| **Valuation Method** | {{ valuation_analysis.valuation_method | default('N/A') }} |
| **P/E Ratio** | {{ valuation_analysis.pe_ratio | default('N/A') }} |
| **EV/EBITDA** | {{ valuation_analysis.ev_ebitda | default('N/A') }} |
| **Price/Sales** | {{ valuation_analysis.price_to_sales | default('N/A') }} |
| **Fair Value Estimate** | {{ valuation_analysis.fair_value_estimate | default('N/A') }} |
| **Upside/Downside** | {{ valuation_analysis.upside_downside | default('N/A') }} |
{% endif %}

---

## Growth Catalysts

{% if growth_catalysts %}
{% for catalyst in growth_catalysts %}
### {{ catalyst.catalyst }}

| Attribute | Assessment |
|-----------|------------|
| **Timeline** | {{ catalyst.timeline | default('N/A') }} |
| **Impact** | {{ catalyst.impact | default('N/A') }} |
| **Probability** | {{ catalyst.probability | default('N/A') }} |

{% endfor %}
{% else %}
No growth catalysts identified.
{% endif %}

---

## Risk Factors

{% if risk_factors %}
{% for risk in risk_factors %}
### {{ risk.risk }}

| Attribute | Assessment |
|-----------|------------|
| **Severity** | {{ risk.severity | default('N/A') }} |
| **Probability** | {{ risk.probability | default('N/A') }} |
| **Mitigation** | {{ risk.mitigation | default('N/A') }} |

{% endfor %}
{% else %}
No risk factors identified.
{% endif %}

---

{% if competitive_moat %}
## Competitive Moat

| Attribute | Assessment |
|-----------|------------|
| **Moat Rating** | {{ competitive_moat.moat_rating | default('N/A') }} |
| **Sustainability** | {{ competitive_moat.sustainability | default('N/A') }} |

{% if competitive_moat.moat_sources %}
**Sources of Moat:**
{% for source in competitive_moat.moat_sources %}
- {{ source }}
{% endfor %}
{% endif %}
{% endif %}

---

{% if swot_analysis %}
## SWOT Analysis

### Strengths
{% for item in swot_analysis.strengths %}
- {{ item }}
{% endfor %}

### Weaknesses
{% for item in swot_analysis.weaknesses %}
- {{ item }}
{% endfor %}

### Opportunities
{% for item in swot_analysis.opportunities %}
- {{ item }}
{% endfor %}

### Threats
{% for item in swot_analysis.threats %}
- {{ item }}
{% endfor %}
{% endif %}

---

{% if management_assessment %}
## Management Assessment

| Attribute | Assessment |
|-----------|------------|
| **CEO Tenure** | {{ management_assessment.ceo_tenure | default('N/A') }} |
| **Track Record** | {{ management_assessment.track_record | default('N/A') }} |
| **Insider Ownership** | {{ management_assessment.insider_ownership | default('N/A') }} |
| **Capital Allocation** | {{ management_assessment.capital_allocation | default('N/A') }} |
{% endif %}

---

{% if financial_health %}
## Financial Health

| Metric | Assessment |
|--------|------------|
| **Balance Sheet Strength** | {{ financial_health.balance_sheet_strength | default('N/A') }} |
| **Debt/Equity** | {{ financial_health.debt_to_equity | default('N/A') }} |
| **Interest Coverage** | {{ financial_health.interest_coverage | default('N/A') }} |
| **Free Cash Flow** | {{ financial_health.free_cash_flow | default('N/A') }} |
| **Dividend Policy** | {{ financial_health.dividend_policy | default('N/A') }} |
{% endif %}

---

{% if institutional_ownership %}
## Institutional Ownership

| Attribute | Details |
|-----------|---------|
| **Total Institutional** | {{ institutional_ownership.total_institutional | default('N/A') }} |
| **Recent Changes** | {{ institutional_ownership.recent_changes | default('N/A') }} |

{% if institutional_ownership.top_holders %}
**Top Holders:**
{% for holder in institutional_ownership.top_holders %}
- {{ holder }}
{% endfor %}
{% endif %}
{% endif %}

---

{% if scenario_analysis %}
## Scenario Analysis

### Bull Case
| Target | {{ scenario_analysis.bull_case.target | default('N/A') }} |
|--------|-------|
| **Assumptions** | {{ scenario_analysis.bull_case.assumptions | default('N/A') }} |

### Base Case
| Target | {{ scenario_analysis.base_case.target | default('N/A') }} |
|--------|-------|
| **Assumptions** | {{ scenario_analysis.base_case.assumptions | default('N/A') }} |

### Bear Case
| Target | {{ scenario_analysis.bear_case.target | default('N/A') }} |
|--------|-------|
| **Assumptions** | {{ scenario_analysis.bear_case.assumptions | default('N/A') }} |
{% endif %}

---

{% if key_metrics_to_watch %}
## Key Metrics to Watch

| Metric | Current Value | Target Value |
|--------|---------------|--------------|
{% for metric in key_metrics_to_watch %}
| {{ metric.metric }} | {{ metric.current_value | default('N/A') }} | {{ metric.target_value | default('N/A') }} |
{% endfor %}
{% endif %}

---

## Investment Parameters

| Parameter | Value |
|-----------|-------|
| **Investment Horizon** | {{ investment_horizon | default('N/A') }} |
| **Position Sizing** | {{ position_sizing | default('N/A') }} |

---

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
