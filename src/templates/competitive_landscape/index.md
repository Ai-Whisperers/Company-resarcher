{% extends "base_report.md" %}

{% block content %}

## Top Competitors

{% for competitor in competitors %}

### {{ competitor.name }}

- **Overview:** {{ competitor.overview }}
- **Strengths:** {{ competitor.strengths }}
- **Weaknesses:** {{ competitor.weaknesses }}
- **Pricing:** {{ competitor.pricing }}
  {% endfor %}

## Feature Comparison

{{ feature_comparison_matrix }}

## Market Share

{{ market_share_analysis }}
{% endblock %}
