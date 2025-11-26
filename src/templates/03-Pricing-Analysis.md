# Pricing Analysis

**Industry:** {{ industry }}
**Date:** {{ generated_at }}

## Pricing Models

{% for model in pricing_models %}

### {{ model.company }}

- **Model:** {{ model.type }} (e.g., Freemium, Subscription)
- **Tiers:**
  {% for tier in model.tiers %}
  - **{{ tier.name }}:** {{ tier.price }} - {{ tier.features }}
    {% endfor %}
    {% else %}
- N/A
  {% endfor %}

## Price Comparison

{{ price_comparison_summary | default('N/A') }}

## Discounts & Offers

{% for offer in discounts %}

- {{ offer }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
