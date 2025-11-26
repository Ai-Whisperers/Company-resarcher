# Brand Positioning

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Unique Selling Proposition (USP)

{{ usp | default('N/A') }}

## Value Proposition

{{ value_prop | default('N/A') }}

## Brand Archetype

**Archetype:** {{ brand_archetype | default('N/A') }}
**Description:** {{ archetype_description | default('N/A') }}

## Positioning Statement

> {{ positioning_statement | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
