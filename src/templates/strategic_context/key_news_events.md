# Key News & Events

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Recent Press Releases (2024-2025)

{% for news in press_releases %}

### {{ news.date }} - {{ news.title }}

{{ news.summary }}
{% else %}

- No recent press releases found.
  {% endfor %}

## Mergers & Acquisitions

{% for ma in mergers_acquisitions %}

- **{{ ma.date }}:** {{ ma.details }}
  {% else %}
- No recent M&A activity found.
  {% endfor %}

## Crisis Management / Issues

{{ crisis_management | default('No significant recent crises found.') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
