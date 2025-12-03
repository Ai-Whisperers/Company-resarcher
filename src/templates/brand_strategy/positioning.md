# Brand Positioning

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

{% if company_overview %}
## Company Overview

| Attribute | Details |
|-----------|---------|
| **Founded** | {{ company_overview.founded | default('N/A') }} |
| **Mission** | {{ company_overview.mission | default('N/A') }} |
| **Vision** | {{ company_overview.vision | default('N/A') }} |

{% if company_overview.history and company_overview.history != 'N/A' %}
### History

{{ company_overview.history }}
{% endif %}
{% endif %}

## Unique Selling Proposition (USP)

{{ usp | default('N/A') }}

## Value Proposition

{{ value_prop | default('N/A') }}

{% if brand_identity %}
## Brand Identity

| Element | Description |
|---------|-------------|
| **Tagline** | {{ brand_identity.tagline | default('N/A') }} |
| **Brand Promise** | {{ brand_identity.brand_promise | default('N/A') }} |
| **Brand Personality** | {{ brand_identity.brand_personality | default('N/A') }} |
| **Tone of Voice** | {{ brand_identity.tone_of_voice | default('N/A') }} |
{% endif %}

## Brand Archetype

**Archetype:** {{ brand_archetype | default('N/A') }}

{{ archetype_description | default('') }}

## Positioning Statement

> {{ positioning_statement | default('N/A') }}

{% if brand_strengths %}
## Brand Strengths

{% for strength in brand_strengths %}
{% if strength is mapping %}
### {{ strength.strength }}

{{ strength.description | default('') }}

{% if strength.competitive_advantage and strength.competitive_advantage != 'N/A' %}
**Competitive Advantage:** {{ strength.competitive_advantage }}
{% endif %}
{% else %}
- {{ strength }}
{% endif %}
{% endfor %}
{% endif %}

{% if brand_weaknesses %}
## Brand Challenges

{% for weakness in brand_weaknesses %}
{% if weakness is mapping %}
### {{ weakness.weakness }}

{{ weakness.description | default('') }}

{% if weakness.impact and weakness.impact != 'N/A' %}
**Impact:** {{ weakness.impact }}
{% endif %}
{% else %}
- {{ weakness }}
{% endif %}
{% endfor %}
{% endif %}

{% if brand_values %}
## Core Values

{% for value in brand_values %}
{% if value is mapping %}
### {{ value.value }}

{{ value.description | default('') }}
{% else %}
- {{ value }}
{% endif %}
{% endfor %}
{% endif %}

{% if target_audience %}
## Target Audience

| Segment | Description |
|---------|-------------|
| **Primary** | {{ target_audience.primary | default('N/A') }} |
| **Secondary** | {{ target_audience.secondary | default('N/A') }} |
| **Demographics** | {{ target_audience.demographics | default('N/A') }} |
| **Psychographics** | {{ target_audience.psychographics | default('N/A') }} |
{% endif %}

{% if marketing_campaigns %}
## Marketing Campaigns

{% for campaign in marketing_campaigns %}
{% if campaign is mapping %}
### {{ campaign.campaign }}

{{ campaign.details | default('') }}

{% if campaign.results and campaign.results != 'N/A' %}
**Results:** {{ campaign.results }}
{% endif %}
{% else %}
- {{ campaign }}
{% endif %}
{% endfor %}
{% endif %}

{% if customer_perception %}
## Customer Perception

| Metric | Value |
|--------|-------|
| **Reputation** | {{ customer_perception.reputation | default('N/A') }} |
| **Reviews Sentiment** | {{ customer_perception.reviews_sentiment | default('N/A') }} |
| **NPS Score** | {{ customer_perception.nps_score | default('N/A') }} |

{% if customer_perception.key_complaints and customer_perception.key_complaints != 'N/A' %}
**Key Complaints:** {{ customer_perception.key_complaints }}
{% endif %}
{% endif %}

{% if digital_presence %}
## Digital Presence

| Channel | Analysis |
|---------|----------|
| **Website** | {{ digital_presence.website | default('N/A') }} |
| **Social Media** | {{ digital_presence.social_media | default('N/A') }} |
| **Content Strategy** | {{ digital_presence.content_strategy | default('N/A') }} |
{% endif %}

{% if brand_evolution and brand_evolution != 'N/A' %}
## Brand Evolution

{{ brand_evolution }}
{% endif %}

{% if strategic_recommendations and strategic_recommendations != 'N/A' %}
## Strategic Recommendations

{{ strategic_recommendations }}
{% endif %}

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
