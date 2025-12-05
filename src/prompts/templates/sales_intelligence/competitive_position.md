# Competitive Position

## Market Position
{{ market_position | default("N/A") }}

## Competitive Advantages
{% for advantage in advantages | default([]) %}
- {{ advantage }}
{% else %}
- N/A
{% endfor %}

## Competitive Disadvantages
{% for disadvantage in disadvantages | default([]) %}
- {{ disadvantage }}
{% else %}
- N/A
{% endfor %}

## Positioning Against Key Competitors

{% for competitor in competitors | default([]) %}
### vs {{ competitor.name | default("Competitor") }}
- **Key Differentiators:** {{ competitor.differentiators | default("N/A") }}
- **Win Strategy:** {{ competitor.win_strategy | default("N/A") }}
- **Risk Factors:** {{ competitor.risks | default("N/A") }}

{% else %}
No competitor positioning available.
{% endfor %}

---
*Generated: {{ generated_at | format_date }}*
