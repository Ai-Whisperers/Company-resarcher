{% extends "base_report.md" %}

{% block content %}

## Market Overview

**Industry:** {{ industry }}
**Market Size:** {{ market_size }}
**Growth Rate (CAGR):** {{ growth_rate }}

## Key Trends

{% for trend in trends %}

### {{ trend.name }}

{{ trend.description }}
{% endfor %}

## Cultural Context

{{ cultural_context }}

## Regulatory Landscape

{{ regulatory_landscape }}
{% endblock %}
