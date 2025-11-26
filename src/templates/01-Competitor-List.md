# Competitor List

**Company:** {{ company_name }}
**Industry:** {{ industry }}
**Date:** {{ generated_at }}

## Direct Competitors

{% for competitor in direct_competitors %}

### {{ competitor.name }}

- **Website:** {{ competitor.website | default('N/A') }}
- **Description:** {{ competitor.description | default('N/A') }}
- **Key Strength:** {{ competitor.strength | default('N/A') }}
  {% else %}
- N/A
  {% endfor %}

## Indirect Competitors / Alternatives

{% for alt in indirect_competitors %}

- **{{ alt.name }}:** {{ alt.description }}
  {% else %}
- N/A
  {% endfor %}

## Emerging Threats

{% for threat in emerging_threats %}

- {{ threat }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
