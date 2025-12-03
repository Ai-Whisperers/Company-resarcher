# Market Size & Growth

**Industry:** {{ industry }}
**Region:** {{ country }}
**Date:** {{ generated_at }}

## Market Overview

**TAM (Total Addressable Market):** {{ tam | default('N/A') }}
{% if tam_details and tam_details != 'N/A' %}
> {{ tam_details }}
{% endif %}

**SAM (Serviceable Available Market):** {{ sam | default('N/A') }}
**SOM (Serviceable Obtainable Market):** {{ som | default('N/A') }}

{% if market_value_current and market_value_current != 'N/A' %}
**Current Market Value:** {{ market_value_current }}
{% endif %}
{% if market_value_projected and market_value_projected != 'N/A' %}
**Projected Market Value:** {{ market_value_projected }}
{% endif %}

## Growth Projections

**CAGR:** {{ cagr | default('N/A') }}

### Forecast (2025-2030)

{{ forecast_summary | default('N/A') }}

{% if market_segments %}
## Market Segments

| Segment | Size | Growth |
|---------|------|--------|
{% for segment in market_segments %}
| {{ segment.segment | default('N/A') }} | {{ segment.size | default('N/A') }} | {{ segment.growth | default('N/A') }} |
{% endfor %}
{% endif %}

## Key Growth Drivers

{% for driver in growth_drivers %}
{% if driver is mapping %}
### {{ driver.driver | default('Growth Driver') }}

{{ driver.description | default('') }}

{% if driver.impact %}**Impact:** {{ driver.impact }}{% endif %}
{% else %}
- {{ driver }}
{% endif %}
{% else %}
- N/A
{% endfor %}

## Market Challenges

{% for challenge in market_challenges %}
{% if challenge is mapping %}
### {{ challenge.challenge | default('Challenge') }}

{{ challenge.description | default('') }}

{% if challenge.severity %}**Severity:** {{ challenge.severity }}{% endif %}
{% else %}
- {{ challenge }}
{% endif %}
{% else %}
- N/A
{% endfor %}

{% if market_trends %}
## Emerging Trends

{% for trend in market_trends %}
{% if trend is mapping %}
### {{ trend.trend | default('Trend') }}

{{ trend.description | default('') }}

{% if trend.relevance %}**Relevance to Company:** {{ trend.relevance }}{% endif %}
{% else %}
- {{ trend }}
{% endif %}
{% endfor %}
{% endif %}

{% if regional_insights and regional_insights != 'N/A' %}
## Regional Insights

{{ regional_insights }}
{% endif %}

{% if competitive_position and competitive_position != 'N/A' %}
## Competitive Position

{{ competitive_position }}
{% endif %}

{% if key_statistics %}
## Key Statistics

{% for stat in key_statistics %}
- {{ stat }}
{% endfor %}
{% endif %}

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
