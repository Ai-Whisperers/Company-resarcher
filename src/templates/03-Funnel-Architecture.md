# Funnel Architecture

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Top of Funnel (Awareness)

{{ tof_strategy | default('N/A') }}

## Middle of Funnel (Consideration)

{{ mof_strategy | default('N/A') }}

## Bottom of Funnel (Conversion)

{{ bof_strategy | default('N/A') }}

## Lead Magnets

{% for magnet in lead_magnets %}

- {{ magnet }}
  {% else %}
- N/A
  {% endfor %}

## Nurture Sequences

{{ nurture_sequences | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
