# Sources

## References
{% for source in sources | default([]) %}
{{ loop.index }}. [{{ source.title | default("Source") }}]({{ source.url | default("#") }})
   - Accessed: {{ source.accessed_at | default("N/A") }}
   - Reliability: {{ source.reliability | default("N/A") }}

{% else %}
No sources available.
{% endfor %}

---
*Generated: {{ generated_at | format_date }}*
