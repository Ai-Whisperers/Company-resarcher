# Source Log

## All Sources Used

| # | Title | URL | Type | Reliability | Accessed |
|---|-------|-----|------|-------------|----------|
{% for source in sources | default([]) %}
| {{ loop.index }} | {{ source.title | default("N/A") }} | {{ source.url | default("N/A") }} | {{ source.type | default("N/A") }} | {{ source.reliability | default("N/A") }} | {{ source.accessed_at | default("N/A") }} |
{% else %}
| - | No sources logged | - | - | - | - |
{% endfor %}

## Source Statistics
- **Total Sources:** {{ total_sources | default(0) }}
- **Primary Sources:** {{ primary_sources | default(0) }}
- **Secondary Sources:** {{ secondary_sources | default(0) }}
- **Average Reliability:** {{ avg_reliability | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
