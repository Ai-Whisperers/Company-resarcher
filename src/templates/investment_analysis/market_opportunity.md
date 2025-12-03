# Market Opportunity

## Market Overview
{{ market_overview | default("N/A") }}

## Total Addressable Market (TAM)
{{ tam | default("N/A") }}

## Serviceable Addressable Market (SAM)
{{ sam | default("N/A") }}

## Serviceable Obtainable Market (SOM)
{{ som | default("N/A") }}

## Growth Projections
{{ growth_projections | default("N/A") }}

## Key Market Drivers
{% for driver in market_drivers | default([]) %}
- {{ driver }}
{% else %}
- N/A
{% endfor %}

## Competitive Landscape
{{ competitive_landscape | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
