# Market Size & Growth

**Industry:** {{ industry }}
**Region:** {{ country }}
**Date:** {{ generated_at }}

## Market Overview

**TAM (Total Addressable Market):** {{ tam | default('N/A') }}
**SAM (Serviceable Available Market):** {{ sam | default('N/A') }}
**SOM (Serviceable Obtainable Market):** {{ som | default('N/A') }}

## Growth Projections

**CAGR:** {{ cagr | default('N/A') }}
**Forecast (2025-2030):** {{ forecast_summary | default('N/A') }}

### Key Growth Drivers

{% for driver in growth_drivers %}

- {{ driver }}
  {% else %}
- N/A
  {% endfor %}

### Market Challenges

{% for challenge in market_challenges %}

- {{ challenge }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
