# Regulatory Landscape

**Industry:** {{ industry }}
**Region:** {{ country }}
**Date:** {{ generated_at }}

## Key Regulations

{% for reg in regulations %}

### {{ reg.name }}

{{ reg.description }}
{% else %}

- N/A
  {% endfor %}

## Compliance Requirements

{% for req in compliance_requirements %}

- {{ req }}
  {% else %}
- N/A
  {% endfor %}

## Political/Legal Risks

{{ political_risks | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
