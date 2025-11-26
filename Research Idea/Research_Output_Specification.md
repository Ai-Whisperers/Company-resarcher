# Complete Research Output Specification

**Purpose**: Define the exact structure and content of research outputs for every company analyzed.

**Philosophy**: Every subfolder contains detailed reports with full source attribution - no claim without evidence.

---

## 📁 Output Folder Structure

```text
output/
  [Company Name]/
    00-Strategic-Context/
      01-Company-Overview.md
      02-Executive-Summary.md
      03-Key-News-Events.md
      04-Key-People.md
      _Sources.md                    # ← Sources used in this section

    01-Market-Intelligence/
      01-Market-Size-Growth.md
      02-Key-Trends.md
      03-Consumer-Behavior.md
      04-Regulatory-Landscape.md
      _Sources.md                    # ← Sources used in this section

    02-Target-Audience/
      01-ICP-Personas.md
      02-Customer-Journey.md
      03-Pain-Points-Needs.md
      _Sources.md                    # ← Sources used in this section

    03-Competitive-Landscape/
      01-Competitor-List.md
      02-Feature-Comparison.md
      03-Pricing-Analysis.md
      04-Market-Share.md
      05-SWOT-Analysis.md
      _Sources.md                    # ← Sources used in this section

    04-Brand-Strategy/
      01-Positioning.md
      02-Messaging-Framework.md
      03-Brand-Voice.md
      04-Brand-Archetype.md
      _Sources.md                    # ← Sources used in this section

    05-Marketing-Execution/
      01-Channel-Strategy.md
      02-Content-Plan.md
      03-Funnel-Architecture.md
      04-Campaign-Ideas.md
      _Sources.md                    # ← Sources used in this section

    06-Data-Room/
      01-Financials.md
      02-Statistics.md
      03-Funding-History.md
      04-Key-Metrics.md
      _Sources.md                    # ← Sources used in this section

    07-Creative-Inspiration/
      01-Visual-Style.md
      02-Ad-Examples.md
      03-Viral-Campaigns.md
      04-Content-Examples.md
      _Sources.md                    # ← Sources used in this section

    08-Sales-Intelligence/          # ← NEW: B2B Sales signals
      01-Pain-Point-Analysis.md
      02-Buying-Signals.md
      03-Decision-Makers.md
      04-Competitive-Position.md
      _Sources.md                    # ← Sources used in this section

    09-Investment-Analysis/         # ← NEW: Investment signals
      01-Growth-Signals.md
      02-Risk-Factors.md
      03-Market-Opportunity.md
      04-Valuation-Assessment.md
      _Sources.md                    # ← Sources used in this section

    99-Sources/
      Source-Log.md                  # Master index of ALL sources
      raw/
        Source-001-[Title].md
        Source-002-[Title].md
        ...
```

---

## 📄 Report File Format

Every `.md` report file follows this structure:

```markdown
# [Report Title]

## Summary

[2-3 sentence executive summary of key findings]

## Key Findings

### Finding 1: [Title]

[Detailed explanation]

**Source**: [Source-001](../99-Sources/raw/Source-001-Title.md) - [Brief description of what was extracted]

### Finding 2: [Title]

[Detailed explanation]

**Source**: [Source-003](../99-Sources/raw/Source-003-Title.md), [Source-007](../99-Sources/raw/Source-007-Title.md)

## Detailed Analysis

[In-depth analysis with subsections as needed]

## Recommendations

[Actionable insights based on the findings]

## Data Quality Notes

- **Confidence Level**: High/Medium/Low
- **Data Gaps**: [What we couldn't find]
- **Last Updated**: [Date]
```

---

## 📋 \_Sources.md Format (Per Subfolder)

Each subfolder has a `_Sources.md` file that lists ONLY the sources used in that specific section:

```markdown
# Sources for [Section Name]

This document lists all sources used in the reports within this folder.

## Source Index

| ID  | Title                        | Type         | URL         | Used In                | Key Data Extracted                |
| --- | ---------------------------- | ------------ | ----------- | ---------------------- | --------------------------------- |
| 001 | Company Website - About Page | Website      | https://... | 01-Company-Overview.md | Mission, Vision, Leadership names |
| 003 | LinkedIn Company Page        | Social Media | https://... | 04-Key-People.md       | Employee count, job titles        |
| 007 | TechCrunch Article           | News         | https://... | 03-Key-News-Events.md  | Funding announcement, quotes      |

## Detailed Source Breakdown

### Source-001: Company Website - About Page

- **URL**: https://example.com/about
- **Date Accessed**: 2025-11-26
- **Reliability**: High (Official source)
- **Data Extracted**:
  - Mission Statement: "To revolutionize..."
  - Founded: 2018
  - CEO: John Doe
- **Used In**:
  - 01-Company-Overview.md (Mission, History)
  - 04-Key-People.md (CEO name)

### Source-003: LinkedIn Company Page

- **URL**: https://linkedin.com/company/example
- **Date Accessed**: 2025-11-26
- **Reliability**: High (Official source)
- **Data Extracted**:
  - Employee Count: 250-500
  - Top Job Titles: Software Engineer (45), Sales (30)
  - Recent Hires: 15 in last month
- **Used In**:
  - 04-Key-People.md (Headcount, org structure)
```

