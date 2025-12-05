# Sales Strategy: {{ company_name }}

**Agent:** {{ agent_name }}
**Date:** {{ timestamp }}

---

## Executive Summary

{{ executive_summary }}

{% if company_context %}
## Company Context

| Attribute | Details |
|-----------|---------|
| **Business Model** | {{ company_context.business_model | default('N/A') }} |
| **Technology Stack** | {{ company_context.technology_stack | default('N/A') }} |
| **Organization** | {{ company_context.organizational_structure | default('N/A') }} |

{% if company_context.current_initiatives %}
### Current Strategic Initiatives

{% for initiative in company_context.current_initiatives %}
- {{ initiative }}
{% endfor %}
{% endif %}
{% endif %}

## Strategic Priorities

{% for priority in priorities %}
{% if priority is mapping %}
### {{ priority.priority }}

{{ priority.description | default('') }}

| Timeline | Investment Level |
|----------|------------------|
| {{ priority.timeline | default('N/A') }} | {{ priority.investment_level | default('N/A') }} |
{% else %}
- {{ priority }}
{% endif %}
{% endfor %}

## Identified Pain Points

{% for point in pain_points %}
{% if point is mapping %}
### {{ point.pain_point }}

{{ point.description | default('') }}

| Business Impact | Urgency |
|-----------------|---------|
| {{ point.business_impact | default('N/A') }} | {{ point.urgency | default('N/A') }} |
{% else %}
- {{ point }}
{% endif %}
{% endfor %}

{% if decision_makers %}
## Decision Makers

| Attribute | Details |
|-----------|---------|
| **Key Titles** | {{ decision_makers.key_titles | join(', ') if decision_makers.key_titles else 'N/A' }} |
| **Buying Process** | {{ decision_makers.buying_process | default('N/A') }} |
| **Budget Cycle** | {{ decision_makers.budget_cycle | default('N/A') }} |
{% endif %}

## Recommended Solutions

{% for solution in recommended_solutions %}
### {{ solution.product }}

{% if solution.primary_pain_point and solution.primary_pain_point != 'N/A' %}
**Addresses:** {{ solution.primary_pain_point }}
{% endif %}

**Rationale:** {{ solution.rationale }}

{% if solution.value_proposition and solution.value_proposition != 'N/A' %}
**Value Proposition:** {{ solution.value_proposition }}
{% endif %}

**Pitch Angle:** {{ solution.pitch_angle }}

{% if solution.objection_handling %}
**Objection Handling:**
{% for objection in solution.objection_handling %}
- {{ objection }}
{% endfor %}
{% endif %}

{% if solution.success_metrics %}
**Success Metrics:**
{% for metric in solution.success_metrics %}
- {{ metric }}
{% endfor %}
{% endif %}

{% if solution.implementation_approach and solution.implementation_approach != 'N/A' %}
**Implementation Approach:** {{ solution.implementation_approach }}
{% endif %}

---
{% endfor %}

{% if competitive_positioning %}
## Competitive Positioning

| Attribute | Details |
|-----------|---------|
| **Current Vendors** | {{ competitive_positioning.current_vendors | default('N/A') }} |
| **Displacement Strategy** | {{ competitive_positioning.displacement_strategy | default('N/A') }} |

{% if competitive_positioning.differentiators %}
**Key Differentiators:**
{% for diff in competitive_positioning.differentiators %}
- {{ diff }}
{% endfor %}
{% endif %}
{% endif %}

{% if engagement_strategy %}
## Engagement Strategy

| Attribute | Details |
|-----------|---------|
| **Entry Point** | {{ engagement_strategy.entry_point | default('N/A') }} |
| **Expansion Opportunity** | {{ engagement_strategy.expansion_opportunity | default('N/A') }} |
| **Reference Customers** | {{ engagement_strategy.reference_customers | default('N/A') }} |
{% endif %}

{% if next_steps %}
## Next Steps

{% for step in next_steps %}
1. {{ step }}
{% endfor %}
{% endif %}

---

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
