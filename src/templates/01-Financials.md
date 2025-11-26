# Financials

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Revenue & Growth

**Revenue (Latest):** {{ revenue_latest | default('N/A') }}
**Revenue Growth (YoY):** {{ revenue_growth | default('N/A') }}
**Profitability:** {{ profitability | default('N/A') }}

## Funding History

{% for round in funding_rounds %}

- **{{ round.date }}:** {{ round.amount }} ({{ round.stage }}) - Investors: {{ round.investors }}
  {% else %}
- N/A
  {% endfor %}

## Stock Performance (if public)

{{ stock_performance | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