---

## 🗂️ 99-Sources/Source-Log.md Format (Master Index)

The master `Source-Log.md` is a complete index of ALL sources across ALL sections:

```markdown
# Master Source Log

**Company**: [Company Name]
**Research Date**: [Date]
**Total Sources**: [Count]

## Source Summary by Category

- **Official Sources** (Website, Press Releases): 15
- **Social Media**: 8
- **News Articles**: 12
- **Financial Data**: 5
- **Review Sites**: 6
- **Job Boards**: 4
- **Third-Party Reports**: 3

## Complete Source Index

| ID  | Title                      | Type     | URL         | Sections Used                  | Reliability |
| --- | -------------------------- | -------- | ----------- | ------------------------------ | ----------- |
| 001 | Company Website - About    | Website  | https://... | 00-Strategic-Context           | High        |
| 002 | Company Website - Products | Website  | https://... | 04-Brand-Strategy              | High        |
| 003 | LinkedIn Company Page      | Social   | https://... | 00-Strategic-Context, 08-Sales | High        |
| 004 | Twitter Profile            | Social   | https://... | 05-Marketing, 08-Sales         | Medium      |
| 005 | Crunchbase Profile         | Database | https://... | 06-Data-Room, 09-Investment    | High        |
| ... | ...                        | ...      | ...         | ...                            | ...         |

## Sources by Section

### 00-Strategic-Context

- Source-001, Source-003, Source-007, Source-012

### 01-Market-Intelligence

- Source-015, Source-018, Source-023, Source-029

### 02-Target-Audience

- Source-004, Source-011, Source-021, Source-033

[Continue for all sections...]

## Reliability Assessment

### High Reliability (Official/Verified)

- Source-001: Company Website
- Source-003: LinkedIn (Official)
- Source-005: Crunchbase (Verified)

### Medium Reliability (Third-Party)

- Source-004: Twitter (User-generated)
- Source-018: Industry Report (Analyst opinion)

### Low Reliability (Unverified)

- Source-033: Reddit Discussion (Anecdotal)
```

---

## 📝 99-Sources/raw/Source-XXX-[Title].md Format

Each individual source file contains the full extracted content:

```markdown
# Source-001: Company Website - About Page

## Metadata

- **URL**: https://example.com/about
- **Type**: Website
- **Date Accessed**: 2025-11-26 15:30:00
- **Reliability**: High (Official source)
- **Language**: English
- **Archive Link**: [Wayback Machine](https://web.archive.org/...)

## Content Classification

- **Primary Topic**: Company Background
- **Secondary Topics**: Leadership, Mission, History
- **Relevant Sections**: 00-Strategic-Context

## Extracted Content

### Mission Statement

"To revolutionize the way businesses analyze customer feedback through AI-powered insights."

### Company History

Founded in 2018 by Jane Smith and John Doe in San Francisco, California.

### Leadership Team

- **CEO**: John Doe (Former VP at TechCorp)
- **CTO**: Jane Smith (PhD in AI from Stanford)
- **CFO**: Mike Johnson (Ex-Goldman Sachs)

### Key Facts

- Headquarters: San Francisco, CA
- Founded: 2018
- Employees: 250+ (as of website)
- Industries Served: SaaS, E-commerce, Retail

## Data Extraction Summary

| Data Point     | Value                 | Confidence | Notes                  |
| -------------- | --------------------- | ---------- | ---------------------- |
| Mission        | "To revolutionize..." | High       | Direct quote           |
| Founded Year   | 2018                  | High       | Stated on page         |
| CEO Name       | John Doe              | High       | Listed in team section |
| Employee Count | 250+                  | Medium     | Approximate, not exact |

## Usage in Reports

- **01-Company-Overview.md**: Mission, History, Leadership
- **04-Key-People.md**: CEO background

## Quality Notes

- **Strengths**: Official source, comprehensive
- **Limitations**: Employee count is approximate, no revenue data
- **Last Updated**: Website footer shows "© 2025"
```

---

## 🎯 Content Requirements for Each Section

### 00-Strategic-Context

**01-Company-Overview.md**

- Mission & Vision statements
- Company history (founding, milestones)
- Core values
- Headquarters & office locations
- Employee count
- **Sources**: Company website, LinkedIn, Crunchbase

**02-Executive-Summary.md**

- 1-page strategic overview
- Key strengths & weaknesses
- Market position
- Growth trajectory
- **Sources**: Synthesized from all sections

