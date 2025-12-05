{% extends "base_report.md" %}

{% block content %}

## Visual References

{{ visual_style_description }}

## Ad Examples

{% for ad in ad_examples %}

### {{ ad.title }}

- **Description:** {{ ad.description }}
- **Why it works:** {{ ad.analysis }}
  {% endfor %}

## Viral Campaigns

{{ viral_campaigns }}
{% endblock %}
