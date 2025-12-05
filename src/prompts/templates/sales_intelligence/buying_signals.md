# Buying Signals

## Strong Buying Indicators
{% for signal in strong_signals | default([]) %}
- {{ signal }}
{% else %}
- N/A
{% endfor %}

## Moderate Buying Indicators
{% for signal in moderate_signals | default([]) %}
- {{ signal }}
{% else %}
- N/A
{% endfor %}

## Timing Indicators
{{ timing_indicators | default("N/A") }}

## Budget Indicators
{{ budget_indicators | default("N/A") }}

## Recommended Actions
{{ recommended_actions | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
