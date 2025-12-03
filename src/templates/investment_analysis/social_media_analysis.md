# Social Media Analysis: {{ company.name }}

**Agent:** {{ agent_name }}
**Date:** {{ timestamp }}
**Industry:** {{ company.industry | default('N/A') }}
**Country:** {{ company.country | default('Global') }}

---

## Executive Summary

{% if executive_summary %}
| Attribute | Assessment |
|-----------|------------|
| **Overall Presence** | {{ executive_summary.overall_presence | default('N/A') }} |
| **Primary Platforms** | {{ executive_summary.primary_platforms | join(', ') if executive_summary.primary_platforms else 'N/A' }} |

**Key Insight:** {{ executive_summary.key_insight | default('No key insight available.') }}
{% else %}
No executive summary available.
{% endif %}

---

## Platform Analysis

{% if platform_analysis %}
### LinkedIn
{% if platform_analysis.linkedin %}
| Metric | Value |
|--------|-------|
| **Followers** | {{ platform_analysis.linkedin.followers | default('N/A') }} |
| **Engagement Rate** | {{ platform_analysis.linkedin.engagement_rate | default('N/A') }} |
| **Posting Frequency** | {{ platform_analysis.linkedin.posting_frequency | default('N/A') }} |
| **Content Focus** | {{ platform_analysis.linkedin.content_focus | default('N/A') }} |

{% if platform_analysis.linkedin.notable_posts %}
**Notable Posts:** {{ platform_analysis.linkedin.notable_posts }}
{% endif %}
{% else %}
No LinkedIn data available.
{% endif %}

### Twitter/X
{% if platform_analysis.twitter_x %}
| Metric | Value |
|--------|-------|
| **Followers** | {{ platform_analysis.twitter_x.followers | default('N/A') }} |
| **Engagement Rate** | {{ platform_analysis.twitter_x.engagement_rate | default('N/A') }} |
| **Posting Frequency** | {{ platform_analysis.twitter_x.posting_frequency | default('N/A') }} |
| **Content Focus** | {{ platform_analysis.twitter_x.content_focus | default('N/A') }} |

{% if platform_analysis.twitter_x.notable_mentions %}
**Notable Mentions:** {{ platform_analysis.twitter_x.notable_mentions }}
{% endif %}
{% else %}
No Twitter/X data available.
{% endif %}

### YouTube
{% if platform_analysis.youtube %}
| Metric | Value |
|--------|-------|
| **Subscribers** | {{ platform_analysis.youtube.subscribers | default('N/A') }} |
| **Total Views** | {{ platform_analysis.youtube.total_views | default('N/A') }} |
| **Average Views** | {{ platform_analysis.youtube.avg_views | default('N/A') }} |
| **Content Types** | {{ platform_analysis.youtube.content_types | default('N/A') }} |
| **Upload Frequency** | {{ platform_analysis.youtube.upload_frequency | default('N/A') }} |
{% else %}
No YouTube data available.
{% endif %}

### Instagram
{% if platform_analysis.instagram %}
| Metric | Value |
|--------|-------|
| **Followers** | {{ platform_analysis.instagram.followers | default('N/A') }} |
| **Engagement Rate** | {{ platform_analysis.instagram.engagement_rate | default('N/A') }} |
| **Content Style** | {{ platform_analysis.instagram.content_style | default('N/A') }} |
{% else %}
No Instagram data available.
{% endif %}

### Facebook
{% if platform_analysis.facebook %}
| Metric | Value |
|--------|-------|
| **Followers** | {{ platform_analysis.facebook.followers | default('N/A') }} |
| **Engagement Level** | {{ platform_analysis.facebook.engagement_level | default('N/A') }} |
{% else %}
No Facebook data available.
{% endif %}

### TikTok
{% if platform_analysis.tiktok %}
| Metric | Value |
|--------|-------|
| **Followers** | {{ platform_analysis.tiktok.followers | default('N/A') }} |
| **Content Strategy** | {{ platform_analysis.tiktok.content_strategy | default('N/A') }} |
{% else %}
No TikTok presence detected.
{% endif %}
{% endif %}

---

{% if content_strategy %}
## Content Strategy

