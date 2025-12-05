# Brand Archetype Analysis

## Primary Archetype
{{ primary_archetype | default("N/A") }}

## Archetype Characteristics
{{ archetype_characteristics | default("N/A") }}

## Brand Personality Traits
{% for trait in personality_traits | default([]) %}
- {{ trait }}
{% else %}
- N/A
{% endfor %}

## Communication Style
{{ communication_style | default("N/A") }}

## Visual Identity Guidelines
{{ visual_identity | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
