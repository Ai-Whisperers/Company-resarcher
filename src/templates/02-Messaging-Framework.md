# Messaging Framework

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Core Messaging Pillars

{% for pillar in messaging_pillars %}

### {{ pillar.name }}

{{ pillar.description }}
{% else %}

- N/A
  {% endfor %}

## Taglines & Slogans

{% for tagline in taglines %}

- "{{ tagline }}"
  {% else %}
- N/A
  {% endfor %}

## Key Benefit Statements

{% for benefit in key_benefits %}

- {{ benefit }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
