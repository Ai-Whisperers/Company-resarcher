# SWOT Analysis

## Strengths
{% for item in strengths | default([]) %}
- {{ item }}
{% else %}
- N/A
{% endfor %}

## Weaknesses
{% for item in weaknesses | default([]) %}
- {{ item }}
{% else %}
- N/A
{% endfor %}

## Opportunities
{% for item in opportunities | default([]) %}
- {{ item }}
{% else %}
- N/A
{% endfor %}

## Threats
{% for item in threats | default([]) %}
- {{ item }}
{% else %}
- N/A
{% endfor %}

---
*Generated: {{ generated_at | format_date }}*
