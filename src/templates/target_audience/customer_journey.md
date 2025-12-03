# Customer Journey Map

**Industry:** {{ industry }}
**Date:** {{ generated_at }}

## Journey Stages

### 1. Awareness

{{ awareness_stage | default('N/A') }}

### 2. Consideration

{{ consideration_stage | default('N/A') }}

### 3. Decision

{{ decision_stage | default('N/A') }}

### 4. Retention/Advocacy

{{ retention_stage | default('N/A') }}

## Key Touchpoints

{% for point in touchpoints %}

- {{ point }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
