# Key People & Organizational Structure

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Executive Leadership Team

{% for exec in executives %}

### {{ exec.name }} - {{ exec.title }}

- **Background:** {{ exec.background | default('N/A') }}
- **LinkedIn:** {{ exec.linkedin | default('N/A') }}
  {% else %}
- N/A
  {% endfor %}

## Department Heads

{% for head in department_heads %}

- **{{ head.department }}:** {{ head.name }} ({{ head.title }})
  {% else %}
- N/A
  {% endfor %}

## Organizational Structure

{{ org_structure_summary | default('N/A') }}

## Potential Leads (Key Contacts)

{% for lead in potential_leads %}

- **{{ lead.name }}** ({{ lead.title }}) - {{ lead.department }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
