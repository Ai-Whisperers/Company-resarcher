# Visual Style & Brand Identity

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Brand Colors

{% for color in brand_colors %}

- **{{ color.name }}:** {{ color.hex }} ({{ color.usage }})
  {% else %}
- N/A
  {% endfor %}

## Typography

{% for font in fonts %}

- **{{ font.name }}:** {{ font.usage }}
  {% else %}
- N/A
  {% endfor %}

## Imagery Style

{{ imagery_style | default('N/A') }}

## Design System Notes

{{ design_system_notes | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
