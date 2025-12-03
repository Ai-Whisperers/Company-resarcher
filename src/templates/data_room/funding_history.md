# Funding History

## Funding Rounds

{% for round in funding_rounds | default([]) %}
### {{ round.type | default("Round") }} - {{ round.date | default("N/A") }}
- **Amount:** {{ round.amount | default("N/A") }}
- **Valuation:** {{ round.valuation | default("N/A") }}
- **Lead Investor:** {{ round.lead_investor | default("N/A") }}
- **Other Investors:** {{ round.other_investors | default("N/A") }}

{% else %}
No funding history available.
{% endfor %}

## Total Funding
{{ total_funding | default("N/A") }}

## Key Investors
{{ key_investors | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
