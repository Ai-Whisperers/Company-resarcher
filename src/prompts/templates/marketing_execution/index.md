{% extends "base_report.md" %}

{% block content %}

## Channel Strategy

{% for channel in channels %}

### {{ channel.name }}

- **Priority:** {{ channel.priority }}
- **Strategy:** {{ channel.strategy }}
  {% endfor %}

## Content Strategy

**Content Pillars:** {{ content_pillars }}
**Formats:** {{ content_formats }}

## Funnel Architecture

### Top of Funnel (Attract)

{{ funnel_top }}

### Middle of Funnel (Engage)

{{ funnel_middle }}

### Bottom of Funnel (Convert)

{{ funnel_bottom }}
{% endblock %}
