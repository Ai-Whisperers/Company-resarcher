# Channel Strategy

**Company:** {{ company_name }}
**Date:** {{ generated_at }}

## Priority Channels

{% for channel in priority_channels %}

### {{ channel.name }}

- **Rationale:** {{ channel.rationale }}
- **Strategy:** {{ channel.strategy }}
  {% else %}
- N/A
  {% endfor %}

## Social Media Presence

{% for social in social_media %}

- **{{ social.platform }}:** {{ social.followers }} followers - {{ social.engagement }}
  {% else %}
- N/A
  {% endfor %}

## Paid Media Strategy

{{ paid_media_strategy | default('N/A') }}

## Sources

{% for source in sources %}

- [{{ source.title }}]({{ source.url }})
  {% endfor %}
