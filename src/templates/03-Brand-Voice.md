# Brand Voice & Tone

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Voice Personality

**Primary Traits:**
{% for trait in voice_traits %}

- {{ trait }}
  {% else %}
- N/A
  {% endfor %}

## Tone Guidelines

{{ tone_guidelines | default('N/A') }}

## Do's and Don'ts

| Do  | Don't |
| :-- | :---- |

{% for rule in dos_and_donts %}
| {{ rule.do }} | {{ rule.dont }} |
{% else %}
| N/A | N/A |
{% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
