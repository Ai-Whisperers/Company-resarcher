# Feature Comparison Matrix

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Feature Matrix

| Feature | {{ company_name }} | Competitor 1 | Competitor 2 |
| :------ | :----------------- | :----------- | :----------- |

{% for row in feature_rows %}
| {{ row.feature }} | {{ row.company_val }} | {{ row.comp1_val }} | {{ row.comp2_val }} |
{% else %}
| N/A | N/A | N/A | N/A |
{% endfor %}

## Key Differentiators

{% for diff in differentiators %}

- **{{ diff.feature }}:** {{ diff.description }}
  {% else %}
- N/A
  {% endfor %}

## Feature Gaps

{% for gap in feature_gaps %}

- {{ gap }}
  {% else %}
- N/A
  {% endfor %}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
