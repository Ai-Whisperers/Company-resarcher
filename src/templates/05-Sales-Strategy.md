# Sales Strategy: {{ company.name }}

**Agent:** {{ agent_name }}
**Date:** {{ timestamp }}

---

## Executive Summary

{{ executive_summary }}

## Strategic Priorities

{% for priority in priorities %}

- {{ priority }}
  {% endfor %}

## Identified Pain Points

{% for point in pain_points %}

- {{ point }}
  {% endfor %}

## Recommended Solutions

{% for solution in recommended_solutions %}

### {{ solution.product }}

- **Rationale:** {{ solution.rationale }}
- **Pitch Angle:** {{ solution.pitch_angle }}
  {% endfor %}

---

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
