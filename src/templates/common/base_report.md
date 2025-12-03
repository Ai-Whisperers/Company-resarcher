# {{ title }}

**Company:** {{ company_name }}
**Date:** {{ generated_at | format_date }}
**Agent:** {{ agent_name }}

---

{{ content }}

## Key Findings

{% for finding in key_findings %}

- **{{ finding.title }}**: {{ finding.description }}
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }}) - _{{ source.source_type }}_
  {% endfor %}
