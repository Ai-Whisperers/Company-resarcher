{% extends "base_report.md" %}

{% block content %}

## Key Statistics

{% for stat in statistics %}

- **{{ stat.metric }}:** {{ stat.value }} (Source: {{ stat.source }})
  {% endfor %}

## Financial Overview

{{ financial_overview }}

## Market Data

{{ market_data }}
{% endblock %}
