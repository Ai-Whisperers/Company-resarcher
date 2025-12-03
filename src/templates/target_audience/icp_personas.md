# ICP Personas

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Ideal Customer Profiles (ICPs)

{% for icp in icps %}

### {{ icp.name }}

- **Demographics:** {{ icp.demographics | default('N/A') }}
- **Job Titles:** {{ icp.job_titles | default('N/A') }}
- **Goals:** {{ icp.goals | default('N/A') }}
- **Challenges:** {{ icp.challenges | default('N/A') }}
- **Values:** {{ icp.values | default('N/A') }}
  {% else %}
- N/A
  {% endfor %}

## Psychographics

{{ psychographics_summary | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
