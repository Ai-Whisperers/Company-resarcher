# [RESOLVED] AGENT: Social Media Agent

**Status**: RESOLVED
**Original File**: backlog/08-agents-tools.md
**Resolved Date**: 2024-12-01

## Original Issue

**Priority:** Low
**Description:** Analyze public social media footprint.

**Acceptance Criteria:**
- [x] Analyze social media presence across platforms
- [x] Analyze sentiment and engagement
- [x] Identify key decision makers

## Resolution

### Implementation

**File:** `src/agents/specialists.py`

```python
class SocialMediaAgent(BaseAgent):
    """
    Specialist agent for social media analysis.

    Analyzes public social media footprint including:
    - Brand presence and engagement metrics
    - Sentiment analysis
    - Key influencers and decision makers
    - Social media strategy assessment
    """

    def __init__(self, client: BaseAIClient = None, **kwargs):
        super().__init__(
            client=client,
            name="social_media_analyst",
            prompt_template="social_media_analysis.txt",
            **kwargs,
        )
```

### Files

- **Agent:** `src/agents/specialists.py` - `SocialMediaAgent` class
- **Prompt:** `src/prompts/social_media_analysis.txt`
- **Template:** `src/templates/07-Social-Media-Analysis.md`

### Output Structure

The agent generates reports containing:
- Executive Summary (Overall presence, Primary platforms, Key insight)
- Platform Analysis:
  - LinkedIn (followers, engagement, content focus)
  - Twitter/X (followers, engagement, mentions)
  - YouTube (subscribers, views, content types)
  - Instagram (followers, engagement, style)
  - Facebook (followers, engagement)
  - TikTok (followers, strategy)
- Content Strategy (themes, types, brand voice, visual identity)
- Engagement Metrics (sentiment, response rate, community management)
- Executive Presence (personal brands of leadership)
- Employer Brand (Glassdoor, employee advocacy)
- Competitive Comparison
- Sentiment Analysis (positive/negative themes, trend)
- Influencer Partnerships
- Crisis Management history
- Recommendations with priority levels
- Key Metrics Summary (total reach, impressions, share of voice)

### Note

This agent uses web search to gather publicly available social media data. It does not require direct API integration with social platforms.
