# Pain Points & Unmet Needs

**Industry:** {{ industry }}
**Date:** {{ generated_at }}

## Primary Pain Points

{% for pain in pain_points %}

### {{ pain.name }}

- **Description:** {{ pain.description }}
- **Impact:** {{ pain.impact }}
  {% else %}
- N/A
  {% endfor %}

## Unmet Needs (Gaps)

{% for need in unmet_needs %}

- {{ need }}
  {% else %}
- N/A
  {% endfor %}

## Common Complaints (from Reviews)

{% for complaint in common_complaints %}

- {{ complaint }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