**03-Key-News-Events.md**

- Last 12 months of major news
- Funding announcements
- Product launches
- Leadership changes
- **Sources**: News articles, press releases

**04-Key-People.md**

- Org chart (if available)
- C-Suite profiles (background, LinkedIn)
- Board members
- Key hires (last 6 months)
- **Sources**: LinkedIn, company website, news

### 01-Market-Intelligence

**01-Market-Size-Growth.md**

- TAM/SAM/SOM calculations
- Market growth rate (CAGR)
- Revenue projections
- **Sources**: Industry reports, analyst research

**02-Key-Trends.md**

- Top 5 industry trends
- Technology shifts
- Consumer behavior changes
- **Sources**: Industry publications, analyst reports

**03-Consumer-Behavior.md**

- How customers buy
- Decision-making process
- Buying triggers
- **Sources**: Surveys, reviews, social media

**04-Regulatory-Landscape.md**

- Current regulations
- Pending legislation
- Compliance requirements
- **Sources**: Government sites, legal databases

### 02-Target-Audience

**01-ICP-Personas.md**

- 3-5 detailed buyer personas
- Demographics, psychographics
- Pain points, goals
- **Sources**: Reviews, social media, surveys

**02-Customer-Journey.md**

- Awareness → Consideration → Decision stages
- Touchpoints at each stage
- Content needs
- **Sources**: Website analytics, customer interviews

**03-Pain-Points-Needs.md**

- Top 10 customer pain points
- Unmet needs
- Desired solutions
- **Sources**: Reviews, support tickets, social media

### 03-Competitive-Landscape

**01-Competitor-List.md**

- Top 5 direct competitors
- Top 3 indirect competitors
- Emerging threats
- **Sources**: Market research, Google search

**02-Feature-Comparison.md**

- Feature matrix (Company vs. Competitors)
- Unique features
- Feature gaps
- **Sources**: Product pages, reviews

**03-Pricing-Analysis.md**

- Pricing tiers comparison
- Pricing models
- Discounts & promotions
- **Sources**: Pricing pages, sales calls

**04-Market-Share.md**

- Estimated market share %
- Share of voice
- Growth trends
- **Sources**: Industry reports, social media metrics

**05-SWOT-Analysis.md**

- Strengths, Weaknesses, Opportunities, Threats
- Competitive advantages
- Vulnerabilities
- **Sources**: Synthesized from all competitive data

### 08-Sales-Intelligence (NEW)

**01-Pain-Point-Analysis.md**

- Social media pain signals
- Internal feedback chaos indicators
- Manual process signals
- **Pain Index Score**: 0-100
- **Sources**: Social media, job posts, reviews

**02-Buying-Signals.md**

- Budget availability indicators
- Decision-maker accessibility
- Timing triggers
- Technology adoption signals
- **Sources**: Funding news, LinkedIn, conferences

**03-Decision-Makers.md**

- CMO/CTO/CEO profiles
- Contact information
- LinkedIn activity
- Warm intro paths
- **Sources**: LinkedIn, company website

**04-Competitive-Position.md**

- Current tools they use
- Vendor satisfaction
- Switching costs
- Our competitive advantage
- **Sources**: Tech stack tools, reviews

### 09-Investment-Analysis (NEW)

**01-Growth-Signals.md**

- Talent migration (key hires)
- Tech stack expansion
- Social arbitrage opportunities
- **Sources**: LinkedIn, job posts, tech stack

**02-Risk-Factors.md**

- Sentiment divergence
- Executive churn
- Regulatory exposure
- **Sources**: Reviews, LinkedIn, news

**03-Market-Opportunity.md**

- TAM/SAM/SOM
- Growth rate vs. market
- Competitive moat assessment
- **Sources**: Industry reports, financials

**04-Valuation-Assessment.md**

- Current valuation (if known)
- Revenue multiples
- Comparable companies
- Investment attractiveness score
- **Sources**: Crunchbase, PitchBook, financials

---

## ✅ Quality Standards

Every report must meet these criteria:

1. **Source Attribution**: Every claim has a source link
2. **Data Freshness**: Sources accessed within last 30 days
3. **Confidence Levels**: Explicitly state High/Medium/Low confidence
4. **Data Gaps**: Acknowledge what we couldn't find
5. **Actionability**: Include "Recommendations" section
6. **Consistency**: Use same format across all reports

---

## 🔄 Research Workflow

1. **Wave 1: Primary Research** → Collect data from `Research_Data_Online.md`
2. **Wave 2: Secondary Analysis** → Generate insights from `Research_Data_Inferred.md`
3. **Wave 3: Report Generation** → Create all `.md` files with source attribution
4. **Wave 4: Quality Check** → Verify all sources are accessible and relevant
5. **Wave 5: Cross-Reference** → Ensure consistency across sections
