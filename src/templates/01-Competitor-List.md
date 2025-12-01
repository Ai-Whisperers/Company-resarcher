# Competitor List

**Company:** {{ company_name }}
**Industry:** {{ industry }}
**Date:** {{ generated_at }}

## Direct Competitors

{% for competitor in direct_competitors %}

### {{ competitor.name }}

| Attribute | Details |
|-----------|---------|
| **Website** | {{ competitor.website | default('N/A') }} |
| **Market Share** | {{ competitor.market_share | default('N/A') }} |
| **Subscribers** | {{ competitor.subscriber_count | default('N/A') }} |
| **Revenue** | {{ competitor.revenue | default('N/A') }} |
| **Threat Level** | {{ competitor.threat_level | default('N/A') }} |

**Description:** {{ competitor.description | default('N/A') }}

**Key Strength:** {{ competitor.strength | default('N/A') }}

{% if competitor.weaknesses and competitor.weaknesses != 'N/A' %}
**Weaknesses:** {{ competitor.weaknesses }}
{% endif %}

{% if competitor.products_services %}
**Products/Services:**
{% for product in competitor.products_services %}
- {{ product }}
{% endfor %}
{% endif %}

{% if competitor.recent_developments and competitor.recent_developments != 'N/A' %}
**Recent Developments:** {{ competitor.recent_developments }}
{% endif %}

---

{% else %}
- N/A
{% endfor %}

## Indirect Competitors / Alternatives

{% for alt in indirect_competitors %}
{% if alt is mapping %}

### {{ alt.name }}

**Type:** {{ alt.type | default('N/A') }}

{{ alt.description | default('') }}

{% if alt.potential_impact and alt.potential_impact != 'N/A' %}
**Potential Impact:** {{ alt.potential_impact }}
{% endif %}

{% else %}
- **{{ alt.name | default(alt) }}:** {{ alt.description | default('') }}
{% endif %}
{% else %}
- N/A
{% endfor %}

## Emerging Threats

{% for threat in emerging_threats %}
{% if threat is mapping %}

### {{ threat.threat }}

{{ threat.description | default('') }}

{% if threat.timeline and threat.timeline != 'N/A' %}
**Timeline:** {{ threat.timeline }}
{% endif %}

{% if threat.mitigation and threat.mitigation != 'N/A' %}
**Mitigation:** {{ threat.mitigation }}
{% endif %}

{% else %}
- {{ threat }}
{% endif %}
{% else %}
- N/A
{% endfor %}

{% if competitive_advantages %}
## {{ company_name }}'s Competitive Advantages

{% for advantage in competitive_advantages %}
{% if advantage is mapping %}

### {{ advantage.advantage }}

{{ advantage.description | default('') }}

{% if advantage.sustainability and advantage.sustainability != 'N/A' %}
**Sustainability:** {{ advantage.sustainability }}
{% endif %}

{% else %}
- {{ advantage }}
{% endif %}
{% endfor %}
{% endif %}

{% if market_dynamics %}
## Market Dynamics

{% if market_dynamics.market_concentration and market_dynamics.market_concentration != 'N/A' %}
**Market Concentration:** {{ market_dynamics.market_concentration }}
{% endif %}

{% if market_dynamics.price_competition and market_dynamics.price_competition != 'N/A' %}
**Price Competition:** {{ market_dynamics.price_competition }}
{% endif %}

{% if market_dynamics.differentiation_factors %}
**Key Differentiation Factors:**
{% for factor in market_dynamics.differentiation_factors %}
- {{ factor }}
{% endfor %}
{% endif %}

{% if market_dynamics.barriers_to_entry %}
**Barriers to Entry:**
{% for barrier in market_dynamics.barriers_to_entry %}
- {{ barrier }}
{% endfor %}
{% endif %}
{% endif %}

{% if competitive_positioning_summary and competitive_positioning_summary != 'N/A' %}
## Competitive Positioning Summary

{{ competitive_positioning_summary }}
{% endif %}

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
