# Financials

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

{% if company_structure %}
## Company Structure

| Attribute | Details |
|-----------|---------|
| **Ownership** | {{ company_structure.ownership | default('N/A') }} |
| **Subsidiaries** | {{ company_structure.subsidiaries | default('N/A') }} |
| **Headquarters** | {{ company_structure.headquarters | default('N/A') }} |
| **Founded** | {{ company_structure.founded | default('N/A') }} |
{% endif %}

## Revenue & Growth

**Revenue (Latest):** {{ revenue_latest | default('N/A') }}
**Revenue Growth (YoY):** {{ revenue_growth | default('N/A') }}

{% if revenue_history %}
### Revenue History

| Year | Amount | Growth |
|------|--------|--------|
{% for year_data in revenue_history %}
| {{ year_data.year | default('N/A') }} | {{ year_data.amount | default('N/A') }} | {{ year_data.growth | default('N/A') }} |
{% endfor %}
{% endif %}

## Profitability

{% if profitability is mapping %}
| Metric | Value |
|--------|-------|
| **Status** | {{ profitability.status | default('N/A') }} |
| **Profit Margin** | {{ profitability.profit_margin | default('N/A') }} |
| **EBITDA** | {{ profitability.ebitda | default('N/A') }} |
| **Net Income** | {{ profitability.net_income | default('N/A') }} |
{% else %}
{{ profitability | default('N/A') }}
{% endif %}

{% if key_financial_metrics %}
## Key Financial Metrics

| Metric | Value |
|--------|-------|
| **ARPU** | {{ key_financial_metrics.arpu | default('N/A') }} |
| **Customer Acquisition Cost** | {{ key_financial_metrics.customer_acquisition_cost | default('N/A') }} |
| **Lifetime Value** | {{ key_financial_metrics.lifetime_value | default('N/A') }} |
| **Churn Rate** | {{ key_financial_metrics.churn_rate | default('N/A') }} |
| **Subscriber Count** | {{ key_financial_metrics.subscriber_count | default('N/A') }} |
{% endif %}

## Funding History

{% for round in funding_rounds %}
{% if round is mapping %}
### {{ round.stage | default('Funding Round') }} - {{ round.date | default('') }}

- **Amount:** {{ round.amount | default('N/A') }}
- **Investors:** {{ round.investors | default('N/A') }}
{% if round.valuation and round.valuation != 'N/A' %}
- **Valuation:** {{ round.valuation }}
{% endif %}
{% else %}
- {{ round }}
{% endif %}
{% else %}
- N/A
{% endfor %}

## Stock Performance

{% if stock_performance is mapping %}
| Attribute | Value |
|-----------|-------|
| **Status** | {{ stock_performance.status | default('N/A') }} |
| **Ticker** | {{ stock_performance.ticker | default('N/A') }} |
| **Exchange** | {{ stock_performance.exchange | default('N/A') }} |
| **Current Price** | {{ stock_performance.current_price | default('N/A') }} |
| **Market Cap** | {{ stock_performance.market_cap | default('N/A') }} |
| **52-Week Range** | {{ stock_performance['52_week_range'] | default('N/A') }} |
| **YTD Performance** | {{ stock_performance.performance_ytd | default('N/A') }} |
{% else %}
{{ stock_performance | default('N/A') }}
{% endif %}

{% if financial_highlights %}
## Financial Highlights

{% for highlight in financial_highlights %}
{% if highlight is mapping %}
### {{ highlight.highlight }}

{{ highlight.details | default('') }}

{% if highlight.date and highlight.date != 'N/A' %}
*{{ highlight.date }}*
{% endif %}
{% else %}
- {{ highlight }}
{% endif %}
{% endfor %}
{% endif %}

{% if investments_capex and investments_capex != 'N/A' %}
## Investments & Capital Expenditures

{{ investments_capex }}
{% endif %}

{% if debt_position and debt_position != 'N/A' %}
## Debt Position

{{ debt_position }}
{% endif %}

{% if financial_outlook and financial_outlook != 'N/A' %}
## Financial Outlook

{{ financial_outlook }}
{% endif %}

{% if industry_comparison and industry_comparison != 'N/A' %}
## Industry Comparison

{{ industry_comparison }}
{% endif %}

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
