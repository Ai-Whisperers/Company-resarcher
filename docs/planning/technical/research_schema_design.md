# Enhanced Research Schema Design

Based on the analysis of `temp_analysis/marketing-strategy`, this document outlines a structured approach to generating comprehensive marketing strategies for companies.

## 1. Core Philosophy

- **Evidence-Based**: Every claim must be backed by a source (URL, report, data point).
- **Structured Depth**: Moving beyond surface-level summaries to actionable, granular details (e.g., specific pain points, exact budget ranges).
- **Modular**: Each section stands alone but contributes to the holistic strategy.

## 2. Proposed Folder Structure

We will organize the output per company, with numbered subfolders for logical flow.

```
output/
  [Company Name]/
    00-Strategic-Context/
      01-Company-Overview.md        # Mission, Vision, History, Leadership
      02-Executive-Summary.md       # High-level strategic summary
      03-Key-News-Events.md         # Recent press releases, mergers, acquisitions
      04-Key-People.md              # Org chart, leadership, key contacts (Leads)

    01-Market-Intelligence/
      01-Market-Size-Growth.md      # TAM/SAM/SOM, CAGR, financial projections
      02-Key-Trends.md              # Emerging technologies, shifts in behavior
      03-Consumer-Behavior.md       # How people buy, cultural nuances
      04-Regulatory-Landscape.md    # Laws, compliance, political factors

    02-Target-Audience/
      01-ICP-Personas.md            # Detailed profiles of ideal customers
      02-Customer-Journey.md        # Awareness -> Consideration -> Decision map
      03-Pain-Points-Needs.md       # Specific problems and desired solutions

    03-Competitive-Landscape/
      01-Competitor-List.md         # Direct and indirect competitors
      02-Feature-Comparison.md      # Matrix of features vs competitors
      03-Pricing-Analysis.md        # Pricing tiers, models, and discounts
      04-Market-Share.md            # Who owns the market?

    04-Brand-Strategy/
      01-Positioning.md             # USP, Value Prop, Brand Archetype
      02-Messaging-Framework.md     # Key pillars, taglines, slogans
      03-Brand-Voice.md             # Tone, personality, do's and don'ts

    05-Marketing-Execution/
      01-Channel-Strategy.md        # Priority channels (Social, SEO, Paid)
      02-Content-Plan.md            # Content pillars, formats, calendar ideas
      03-Funnel-Architecture.md     # Lead magnets, nurture sequences

    06-Data-Room/
      01-Financials.md              # Revenue, funding, stock performance
      02-Statistics.md              # Verified hard numbers and stats

    07-Creative-Inspiration/
      01-Visual-Style.md            # Color palettes, imagery, design language
      02-Ad-Examples.md             # Screenshots/descriptions of top ads
      03-Viral-Campaigns.md         # Case studies of successful campaigns

    99-Sources/
      Source-Log.md                 # Index of all sources with links and summaries
      raw/                          # Folder containing individual source files
        Source-001-[Title].md       # Full extracted text + metadata for Source 1
        Source-002-[Title].md       # Full extracted text + metadata for Source 2
        ...
```

## 3. Detailed Input Schema (Data Points to Gather)

To generate the above structure, the agents will be tasked with finding specific "Input Data Points".

### Phase 1: Market & Brand Audit

- **Company Basics**: Name, Website, Industry, Location, Size (Employees/Revenue).
- **Current Positioning**: Tagline, Value Proposition (from website), visual style.
- **Digital Footprint**: Social media follower counts, posting frequency, engagement rates.
- **Market Data**: Global/Local market size (TAM/SAM/SOM), CAGR, key trends (last 2 years).

### Phase 2: Audience Intelligence (ICPs)

- **Demographics**: Age, Gender, Location, Job Titles, Income/Budget.
- **Psychographics**: Values, Interests, Lifestyle.
- **Pain Points**: "What keeps them up at night?", specific problems they face.
- **Buying Triggers**: Events or needs that precipitate a purchase.
- **Where They Hang Out**: Specific subreddits, LinkedIn groups, conferences, influencers they follow.

### Phase 3: Competitive Intelligence

- **Direct Competitors**: Top 3-5 companies solving the same problem.
- **Indirect Competitors**: Alternatives (e.g., "Excel spreadsheets" or "hiring an intern").
- **Pricing Models**: Tiers, free trials, enterprise pricing (if public).
- **Marketing Channels**: Where are they advertising? What content works for them?
- **Gap Analysis**: What are they missing? What do customers complain about (reviews)?

### Phase 4: Strategic Synthesis (The "Why")

- **Differentiation Angle**: "We are the X for Y" or "Unlike Z, we do A".
- **Content Pillars**: 3-5 core themes that bridge the product and the audience's interests.
- **Channel Prioritization**: Scoring channels based on Audience Match + Cost + Scalability.

## 4. Implementation Changes

To achieve this, we need to update the `Company-resarcher` codebase:

1.  **Update `RESEARCH_PHASES`**: Refine the query templates to be more specific (e.g., instead of "competitors", use "competitor name pricing page", "competitor name negative reviews").
2.  **Enhance `Orchestrator`**: Add logic to pass data between phases (e.g., use identified competitors to drive the "Competitor Deep Dive" phase).
3.  **New Templates**: Create Jinja2 templates for each of the new markdown files in the structure above.
4.  **Source Citation**: Ensure every fact in the generated markdown links back to a source in `99-Sources`.

## 5. Next Steps

1.  Approve this structure.
2.  Update `src/core/research_phases.py` with the new, granular phases.
3.  Create the Jinja2 templates in `src/templates/`.
4.  Update `src/tools/file_manager.py` to support the new folder structure.
