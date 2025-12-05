{% extends "base_report.md" %}

{% block content %}

## Brand Positioning

**Statement:** {{ positioning_statement }}
**Unique Selling Proposition (USP):** {{ usp }}
**Brand Archetype:** {{ brand_archetype }}

## Messaging Framework

### Core Pillars

{% for pillar in messaging_pillars %}

- **{{ pillar.name }}:** {{ pillar.description }}
  {% endfor %}

### Tone of Voice

{{ tone_of_voice }}

## Taglines & Slogans

{{ taglines }}
{% endblock %}
