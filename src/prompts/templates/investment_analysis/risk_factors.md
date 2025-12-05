# Risk Factors

## High Risk Factors
{% for risk in high_risks | default([]) %}
### {{ risk.name | default("Risk") }}
- **Description:** {{ risk.description | default("N/A") }}
- **Probability:** {{ risk.probability | default("N/A") }}
- **Impact:** {{ risk.impact | default("N/A") }}
- **Mitigation:** {{ risk.mitigation | default("N/A") }}

{% else %}
No high risk factors identified.
{% endfor %}

## Medium Risk Factors
{{ medium_risks | default("N/A") }}

## Low Risk Factors
{{ low_risks | default("N/A") }}

## Risk Assessment Summary
{{ risk_summary | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
