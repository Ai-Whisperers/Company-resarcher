{% extends "base_report.md" %}

{% block content %}

## Ideal Customer Profiles (ICPs)

{% for icp in icps %}

### {{ icp.name }}

- **Demographics:** {{ icp.demographics }}
- **Psychographics:** {{ icp.psychographics }}
- **Pain Points:** {{ icp.pain_points }}
- **Buying Triggers:** {{ icp.buying_triggers }}
  {% endfor %}

## Customer Journey

{{ customer_journey }}

## Digital Habits

{{ digital_habits }}
{% endblock %}
