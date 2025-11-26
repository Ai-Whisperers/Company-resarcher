# Content Plan

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Content Pillars

{% for pillar in content_pillars %}

### {{ pillar.name }}

{{ pillar.description }}
{% else %}

- N/A
  {% endfor %}

## Content Formats

{% for format in content_formats %}

- {{ format }}
  {% else %}
- N/A
  {% endfor %}

## Calendar Ideas / Themes

{% for idea in content_ideas %}

- {{ idea }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