| Attribute | Assessment |
|-----------|------------|
| **Brand Voice** | {{ content_strategy.brand_voice | default('N/A') }} |
| **Storytelling** | {{ content_strategy.storytelling | default('N/A') }} |
| **Visual Identity** | {{ content_strategy.visual_identity | default('N/A') }} |

{% if content_strategy.primary_themes %}
**Primary Themes:**
{% for theme in content_strategy.primary_themes %}
- {{ theme }}
{% endfor %}
{% endif %}

{% if content_strategy.content_types %}
**Content Types:**
{% for type in content_strategy.content_types %}
- {{ type }}
{% endfor %}
{% endif %}
{% endif %}

---

{% if engagement_metrics %}
## Engagement Metrics

| Metric | Assessment |
|--------|------------|
| **Overall Engagement** | {{ engagement_metrics.overall_engagement | default('N/A') }} |
| **Best Performing Content** | {{ engagement_metrics.best_performing_content | default('N/A') }} |
| **Audience Sentiment** | {{ engagement_metrics.audience_sentiment | default('N/A') }} |
| **Response Rate** | {{ engagement_metrics.response_rate | default('N/A') }} |
| **Community Management** | {{ engagement_metrics.community_management | default('N/A') }} |
{% endif %}

---

{% if executive_presence %}
## Executive Presence

{% for exec in executive_presence %}
### {{ exec.name }} - {{ exec.title }}

| Attribute | Details |
|-----------|---------|
| **Platform** | {{ exec.platform | default('N/A') }} |
| **Followers** | {{ exec.followers | default('N/A') }} |
| **Thought Leadership** | {{ exec.thought_leadership | default('N/A') }} |

{% endfor %}
{% endif %}

---

{% if employer_brand %}
## Employer Brand

| Attribute | Assessment |
|-----------|------------|
| **Glassdoor Rating** | {{ employer_brand.glassdoor_rating | default('N/A') }} |
| **Employee Advocacy** | {{ employer_brand.employee_advocacy | default('N/A') }} |
| **Culture Visibility** | {{ employer_brand.culture_visibility | default('N/A') }} |
| **Recruiting Presence** | {{ employer_brand.recruiting_presence | default('N/A') }} |
{% endif %}

---

{% if sentiment_analysis %}
## Sentiment Analysis

| Attribute | Assessment |
|-----------|------------|
| **Overall Sentiment** | {{ sentiment_analysis.overall_sentiment | default('N/A') }} |
| **Sentiment Trend** | {{ sentiment_analysis.sentiment_trend | default('N/A') }} |

{% if sentiment_analysis.positive_themes %}
**What People Praise:**
{% for theme in sentiment_analysis.positive_themes %}
- {{ theme }}
{% endfor %}
{% endif %}

{% if sentiment_analysis.negative_themes %}
**Common Criticisms:**
{% for theme in sentiment_analysis.negative_themes %}
- {{ theme }}
{% endfor %}
{% endif %}
{% endif %}

---

{% if competitive_comparison %}
## Competitive Comparison

| Attribute | Assessment |
|-----------|------------|
| **vs Competitors** | {{ competitive_comparison.vs_competitors | default('N/A') }} |
| **Unique Strengths** | {{ competitive_comparison.unique_strengths | default('N/A') }} |
| **Gaps** | {{ competitive_comparison.gaps | default('N/A') }} |
{% endif %}

---

{% if recommendations %}
## Recommendations

{% for rec in recommendations %}
### {{ rec.area }} ({{ rec.priority }} Priority)

**Current State:** {{ rec.current_state | default('N/A') }}

**Recommendation:** {{ rec.recommendation | default('N/A') }}

{% endfor %}
{% endif %}

---

{% if key_metrics_summary %}
## Key Metrics Summary

| Metric | Value |
|--------|-------|
| **Total Reach** | {{ key_metrics_summary.total_reach | default('N/A') }} |
| **Est. Monthly Impressions** | {{ key_metrics_summary.estimated_monthly_impressions | default('N/A') }} |
| **Share of Voice** | {{ key_metrics_summary.share_of_voice | default('N/A') }} |
{% endif %}

---

## Sources

{% for source in sources %}
- [{{ source.title }}]({{ source.url }})
{% endfor %}
