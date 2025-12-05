# Ad Examples

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Top Performing Ads

{% for ad in top_ads %}

### {{ ad.title }}

- **Platform:** {{ ad.platform }}
- **Format:** {{ ad.format }}
- **Key Message:** {{ ad.message }}
- **Visual Description:** {{ ad.visual_description }}
  {% else %}
- N/A
  {% endfor %}

## Creative Themes

{% for theme in creative_themes %}

- {{ theme }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
