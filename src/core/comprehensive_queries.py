"""
Comprehensive Query Templates - Extensive query generation for deep research.

This module provides comprehensive query templates to gather ~1000 sources
across all research sections, enabling the generation of 52+ output files.
"""

from __future__ import annotations

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class QueryTemplate:
    """A query template with metadata."""
    template: str
    section: str  # Target output section
    file: str  # Target output file
    priority: int = 1  # 1=essential, 2=important, 3=nice-to-have


# =============================================================================
# Comprehensive Query Templates by Section
# =============================================================================

# Targeting ~200 queries total (200 queries × 5 results = ~1000 sources)

COMPREHENSIVE_QUERIES: Dict[str, List[QueryTemplate]] = {
    # =========================================================================
    # 00-Strategic-Context (Company Overview, News, Key People)
    # =========================================================================
    "strategic_context": [
        # 01-Company-Overview.md
        QueryTemplate('"{company}" company overview profile', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" about us history', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" founded year history', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" headquarters location', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" mission vision values', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" company culture', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" subsidiaries divisions', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('"{company}" parent company ownership structure', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('site:linkedin.com/company "{company}"', "00-Strategic-Context", "01-Company-Overview.md"),
        QueryTemplate('site:crunchbase.com "{company}"', "00-Strategic-Context", "01-Company-Overview.md"),

        # 02-Executive-Summary.md
        QueryTemplate('"{company}" {industry} market position', "00-Strategic-Context", "02-Executive-Summary.md"),
        QueryTemplate('"{company}" strategic overview', "00-Strategic-Context", "02-Executive-Summary.md"),
        QueryTemplate('"{company}" business model', "00-Strategic-Context", "02-Executive-Summary.md"),
        QueryTemplate('"{company}" competitive advantage', "00-Strategic-Context", "02-Executive-Summary.md"),
        QueryTemplate('"{company}" growth strategy', "00-Strategic-Context", "02-Executive-Summary.md"),

        # 03-Key-News-Events.md
        QueryTemplate('"{company}" news {year}', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" press release {year}', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" announcement {year}', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" latest news', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" acquisition merger', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" partnership deal', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" expansion launch', "00-Strategic-Context", "03-Key-News-Events.md"),
        QueryTemplate('"{company}" award recognition', "00-Strategic-Context", "03-Key-News-Events.md"),

        # 04-Key-People.md
        QueryTemplate('"{company}" CEO chief executive', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('"{company}" leadership team executives', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('"{company}" management team', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('"{company}" board directors', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('"{company}" CTO CFO COO', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('"{company}" founder founders', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('site:linkedin.com "{company}" CEO', "00-Strategic-Context", "04-Key-People.md"),
        QueryTemplate('"{company}" executive biography', "00-Strategic-Context", "04-Key-People.md"),
    ],

    # =========================================================================
    # 01-Market-Intelligence (Market Size, Trends, Consumer Behavior)
    # =========================================================================
    "market_intelligence": [
        # 01-Market-Size-Growth.md
        QueryTemplate('{industry} market size {country} {year}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('{industry} market growth forecast {country}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('{industry} market revenue {country}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('{industry} TAM SAM SOM {country}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('{industry} market CAGR projection', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('{industry} market report {year}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('"{company}" market share {industry}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('{industry} market statistics {country}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('site:mordorintelligence.com {industry} {country}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),
        QueryTemplate('site:statista.com {industry} {country}', "01-Market-Intelligence", "01-Market-Size-Growth.md"),

        # 02-Key-Trends.md
        QueryTemplate('{industry} trends {year}', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} emerging trends', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} future outlook', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} technology trends', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} digital transformation', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} innovation disruption', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} market drivers challenges', "01-Market-Intelligence", "02-Key-Trends.md"),
        QueryTemplate('{industry} industry analysis {year}', "01-Market-Intelligence", "02-Key-Trends.md"),

        # 03-Consumer-Behavior.md
        QueryTemplate('{industry} consumer behavior {country}', "01-Market-Intelligence", "03-Consumer-Behavior.md"),
        QueryTemplate('{industry} customer preferences', "01-Market-Intelligence", "03-Consumer-Behavior.md"),
        QueryTemplate('{industry} buying habits {country}', "01-Market-Intelligence", "03-Consumer-Behavior.md"),
        QueryTemplate('{industry} customer demographics', "01-Market-Intelligence", "03-Consumer-Behavior.md"),
        QueryTemplate('{industry} user adoption rate', "01-Market-Intelligence", "03-Consumer-Behavior.md"),
        QueryTemplate('{industry} customer satisfaction survey', "01-Market-Intelligence", "03-Consumer-Behavior.md"),

        # 04-Regulatory-Landscape.md
        QueryTemplate('{industry} regulations {country}', "01-Market-Intelligence", "04-Regulatory-Landscape.md"),
        QueryTemplate('{industry} compliance requirements {country}', "01-Market-Intelligence", "04-Regulatory-Landscape.md"),
        QueryTemplate('{industry} legal framework {country}', "01-Market-Intelligence", "04-Regulatory-Landscape.md"),
        QueryTemplate('{industry} government policy {country}', "01-Market-Intelligence", "04-Regulatory-Landscape.md"),
        QueryTemplate('{industry} licensing requirements {country}', "01-Market-Intelligence", "04-Regulatory-Landscape.md"),
        QueryTemplate('{industry} regulatory body {country}', "01-Market-Intelligence", "04-Regulatory-Landscape.md"),
    ],

    # =========================================================================
    # 02-Target-Audience (ICP, Customer Journey, Pain Points)
    # =========================================================================
    "target_audience": [
        # 01-ICP-Personas.md
        QueryTemplate('"{company}" target customers', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('"{company}" customer segments', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('{industry} customer personas', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('{industry} ideal customer profile', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('{industry} B2B buyer persona', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('{industry} B2C customer profile', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('"{company}" enterprise customers', "02-Target-Audience", "01-ICP-Personas.md"),
        QueryTemplate('"{company}" SMB small business customers', "02-Target-Audience", "01-ICP-Personas.md"),

        # 02-Customer-Journey.md
        QueryTemplate('{industry} customer journey', "02-Target-Audience", "02-Customer-Journey.md"),
        QueryTemplate('{industry} buying process', "02-Target-Audience", "02-Customer-Journey.md"),
        QueryTemplate('{industry} purchase decision factors', "02-Target-Audience", "02-Customer-Journey.md"),
        QueryTemplate('{industry} customer touchpoints', "02-Target-Audience", "02-Customer-Journey.md"),
        QueryTemplate('{industry} customer acquisition funnel', "02-Target-Audience", "02-Customer-Journey.md"),
        QueryTemplate('"{company}" customer onboarding', "02-Target-Audience", "02-Customer-Journey.md"),

        # 03-Pain-Points-Needs.md
        QueryTemplate('{industry} customer pain points', "02-Target-Audience", "03-Pain-Points-Needs.md"),
        QueryTemplate('{industry} customer challenges problems', "02-Target-Audience", "03-Pain-Points-Needs.md"),
        QueryTemplate('{industry} customer needs requirements', "02-Target-Audience", "03-Pain-Points-Needs.md"),
        QueryTemplate('{industry} customer complaints', "02-Target-Audience", "03-Pain-Points-Needs.md"),
        QueryTemplate('"{company}" customer feedback', "02-Target-Audience", "03-Pain-Points-Needs.md"),
        QueryTemplate('{industry} common problems {country}', "02-Target-Audience", "03-Pain-Points-Needs.md"),
    ],

    # =========================================================================
    # 03-Competitive-Landscape (Competitors, Features, Pricing, SWOT)
    # =========================================================================
    "competitive_landscape": [
        # 01-Competitor-List.md
        QueryTemplate('"{company}" competitors', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('{industry} top companies {country}', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('{industry} market leaders {country}', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('{industry} major players {country}', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('"{company}" alternatives', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('{industry} competitive landscape {country}', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('site:cbinsights.com "{company}" competitors', "03-Competitive-Landscape", "01-Competitor-List.md"),
        QueryTemplate('{industry} companies list {country}', "03-Competitive-Landscape", "01-Competitor-List.md"),

        # 02-Feature-Comparison.md
        QueryTemplate('"{company}" vs competitor comparison', "03-Competitive-Landscape", "02-Feature-Comparison.md"),
        QueryTemplate('{industry} feature comparison', "03-Competitive-Landscape", "02-Feature-Comparison.md"),
        QueryTemplate('{industry} product comparison {country}', "03-Competitive-Landscape", "02-Feature-Comparison.md"),
        QueryTemplate('"{company}" product features', "03-Competitive-Landscape", "02-Feature-Comparison.md"),
        QueryTemplate('{industry} service comparison', "03-Competitive-Landscape", "02-Feature-Comparison.md"),
        QueryTemplate('"{company}" unique features', "03-Competitive-Landscape", "02-Feature-Comparison.md"),

        # 03-Pricing-Analysis.md
        QueryTemplate('"{company}" pricing plans', "03-Competitive-Landscape", "03-Pricing-Analysis.md"),
        QueryTemplate('{industry} pricing comparison {country}', "03-Competitive-Landscape", "03-Pricing-Analysis.md"),
        QueryTemplate('{industry} price benchmark', "03-Competitive-Landscape", "03-Pricing-Analysis.md"),
        QueryTemplate('"{company}" rates tariffs', "03-Competitive-Landscape", "03-Pricing-Analysis.md"),
        QueryTemplate('{industry} cost analysis', "03-Competitive-Landscape", "03-Pricing-Analysis.md"),
        QueryTemplate('"{company}" pricing strategy', "03-Competitive-Landscape", "03-Pricing-Analysis.md"),

        # 04-Market-Share.md
        QueryTemplate('{industry} market share {country} {year}', "03-Competitive-Landscape", "04-Market-Share.md"),
        QueryTemplate('"{company}" market share', "03-Competitive-Landscape", "04-Market-Share.md"),
        QueryTemplate('{industry} market share distribution', "03-Competitive-Landscape", "04-Market-Share.md"),
        QueryTemplate('{industry} market concentration', "03-Competitive-Landscape", "04-Market-Share.md"),
        QueryTemplate('{industry} subscriber market share {country}', "03-Competitive-Landscape", "04-Market-Share.md"),

        # 05-SWOT-Analysis.md
        QueryTemplate('"{company}" SWOT analysis', "03-Competitive-Landscape", "05-SWOT-Analysis.md"),
        QueryTemplate('"{company}" strengths weaknesses', "03-Competitive-Landscape", "05-SWOT-Analysis.md"),
        QueryTemplate('"{company}" opportunities threats', "03-Competitive-Landscape", "05-SWOT-Analysis.md"),
        QueryTemplate('"{company}" competitive advantage', "03-Competitive-Landscape", "05-SWOT-Analysis.md"),
        QueryTemplate('{industry} SWOT analysis {country}', "03-Competitive-Landscape", "05-SWOT-Analysis.md"),
    ],

    # =========================================================================
    # 04-Brand-Strategy (Positioning, Messaging, Voice, Archetype)
    # =========================================================================
    "brand_strategy": [
        # 01-Positioning.md
        QueryTemplate('"{company}" brand positioning', "04-Brand-Strategy", "01-Positioning.md"),
        QueryTemplate('"{company}" brand identity', "04-Brand-Strategy", "01-Positioning.md"),
        QueryTemplate('"{company}" unique selling proposition', "04-Brand-Strategy", "01-Positioning.md"),
        QueryTemplate('"{company}" brand differentiation', "04-Brand-Strategy", "01-Positioning.md"),
        QueryTemplate('"{company}" market positioning', "04-Brand-Strategy", "01-Positioning.md"),
        QueryTemplate('"{company}" brand perception', "04-Brand-Strategy", "01-Positioning.md"),

        # 02-Messaging-Framework.md
        QueryTemplate('"{company}" brand messaging', "04-Brand-Strategy", "02-Messaging-Framework.md"),
        QueryTemplate('"{company}" value proposition', "04-Brand-Strategy", "02-Messaging-Framework.md"),
        QueryTemplate('"{company}" tagline slogan', "04-Brand-Strategy", "02-Messaging-Framework.md"),
        QueryTemplate('"{company}" marketing message', "04-Brand-Strategy", "02-Messaging-Framework.md"),
        QueryTemplate('"{company}" brand story', "04-Brand-Strategy", "02-Messaging-Framework.md"),

        # 03-Brand-Voice.md
        QueryTemplate('"{company}" brand voice tone', "04-Brand-Strategy", "03-Brand-Voice.md"),
        QueryTemplate('"{company}" communication style', "04-Brand-Strategy", "03-Brand-Voice.md"),
        QueryTemplate('"{company}" social media voice', "04-Brand-Strategy", "03-Brand-Voice.md"),
        QueryTemplate('"{company}" brand personality', "04-Brand-Strategy", "03-Brand-Voice.md"),

        # 04-Brand-Archetype.md
        QueryTemplate('"{company}" brand archetype', "04-Brand-Strategy", "04-Brand-Archetype.md"),
        QueryTemplate('"{company}" brand values', "04-Brand-Strategy", "04-Brand-Archetype.md"),
        QueryTemplate('"{company}" brand character', "04-Brand-Strategy", "04-Brand-Archetype.md"),
    ],

    # =========================================================================
    # 05-Marketing-Execution (Channels, Content, Funnel, Campaigns)
    # =========================================================================
    "marketing_execution": [
        # 01-Channel-Strategy.md
        QueryTemplate('"{company}" marketing channels', "05-Marketing-Execution", "01-Channel-Strategy.md"),
        QueryTemplate('"{company}" advertising strategy', "05-Marketing-Execution", "01-Channel-Strategy.md"),
        QueryTemplate('"{company}" digital marketing', "05-Marketing-Execution", "01-Channel-Strategy.md"),
        QueryTemplate('"{company}" social media marketing', "05-Marketing-Execution", "01-Channel-Strategy.md"),
        QueryTemplate('"{company}" SEO SEM strategy', "05-Marketing-Execution", "01-Channel-Strategy.md"),
        QueryTemplate('{industry} marketing best practices', "05-Marketing-Execution", "01-Channel-Strategy.md"),

        # 02-Content-Plan.md
        QueryTemplate('"{company}" content marketing', "05-Marketing-Execution", "02-Content-Plan.md"),
        QueryTemplate('"{company}" blog content', "05-Marketing-Execution", "02-Content-Plan.md"),
        QueryTemplate('"{company}" content strategy', "05-Marketing-Execution", "02-Content-Plan.md"),
        QueryTemplate('{industry} content marketing examples', "05-Marketing-Execution", "02-Content-Plan.md"),

        # 03-Funnel-Architecture.md
        QueryTemplate('"{company}" marketing funnel', "05-Marketing-Execution", "03-Funnel-Architecture.md"),
        QueryTemplate('"{company}" lead generation', "05-Marketing-Execution", "03-Funnel-Architecture.md"),
        QueryTemplate('"{company}" conversion strategy', "05-Marketing-Execution", "03-Funnel-Architecture.md"),
        QueryTemplate('{industry} sales funnel', "05-Marketing-Execution", "03-Funnel-Architecture.md"),

        # 04-Campaign-Ideas.md
        QueryTemplate('"{company}" marketing campaign', "05-Marketing-Execution", "04-Campaign-Ideas.md"),
        QueryTemplate('"{company}" advertising campaign', "05-Marketing-Execution", "04-Campaign-Ideas.md"),
        QueryTemplate('{industry} successful campaigns', "05-Marketing-Execution", "04-Campaign-Ideas.md"),
        QueryTemplate('{industry} marketing campaign examples', "05-Marketing-Execution", "04-Campaign-Ideas.md"),
    ],

    # =========================================================================
    # 06-Data-Room (Financials, Statistics, Funding, Metrics)
    # =========================================================================
    "data_room": [
        # 01-Financials.md
        QueryTemplate('"{company}" revenue {year}', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" financial results', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" annual report', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" earnings report', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" profit loss', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" EBITDA margin', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" parent company financial report', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('"{company}" investor presentation', "06-Data-Room", "01-Financials.md"),
        QueryTemplate('site:sec.gov "{company}"', "06-Data-Room", "01-Financials.md"),

        # 02-Statistics.md
        QueryTemplate('"{company}" statistics data', "06-Data-Room", "02-Statistics.md"),
        QueryTemplate('"{company}" subscribers users', "06-Data-Room", "02-Statistics.md"),
        QueryTemplate('"{company}" customer count', "06-Data-Room", "02-Statistics.md"),
        QueryTemplate('"{company}" employee count headcount', "06-Data-Room", "02-Statistics.md"),
        QueryTemplate('"{company}" market statistics', "06-Data-Room", "02-Statistics.md"),

        # 03-Funding-History.md
        QueryTemplate('"{company}" funding round investment', "06-Data-Room", "03-Funding-History.md"),
        QueryTemplate('"{company}" series A B C funding', "06-Data-Room", "03-Funding-History.md"),
        QueryTemplate('"{company}" investors venture capital', "06-Data-Room", "03-Funding-History.md"),
        QueryTemplate('"{company}" valuation', "06-Data-Room", "03-Funding-History.md"),
        QueryTemplate('site:crunchbase.com "{company}" funding', "06-Data-Room", "03-Funding-History.md"),

        # 04-Key-Metrics.md
        QueryTemplate('"{company}" ARPU average revenue', "06-Data-Room", "04-Key-Metrics.md"),
        QueryTemplate('"{company}" churn rate', "06-Data-Room", "04-Key-Metrics.md"),
        QueryTemplate('"{company}" customer acquisition cost', "06-Data-Room", "04-Key-Metrics.md"),
        QueryTemplate('"{company}" lifetime value LTV', "06-Data-Room", "04-Key-Metrics.md"),
        QueryTemplate('"{company}" KPIs metrics', "06-Data-Room", "04-Key-Metrics.md"),
        QueryTemplate('"{company}" growth rate', "06-Data-Room", "04-Key-Metrics.md"),
    ],

    # =========================================================================
    # 07-Creative-Inspiration (Visual Style, Ads, Campaigns, Content)
    # =========================================================================
    "creative_inspiration": [
        # 01-Visual-Style.md
        QueryTemplate('"{company}" logo brand design', "07-Creative-Inspiration", "01-Visual-Style.md"),
        QueryTemplate('"{company}" visual identity', "07-Creative-Inspiration", "01-Visual-Style.md"),
        QueryTemplate('"{company}" brand colors', "07-Creative-Inspiration", "01-Visual-Style.md"),
        QueryTemplate('"{company}" website design', "07-Creative-Inspiration", "01-Visual-Style.md"),
        QueryTemplate('site:brandfetch.com "{company}"', "07-Creative-Inspiration", "01-Visual-Style.md"),

        # 02-Ad-Examples.md
        QueryTemplate('"{company}" advertisement examples', "07-Creative-Inspiration", "02-Ad-Examples.md"),
        QueryTemplate('"{company}" TV commercial', "07-Creative-Inspiration", "02-Ad-Examples.md"),
        QueryTemplate('"{company}" print ad', "07-Creative-Inspiration", "02-Ad-Examples.md"),
        QueryTemplate('"{company}" digital ad', "07-Creative-Inspiration", "02-Ad-Examples.md"),
        QueryTemplate('"{company}" billboard outdoor', "07-Creative-Inspiration", "02-Ad-Examples.md"),

        # 03-Viral-Campaigns.md
        QueryTemplate('"{company}" viral campaign', "07-Creative-Inspiration", "03-Viral-Campaigns.md"),
        QueryTemplate('"{company}" successful marketing', "07-Creative-Inspiration", "03-Viral-Campaigns.md"),
        QueryTemplate('"{company}" award winning campaign', "07-Creative-Inspiration", "03-Viral-Campaigns.md"),
        QueryTemplate('{industry} viral marketing examples', "07-Creative-Inspiration", "03-Viral-Campaigns.md"),

        # 04-Content-Examples.md
        QueryTemplate('"{company}" content examples', "07-Creative-Inspiration", "04-Content-Examples.md"),
        QueryTemplate('"{company}" social media posts', "07-Creative-Inspiration", "04-Content-Examples.md"),
        QueryTemplate('"{company}" video content', "07-Creative-Inspiration", "04-Content-Examples.md"),
        QueryTemplate('"{company}" blog posts examples', "07-Creative-Inspiration", "04-Content-Examples.md"),
    ],

    # =========================================================================
    # 08-Sales-Intelligence (Pain Points, Signals, Decision Makers, Strategy)
    # =========================================================================
    "sales_intelligence": [
        # 01-Pain-Point-Analysis.md
        QueryTemplate('"{company}" customer pain points', "08-Sales-Intelligence", "01-Pain-Point-Analysis.md"),
        QueryTemplate('"{company}" service issues problems', "08-Sales-Intelligence", "01-Pain-Point-Analysis.md"),
        QueryTemplate('"{company}" customer complaints reviews', "08-Sales-Intelligence", "01-Pain-Point-Analysis.md"),
        QueryTemplate('site:trustpilot.com "{company}"', "08-Sales-Intelligence", "01-Pain-Point-Analysis.md"),
        QueryTemplate('"{company}" negative reviews', "08-Sales-Intelligence", "01-Pain-Point-Analysis.md"),

        # 02-Buying-Signals.md
        QueryTemplate('"{company}" RFP request for proposal', "08-Sales-Intelligence", "02-Buying-Signals.md"),
        QueryTemplate('"{company}" vendor selection', "08-Sales-Intelligence", "02-Buying-Signals.md"),
        QueryTemplate('"{company}" technology investment', "08-Sales-Intelligence", "02-Buying-Signals.md"),
        QueryTemplate('"{company}" digital transformation initiative', "08-Sales-Intelligence", "02-Buying-Signals.md"),
        QueryTemplate('"{company}" expansion plans', "08-Sales-Intelligence", "02-Buying-Signals.md"),

        # 03-Decision-Makers.md
        QueryTemplate('"{company}" procurement purchasing', "08-Sales-Intelligence", "03-Decision-Makers.md"),
        QueryTemplate('"{company}" IT director CIO', "08-Sales-Intelligence", "03-Decision-Makers.md"),
        QueryTemplate('"{company}" decision makers', "08-Sales-Intelligence", "03-Decision-Makers.md"),
        QueryTemplate('site:linkedin.com "{company}" director', "08-Sales-Intelligence", "03-Decision-Makers.md"),
        QueryTemplate('"{company}" organizational structure', "08-Sales-Intelligence", "03-Decision-Makers.md"),

        # 04-Competitive-Position.md
        QueryTemplate('"{company}" competitive positioning sales', "08-Sales-Intelligence", "04-Competitive-Position.md"),
        QueryTemplate('sell against "{company}"', "08-Sales-Intelligence", "04-Competitive-Position.md"),
        QueryTemplate('"{company}" weaknesses gaps', "08-Sales-Intelligence", "04-Competitive-Position.md"),
        QueryTemplate('"{company}" switching from', "08-Sales-Intelligence", "04-Competitive-Position.md"),

        # 05-Sales-Strategy.md
        QueryTemplate('"{company}" sales approach', "08-Sales-Intelligence", "05-Sales-Strategy.md"),
        QueryTemplate('"{company}" B2B sales strategy', "08-Sales-Intelligence", "05-Sales-Strategy.md"),
        QueryTemplate('"{company}" enterprise sales', "08-Sales-Intelligence", "05-Sales-Strategy.md"),
        QueryTemplate('{industry} sales best practices', "08-Sales-Intelligence", "05-Sales-Strategy.md"),
        QueryTemplate('"{company}" case study success story', "08-Sales-Intelligence", "05-Sales-Strategy.md"),
    ],

    # =========================================================================
    # 10-SEC-Filings (For US-listed companies - official regulatory filings)
    # =========================================================================
    "sec_filings": [
        # 01-Business-Overview.md (from 10-K Item 1)
        QueryTemplate('site:sec.gov "{company}" 10-K business description', "10-SEC-Filings", "01-Business-Overview.md"),
        QueryTemplate('"{company}" SEC filing business overview', "10-SEC-Filings", "01-Business-Overview.md"),
        QueryTemplate('"{company}" annual report business segments', "10-SEC-Filings", "01-Business-Overview.md"),
        QueryTemplate('"{company}" 10-K principal products services', "10-SEC-Filings", "01-Business-Overview.md"),

        # 02-Risk-Factors.md (from 10-K Item 1A)
        QueryTemplate('site:sec.gov "{company}" risk factors', "10-SEC-Filings", "02-Risk-Factors.md"),
        QueryTemplate('"{company}" 10-K risk factors', "10-SEC-Filings", "02-Risk-Factors.md"),
        QueryTemplate('"{company}" SEC filing risk disclosure', "10-SEC-Filings", "02-Risk-Factors.md"),
        QueryTemplate('"{company}" regulatory risk SEC', "10-SEC-Filings", "02-Risk-Factors.md"),

        # 03-Financial-Highlights.md (from 10-K Item 8)
        QueryTemplate('site:sec.gov "{company}" financial statements', "10-SEC-Filings", "03-Financial-Highlights.md"),
        QueryTemplate('"{company}" 10-K audited financials', "10-SEC-Filings", "03-Financial-Highlights.md"),
        QueryTemplate('"{company}" SEC filing revenue income', "10-SEC-Filings", "03-Financial-Highlights.md"),
        QueryTemplate('"{company}" annual report financial highlights', "10-SEC-Filings", "03-Financial-Highlights.md"),

        # 04-MDA-Summary.md (from 10-K Item 7 - Management Discussion & Analysis)
        QueryTemplate('site:sec.gov "{company}" MD&A', "10-SEC-Filings", "04-MDA-Summary.md"),
        QueryTemplate('"{company}" management discussion analysis', "10-SEC-Filings", "04-MDA-Summary.md"),
        QueryTemplate('"{company}" 10-K liquidity capital resources', "10-SEC-Filings", "04-MDA-Summary.md"),
        QueryTemplate('"{company}" SEC filing outlook guidance', "10-SEC-Filings", "04-MDA-Summary.md"),

        # 05-Recent-Events.md (from 8-K filings)
        QueryTemplate('site:sec.gov "{company}" 8-K', "10-SEC-Filings", "05-Recent-Events.md"),
        QueryTemplate('"{company}" 8-K material event', "10-SEC-Filings", "05-Recent-Events.md"),
        QueryTemplate('"{company}" SEC current report', "10-SEC-Filings", "05-Recent-Events.md"),
        QueryTemplate('"{company}" 8-K earnings announcement', "10-SEC-Filings", "05-Recent-Events.md"),

        # 06-Executive-Compensation.md (from DEF 14A proxy)
        QueryTemplate('site:sec.gov "{company}" proxy statement', "10-SEC-Filings", "06-Executive-Compensation.md"),
        QueryTemplate('"{company}" DEF 14A executive compensation', "10-SEC-Filings", "06-Executive-Compensation.md"),
        QueryTemplate('"{company}" proxy CEO pay', "10-SEC-Filings", "06-Executive-Compensation.md"),
        QueryTemplate('"{company}" SEC filing compensation disclosure', "10-SEC-Filings", "06-Executive-Compensation.md"),
    ],

    # =========================================================================
    # 09-Investment-Analysis (Growth, Risk, Opportunity, Valuation)
    # =========================================================================
    "investment_analysis": [
        # 01-Growth-Signals.md
        QueryTemplate('"{company}" growth indicators', "09-Investment-Analysis", "01-Growth-Signals.md"),
        QueryTemplate('"{company}" expansion growth', "09-Investment-Analysis", "01-Growth-Signals.md"),
        QueryTemplate('"{company}" hiring jobs growth', "09-Investment-Analysis", "01-Growth-Signals.md"),
        QueryTemplate('"{company}" new markets', "09-Investment-Analysis", "01-Growth-Signals.md"),
        QueryTemplate('"{company}" product launch new', "09-Investment-Analysis", "01-Growth-Signals.md"),

        # 02-Risk-Factors.md
        QueryTemplate('"{company}" risk factors', "09-Investment-Analysis", "02-Risk-Factors.md"),
        QueryTemplate('"{company}" challenges threats', "09-Investment-Analysis", "02-Risk-Factors.md"),
        QueryTemplate('"{company}" regulatory risk', "09-Investment-Analysis", "02-Risk-Factors.md"),
        QueryTemplate('{industry} industry risks {country}', "09-Investment-Analysis", "02-Risk-Factors.md"),
        QueryTemplate('"{company}" litigation legal issues', "09-Investment-Analysis", "02-Risk-Factors.md"),

        # 03-Market-Opportunity.md
        QueryTemplate('{industry} market opportunity {country}', "09-Investment-Analysis", "03-Market-Opportunity.md"),
        QueryTemplate('{industry} growth potential {country}', "09-Investment-Analysis", "03-Market-Opportunity.md"),
        QueryTemplate('{industry} untapped market', "09-Investment-Analysis", "03-Market-Opportunity.md"),
        QueryTemplate('{industry} emerging opportunities', "09-Investment-Analysis", "03-Market-Opportunity.md"),
        QueryTemplate('"{company}" growth opportunity', "09-Investment-Analysis", "03-Market-Opportunity.md"),

        # 04-Valuation-Assessment.md
        QueryTemplate('"{company}" valuation', "09-Investment-Analysis", "04-Valuation-Assessment.md"),
        QueryTemplate('"{company}" market cap', "09-Investment-Analysis", "04-Valuation-Assessment.md"),
        QueryTemplate('{industry} valuation multiples', "09-Investment-Analysis", "04-Valuation-Assessment.md"),
        QueryTemplate('"{company}" comparable companies', "09-Investment-Analysis", "04-Valuation-Assessment.md"),
        QueryTemplate('{industry} M&A transactions {country}', "09-Investment-Analysis", "04-Valuation-Assessment.md"),
    ],

    # =========================================================================
    # 11-News-Intelligence (Recent News, Sentiment, Business Signals, Crisis)
    # NOTE: This section is primarily populated by NewsAPI via NewsAggregatorTool.
    # These queries serve as supplementary web search fallbacks.
    # =========================================================================
    "news_intelligence": [
        # 01-Recent-News.md
        QueryTemplate('"{company}" news {year}', "11-News-Intelligence", "01-Recent-News.md"),
        QueryTemplate('"{company}" latest news', "11-News-Intelligence", "01-Recent-News.md"),
        QueryTemplate('"{company}" press release', "11-News-Intelligence", "01-Recent-News.md"),
        QueryTemplate('"{company}" announcement', "11-News-Intelligence", "01-Recent-News.md"),
        QueryTemplate('site:prnewswire.com "{company}"', "11-News-Intelligence", "01-Recent-News.md"),

        # 02-Sentiment-Analysis.md
        QueryTemplate('"{company}" public opinion', "11-News-Intelligence", "02-Sentiment-Analysis.md"),
        QueryTemplate('"{company}" reputation', "11-News-Intelligence", "02-Sentiment-Analysis.md"),
        QueryTemplate('"{company}" brand sentiment', "11-News-Intelligence", "02-Sentiment-Analysis.md"),

        # 03-Business-Signals.md
        QueryTemplate('"{company}" funding round {year}', "11-News-Intelligence", "03-Business-Signals.md"),
        QueryTemplate('"{company}" partnership announcement', "11-News-Intelligence", "03-Business-Signals.md"),
        QueryTemplate('"{company}" product launch {year}', "11-News-Intelligence", "03-Business-Signals.md"),
        QueryTemplate('"{company}" acquisition merger', "11-News-Intelligence", "03-Business-Signals.md"),
        QueryTemplate('"{company}" new CEO executive', "11-News-Intelligence", "03-Business-Signals.md"),

        # 04-Crisis-Indicators.md
        QueryTemplate('"{company}" controversy scandal', "11-News-Intelligence", "04-Crisis-Indicators.md"),
        QueryTemplate('"{company}" lawsuit legal', "11-News-Intelligence", "04-Crisis-Indicators.md"),
        QueryTemplate('"{company}" layoffs restructuring', "11-News-Intelligence", "04-Crisis-Indicators.md"),
        QueryTemplate('"{company}" investigation regulatory', "11-News-Intelligence", "04-Crisis-Indicators.md"),
    ],

    # =========================================================================
    # 12-Social-Intelligence (Reddit, Twitter, Brand Sentiment, Social Risks)
    # NOTE: This section is primarily populated by Reddit/Twitter APIs.
    # These queries serve as supplementary web search fallbacks.
    # =========================================================================
    "social_intelligence": [
        # 01-Reddit-Analysis.md
        QueryTemplate('site:reddit.com "{company}"', "12-Social-Intelligence", "01-Reddit-Analysis.md"),
        QueryTemplate('reddit "{company}" review', "12-Social-Intelligence", "01-Reddit-Analysis.md"),
        QueryTemplate('reddit "{company}" discussion', "12-Social-Intelligence", "01-Reddit-Analysis.md"),
        QueryTemplate('"{company}" reddit customer experience', "12-Social-Intelligence", "01-Reddit-Analysis.md"),

        # 02-Twitter-Analysis.md
        QueryTemplate('site:twitter.com "{company}"', "12-Social-Intelligence", "02-Twitter-Analysis.md"),
        QueryTemplate('twitter "{company}" mentions', "12-Social-Intelligence", "02-Twitter-Analysis.md"),
        QueryTemplate('"{company}" twitter customer service', "12-Social-Intelligence", "02-Twitter-Analysis.md"),
        QueryTemplate('"{company}" social media presence', "12-Social-Intelligence", "02-Twitter-Analysis.md"),

        # 03-Sentiment-Summary.md
        QueryTemplate('"{company}" social media sentiment', "12-Social-Intelligence", "03-Sentiment-Summary.md"),
        QueryTemplate('"{company}" brand perception social', "12-Social-Intelligence", "03-Sentiment-Summary.md"),
        QueryTemplate('"{company}" online reputation', "12-Social-Intelligence", "03-Sentiment-Summary.md"),
        QueryTemplate('"{company}" customer reviews social media', "12-Social-Intelligence", "03-Sentiment-Summary.md"),

        # 04-Social-Risks.md
        QueryTemplate('"{company}" social media controversy', "12-Social-Intelligence", "04-Social-Risks.md"),
        QueryTemplate('"{company}" viral complaint', "12-Social-Intelligence", "04-Social-Risks.md"),
        QueryTemplate('"{company}" negative social media', "12-Social-Intelligence", "04-Social-Risks.md"),
        QueryTemplate('"{company}" PR crisis social', "12-Social-Intelligence", "04-Social-Risks.md"),
    ],
}


def get_all_queries() -> List[QueryTemplate]:
    """Get all query templates across all sections."""
    all_queries = []
    for section_queries in COMPREHENSIVE_QUERIES.values():
        all_queries.extend(section_queries)
    return all_queries


def get_queries_by_section(section: str) -> List[QueryTemplate]:
    """Get query templates for a specific section."""
    return COMPREHENSIVE_QUERIES.get(section, [])


def get_queries_for_file(section: str, filename: str) -> List[QueryTemplate]:
    """Get query templates that target a specific output file."""
    section_queries = COMPREHENSIVE_QUERIES.get(section, [])
    return [q for q in section_queries if q.file == filename]


def count_queries() -> Dict[str, int]:
    """Count queries by section."""
    counts = {}
    total = 0
    for section, queries in COMPREHENSIVE_QUERIES.items():
        counts[section] = len(queries)
        total += len(queries)
    counts["TOTAL"] = total
    return counts


def format_query(
    template: QueryTemplate,
    company: str,
    industry: str,
    country: str,
    year: str = "2024",
) -> str:
    """Format a query template with actual values."""
    query = template.template.format(
        company=company,
        industry=industry,
        country=country,
        year=year,
    )
    # Clean up double spaces from empty values
    return " ".join(query.split())


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "QueryTemplate",
    "COMPREHENSIVE_QUERIES",
    "get_all_queries",
    "get_queries_by_section",
    "get_queries_for_file",
    "count_queries",
    "format_query",
]
