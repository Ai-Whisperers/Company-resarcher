# FE-003: Risk Assessment Research Phases

## Priority: High
## Category: Feature Enhancement
## Status: Backlog

## Summary

Add comprehensive risk assessment phases to capture financial, operational, legal/regulatory, and reputational risks for due diligence and investment analysis.

## Current Gap

The current system captures only ~10% of useful risk intelligence:
- No financial risk indicators (concentration, debt, liquidity)
- No operational risk assessment (key person, supplier dependencies)
- No legal/regulatory risk tracking (litigation, compliance)
- No reputational risk monitoring (sentiment, PR crises)

## Proposed New Phases

### 10-Risk-Assessment/ folder

```
10-Risk-Assessment/
├── 01-Financial-Risk.md
├── 02-Operational-Risk.md
├── 03-Legal-Regulatory-Risk.md
└── 04-Reputational-Risk.md
```

### Phase Definitions

#### 01-Financial-Risk
**Description**: Concentration, debt, liquidity risks
**Query Templates**:
- `{company_name} customer concentration risk top customers`
- `{company_name} debt levels leverage ratio`
- `{company_name} liquidity cash position`
- `{company_name} revenue concentration product`
- `{company_name} geographic concentration risk`
- `{company_name} financial risk factors SEC filing`

**Min Sources**: 4
**Priority**: 33

#### 02-Operational-Risk
**Description**: Key person, supplier, technology dependencies
**Query Templates**:
- `{company_name} key man risk founder dependency`
- `{company_name} supply chain risks suppliers`
- `{company_name} technology dependency cloud provider`
- `{company_name} operational challenges disruptions`
- `{company_name} business continuity disaster recovery`
- `{company_name} single point of failure`

**Min Sources**: 3
**Priority**: 34

#### 03-Legal-Regulatory-Risk
**Description**: Litigation, compliance, violations
**Query Templates**:
- `{company_name} lawsuit litigation legal`
- `{company_name} regulatory violations fines`
- `{company_name} SEC investigation enforcement`
- `{company_name} class action settlement`
- `{company_name} compliance issues GDPR CCPA`
- `{company_name} patent infringement IP dispute`
- `{company_name} data breach security incident`

**Min Sources**: 4
**Priority**: 35

#### 04-Reputational-Risk
**Description**: Sentiment, PR crises, employee reviews
**Query Templates**:
- `{company_name} reputation crisis scandal`
- `{company_name} negative press controversy`
- `{company_name} glassdoor reviews employee sentiment`
- `{company_name} customer complaints reviews`
- `{company_name} social media backlash boycott`
- `{company_name} PR crisis management`

**Min Sources**: 4
**Priority**: 36

## Implementation Tasks

- [ ] Add phase definitions to `src/core/research_phases.py`
- [ ] Create Jinja2 templates in `src/templates/`
- [ ] Integrate Glassdoor API for employee sentiment
- [ ] Add court records/litigation database integration
- [ ] Implement sentiment analysis for news/social
- [ ] Create risk scoring algorithm
- [ ] Add unit tests for new phases
- [ ] Document risk assessment methodology

## Template Structure

```markdown
# Risk Assessment

**Company:** {{ company_name }}
**Date:** {{ generated_at }}
**Overall Risk Score:** {{ overall_risk_score }}/100

## Risk Summary

| Risk Category | Score | Level | Trend |
|---------------|-------|-------|-------|
| Financial Risk | {{ financial_score }}/25 | {{ financial_level }} | {{ financial_trend }} |
| Operational Risk | {{ operational_score }}/25 | {{ operational_level }} | {{ operational_trend }} |
| Legal/Regulatory Risk | {{ legal_score }}/25 | {{ legal_level }} | {{ legal_trend }} |
| Reputational Risk | {{ reputational_score }}/25 | {{ reputational_level }} | {{ reputational_trend }} |

## Financial Risk Analysis

### Customer Concentration
{{ customer_concentration }}

### Revenue Concentration
{{ revenue_concentration }}

### Debt & Leverage
{{ debt_analysis }}

### Liquidity Position
{{ liquidity_analysis }}

### Key Financial Risks
{% for risk in financial_risks %}
- **{{ risk.severity }}**: {{ risk.description }}
{% endfor %}

## Operational Risk Analysis

### Key Person Dependencies
{{ key_person_risk }}

### Supply Chain Risk
{{ supply_chain_risk }}

### Technology Dependencies
{{ tech_dependency_risk }}

### Business Continuity
{{ business_continuity }}

### Key Operational Risks
{% for risk in operational_risks %}
- **{{ risk.severity }}**: {{ risk.description }}
{% endfor %}

## Legal & Regulatory Risk

### Active Litigation
{{ active_litigation }}

### Regulatory Compliance Status
{{ compliance_status }}

### Past Violations/Settlements
{{ past_violations }}

### Data Privacy & Security
{{ data_privacy_status }}

### Key Legal Risks
{% for risk in legal_risks %}
- **{{ risk.severity }}**: {{ risk.description }}
{% endfor %}

## Reputational Risk

### Media Sentiment Analysis
{{ media_sentiment }}

### Employee Sentiment (Glassdoor)
- Overall Rating: {{ glassdoor_rating }}/5
- CEO Approval: {{ ceo_approval }}%
- Recommend to Friend: {{ recommend_pct }}%
- Key Themes: {{ employee_themes }}

### Customer Sentiment
{{ customer_sentiment }}

### PR Crisis History
{{ pr_crisis_history }}

### Key Reputational Risks
{% for risk in reputational_risks %}
- **{{ risk.severity }}**: {{ risk.description }}
{% endfor %}

## Risk Mitigation Recommendations

{{ mitigation_recommendations }}

## Sources
{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
```

## Risk Scoring Methodology

### Score Calculation (0-100)
- **0-25**: Low Risk (Green)
- **26-50**: Moderate Risk (Yellow)
- **51-75**: High Risk (Orange)
- **76-100**: Critical Risk (Red)

### Weighting Factors
- Financial Risk: 25%
- Operational Risk: 25%
- Legal/Regulatory Risk: 25%
- Reputational Risk: 25%

## Data Sources to Integrate

1. **Court Records** - PACER, state court databases
2. **SEC EDGAR** - Risk factors section of 10-K
3. **Glassdoor API** - Employee reviews and ratings
4. **News Sentiment** - Media monitoring with NLP
5. **Social Media** - Twitter/X, LinkedIn sentiment
6. **BBB/Consumer Reports** - Customer complaints

## Success Criteria

- Risk score calculated for 80%+ of companies
- Active litigation identified when public
- Employee sentiment captured via Glassdoor
- PR crisis history documented
- Risk mitigation recommendations provided
