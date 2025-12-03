# Consumer Behavior

**Industry:** {{ industry }}
**Region:** {{ country }}
**Date:** {{ generated_at }}

## Buying Habits

{{ buying_habits_summary | default('N/A') }}

## Cultural Nuances

{% for nuance in cultural_nuances %}

- {{ nuance }}
  {% else %}
- N/A
  {% endfor %}

## Decision Making Factors

{% for factor in decision_factors %}

- **{{ factor.name }}:** {{ factor.importance }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
