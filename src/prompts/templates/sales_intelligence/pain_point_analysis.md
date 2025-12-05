# Pain Point Analysis

## Critical Pain Points
{% for pain in critical_pain_points | default([]) %}
### {{ pain.name | default("Pain Point") }}
- **Description:** {{ pain.description | default("N/A") }}
- **Impact Level:** {{ pain.impact | default("N/A") }}
- **Affected Stakeholders:** {{ pain.stakeholders | default("N/A") }}
- **Current Solutions:** {{ pain.current_solutions | default("N/A") }}

{% else %}
No critical pain points identified.
{% endfor %}

## Secondary Pain Points
{{ secondary_pain_points | default("N/A") }}

## Pain Point to Solution Mapping
{{ solution_mapping | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
