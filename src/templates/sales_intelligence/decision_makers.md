# Decision Makers

## Key Decision Makers
{% for person in decision_makers | default([]) %}
### {{ person.name | default("Name") }}
- **Title:** {{ person.title | default("N/A") }}
- **Role in Decision:** {{ person.role | default("N/A") }}
- **LinkedIn:** {{ person.linkedin | default("N/A") }}
- **Key Concerns:** {{ person.concerns | default("N/A") }}

{% else %}
No decision makers identified.
{% endfor %}

## Organizational Structure
{{ org_structure | default("N/A") }}

## Decision Making Process
{{ decision_process | default("N/A") }}

## Influencers
{{ influencers | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
