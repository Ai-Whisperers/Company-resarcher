# Investment Analysis Strategy: The "Company Brain" Platform

**Objective**: Build a future-proof platform that doesn't just "read news" but understands the deep structural and strategic health of a company to drive investment decisions.

**The Vision**: A "Bloomberg Terminal for Private Markets" that uses Agentic AI to uncover signals invisible to human analysts.

---

## 📊 Investment Data Taxonomy (The Tree)

Before we can analyze, we must define **what** we're collecting. This is our complete data hierarchy:

```text
📁 COMPANY INTELLIGENCE ROOT
│
├── 💰 FINANCIAL HEALTH
│   ├── Revenue Metrics
│   │   ├── Total Revenue (YoY, QoQ)
│   │   ├── Revenue by Product Line
│   │   ├── Revenue by Geography
│   │   ├── Recurring vs. One-Time
│   │   └── Customer Concentration (Top 3, Top 10)
│   ├── Profitability
│   │   ├── Gross Margin
│   │   ├── Operating Margin
│   │   ├── Net Margin
│   │   └── EBITDA
│   ├── Unit Economics
│   │   ├── Customer Acquisition Cost (CAC)
│   │   ├── Lifetime Value (LTV)
│   │   ├── LTV/CAC Ratio
│   │   └── Payback Period
│   ├── Cash Flow
│   │   ├── Operating Cash Flow
│   │   ├── Free Cash Flow
│   │   ├── Burn Rate
│   │   └── Runway (Months)
│   └── Capital Structure
│       ├── Debt (Short-term, Long-term)
│       ├── Equity Raised (Total, Last Round)
│       ├── Valuation History
│       └── Cap Table Concentration
│
├── 🌍 MARKET POSITION
│   ├── Market Size
│   │   ├── TAM (Total Addressable Market)
│   │   ├── SAM (Serviceable Available Market)
│   │   └── SOM (Serviceable Obtainable Market)
│   ├── Market Share
│   │   ├── Current Market Share (%)
│   │   ├── Market Share Trend (3Y)
│   │   └── Share of Voice (Media mentions vs. competitors)
│   ├── Competitive Landscape
│   │   ├── Direct Competitors (Top 5)
│   │   ├── Indirect Competitors
│   │   ├── Competitive Advantages (Moat)
│   │   └── Threat of New Entrants
│   ├── Growth Metrics
│   │   ├── Revenue Growth Rate (YoY)
│   │   ├── User/Customer Growth Rate
│   │   ├── Market Growth Rate
│   │   └── Growth vs. Market Average
│   └── Regulatory Environment
│       ├── Current Regulations Impacting Business
│       ├── Pending Legislation
│       ├── Compliance Status (GDPR, CCPA, etc.)
│       └── Regulatory Tailwinds/Headwinds
│
├── 🛠️ PRODUCT & TECHNOLOGY
│   ├── Product Portfolio
│   │   ├── Core Products/Services
│   │   ├── Product Roadmap (Public)
│   │   ├── Recent Launches (12 months)
│   │   └── Product-Market Fit Signals
│   ├── Technology Stack
│   │   ├── Core Technologies Used
│   │   ├── Infrastructure (Cloud, On-Prem)
│   │   ├── Third-Party Dependencies
│   │   └── Platform Risk Assessment
│   ├── Innovation Metrics
│   │   ├── R&D Spend (% of Revenue)
│   │   ├── Patents Filed/Granted
│   │   ├── Technical Publications
│   │   └── GitHub Activity (if open source)
│   ├── Technical Debt
│   │   ├── Codebase Quality (if accessible)
│   │   ├── System Downtime History
│   │   ├── Security Incidents
│   │   └── Scalability Constraints
│   └── Intellectual Property
│       ├── Patents Owned
│       ├── Trademarks
│       ├── Trade Secrets
│       └── IP Litigation History
│
├── 👥 PEOPLE & CULTURE
│   ├── Leadership Team
│   │   ├── C-Suite Profiles
│   │   │   ├── CEO Background & Track Record
│   │   │   ├── CTO/CPO Technical Credentials
│   │   │   ├── CFO Financial Expertise
│   │   │   └── Other C-Level Executives
│   │   ├── Board of Directors
│   │   │   ├── Board Member Profiles
│   │   │   ├── Board Interlocks (Other companies)
│   │   │   └── Independent vs. Insider Ratio
│   │   └── Leadership Stability
│   │       ├── Executive Tenure
│   │       ├── Recent Departures (12 months)
│   │       └── Succession Planning
│   ├── Team Composition
│   │   ├── Total Headcount
│   │   ├── Headcount by Function (Eng, Sales, etc.)
│   │   ├── Geographic Distribution
│   │   └── Hiring Velocity (Net new hires/month)
│   ├── Talent Quality
│   │   ├── Key Hires from Competitors
│   │   ├── Employee Backgrounds (LinkedIn analysis)
│   │   ├── Technical Talent Density
│   │   └── Advisor Network
│   ├── Culture & Sentiment
│   │   ├── Glassdoor Rating
│   │   ├── Employee Reviews (Sentiment analysis)
│   │   ├── Turnover Rate (Estimated)
│   │   └── Diversity Metrics (if public)
│   └── Incentive Alignment
│       ├── Employee Equity Pool (%)
│       ├── Vesting Schedules
│       ├── Executive Compensation Structure
│       └── Founder Ownership (%)
│
├── 🤝 RELATIONSHIPS & ECOSYSTEM
│   ├── Customer Base
│   │   ├── Customer Segments (B2B, B2C, Enterprise)
│   │   ├── Top Customers (if public)
│   │   ├── Customer Retention Rate
│   │   ├── Net Promoter Score (NPS)
│   │   └── Customer Sentiment (Social media analysis)
│   ├── Partnerships
│   │   ├── Strategic Partners
│   │   ├── Technology Partners
│   │   ├── Distribution Partners
│   │   └── Partnership Announcements (12 months)
│   ├── Supply Chain
│   │   ├── Key Suppliers
│   │   ├── Supplier Concentration Risk
│   │   ├── Supply Chain Disruptions (History)
│   │   └── Vertical Integration Level
│   ├── Investor Network
│   │   ├── Current Investors (VCs, Angels, Strategic)
│   │   ├── Lead Investors by Round
│   │   ├── Investor Reputation & Track Record
│   │   └── Investor Involvement (Board seats, etc.)
│   └── Ecosystem Position
│       ├── Industry Associations
│       ├── Standards Bodies Participation
│       ├── Open Source Contributions
│       └── Community Engagement
│
├── 📰 NEWS & SENTIMENT
│   ├── Media Coverage
│   │   ├── Press Mentions (Volume, Trend)
│   │   ├── Media Sentiment (Positive, Neutral, Negative)
│   │   ├── Key Journalists Covering Company
│   │   └── PR Crises (History)
│   ├── Social Media Presence
│   │   ├── Social Media Followers (Twitter, LinkedIn, etc.)
│   │   ├── Engagement Rate
│   │   ├── Social Sentiment Analysis
│   │   └── Viral Moments (Positive/Negative)
│   ├── Industry Recognition
│   │   ├── Awards & Rankings
│   │   ├── Analyst Reports (Gartner, Forrester, etc.)
│   │   └── Conference Speaking Engagements
│   └── Crisis Indicators
│       ├── Negative News Spikes
│       ├── Boycott Campaigns
│       ├── Regulatory Investigations
│       └── Whistleblower Reports
│
├── 📅 STRATEGIC ACTIVITIES
│   ├── Corporate Actions
│   │   ├── M&A Activity (Acquisitions, Divestitures)
│   │   ├── Fundraising Events
│   │   ├── IPO/SPAC Plans
│   │   └── Restructuring Announcements
│   ├── Product Launches
│   │   ├── New Product Announcements
│   │   ├── Feature Releases
│   │   ├── Beta Programs
│   │   └── Product Sunset Announcements
│   ├── Market Expansion
│   │   ├── Geographic Expansion
│   │   ├── New Market Segments
│   │   ├── Channel Expansion
│   │   └── International Hiring
│   └── Strategic Initiatives
│       ├── Digital Transformation Projects
│       ├── Sustainability Initiatives
│       ├── AI/ML Adoption
│       └── Platform Shifts
│
├── 🌐 DIGITAL FOOTPRINT & ONLINE PRESENCE
│   ├── Website Analytics
│   │   ├── Traffic Volume (Monthly visitors)
│   │   ├── Bounce Rate
│   │   ├── Geographic Distribution
│   │   └── Traffic Sources (Organic, Paid, Referral)
│   ├── SEO Performance
│   │   ├── Keyword Rankings (Top keywords)
│   │   ├── Domain Authority
│   │   ├── Backlink Profile
│   │   └── Organic Search Visibility
│   └── App Store Presence
│       ├── Downloads (Total, Monthly)
│       ├── App Store Ratings (iOS, Android)
│       ├── Review Sentiment Analysis
│       └── App Update Frequency
│
├── 🔬 RESEARCH & DEVELOPMENT
│   ├── Research Publications
│   │   ├── Academic Papers (Peer-reviewed)
│   │   ├── Whitepapers
│   │   ├── Technical Blog Posts
│   │   └── Citation Count
│   ├── Conference Presentations
│   │   ├── Speaking Engagements (Industry conferences)
│   │   ├── Thought Leadership (Keynotes, panels)
│   │   ├── Workshop Facilitation
│   │   └── Conference Sponsorships
│   ├── Experimental Projects
│   │   ├── Innovation Labs
│   │   ├── Internal Incubators
│   │   ├── Beta Programs
│   │   └── Hackathon Participation
│   └── Collaboration with Universities
│       ├── Research Partnerships
│       ├── Joint Publications
│       ├── Student Internship Programs
│       └── Sponsored Research Projects
│
├── 🌍 GEOPOLITICAL & MACRO FACTORS
│   ├── Currency Exposure
│   │   ├── Revenue by Currency
│   │   ├── Hedging Strategies
│   │   ├── FX Risk Assessment
│   │   └── Multi-Currency Operations
│   ├── Political Risk
│   │   ├── Operations in Unstable Regions
│   │   ├── Government Relationship Quality
│   │   ├── Nationalization Risk
│   │   └── Political Lobbying Activity
│   ├── Trade Dependencies
│   │   ├── Tariff Exposure
│   │   ├── Import/Export Reliance
│   │   ├── Trade War Impact
│   │   └── Supply Chain Sovereignty
│   └── Economic Sensitivity
│       ├── Recession Resistance
│       ├── Cyclical vs. Counter-Cyclical
│       ├── Interest Rate Sensitivity
│       └── Inflation Impact
│
├── 🌱 ESG (ENVIRONMENTAL, SOCIAL, GOVERNANCE)
│   ├── Environmental
│   │   ├── Carbon Footprint (Scope 1, 2, 3 emissions)
│   │   ├── Sustainability Goals (Net-zero targets)
│   │   ├── Renewable Energy Usage
│   │   ├── Waste Management Practices
│   │   └── Environmental Certifications (B Corp, etc.)
│   ├── Social
│   │   ├── Community Programs
│   │   ├── Charitable Giving (% of revenue)
│   │   ├── Employee Volunteer Programs
│   │   ├── Social Impact Initiatives
│   │   └── Stakeholder Engagement
│   ├── Diversity & Inclusion
│   │   ├── Leadership Diversity (Gender, Ethnicity)
│   │   ├── Pay Equity Analysis
│   │   ├── Inclusive Hiring Practices
│   │   ├── Employee Resource Groups
│   │   └── D&I Training Programs
│   └── Governance
│       ├── Board Independence (% independent directors)
│       ├── Shareholder Rights
│       ├── Executive Compensation Alignment
│       ├── Anti-Corruption Policies
│       └── ESG Reporting Transparency
│
└── ⚖️ LEGAL & COMPLIANCE
    ├── Litigation
    │   ├── Active Lawsuits (Plaintiff/Defendant)
    │   ├── Settled Cases (3Y history)
    │   ├── Class Action Exposure
    │   └── IP Litigation
    ├── Regulatory Compliance
    │   ├── Industry-Specific Regulations
    │   ├── Data Privacy Compliance (GDPR, CCPA)
    │   ├── Financial Regulations (SOX, etc.)
    │   └── Compliance Violations (History)
    ├── Corporate Governance
    │   ├── Board Independence
    │   ├── Audit Committee Composition
    │   ├── Ethics Policies
    │   └── Whistleblower Protections
    └── Risk Factors
        ├── Disclosed Risk Factors (from filings)
        ├── Cybersecurity Incidents
        ├── Data Breaches
        └── Fraud Allegations
```

---

## 🕸️ Inter-Company Graph Analysis

We don't analyze companies in a vacuum. We build a **Knowledge Graph** to see connections:

- **Supply Chain Risks**: "Company A relies on Supplier B. Supplier B is being sued. Short Company A."
- **Board Interlocks**: "Director X sits on the board of Company Y and Z. Is a merger likely?"
- **Cross-Sector Impacts**: "A breakthrough in Battery Tech (Sector A) makes Company B's Diesel Engines (Sector B) obsolete."

---

## 📡 Signal Detection (The Alpha)

The **Investment Agent** queries the Graph to find:

### Growth Signals 🟢

- **Talent Migration**: Hiring key engineers from competitors (e.g., "Company A just hired the Lead AI Researcher from Google").
- **Tech Stack Expansion**: Adopting enterprise-grade AI tools implies scaling operations.
- **Social Arbitrage**: Customer sentiment is rising, but stock price hasn't moved yet.

### Risk Signals 🔴

- **Sentiment Divergence**: Management claims "record satisfaction," but our `Comment-Extractor` shows a 40% spike in complaints.
- **Churn**: High turnover in key leadership roles (detected via LinkedIn/News).
- **Regulatory Exposure**: New laws in one region threatening a specific revenue stream.

---

## 🧠 The "Company Brain" (RAG Architecture)

We are building a **Knowledge Retrieval (RAG)** system where all this data lives.

- **Input**: Markdown reports + Raw Social Data + Excel Financials.
- **Storage**: Vector Database (indexed by `agentic-schemas`).
- **Output**: An interface for complex queries:
  - _"Show me all companies where the CTO left in the last 6 months AND customer sentiment is trending down."_

### 🔗 Supporting Repositories

- **[`chatbot-rag-rbac`](./repo_explanations/chatbot-rag-rbac.md)**: The secure interface for analysts.
- **[`agentic-schemas`](./repo_explanations/agentic-schemas.md)**: The "Language" ensuring data consistency.

---

## 📋 The Master Due Diligence Checklist

Before writing a check, the **Investment Agent** must answer every question in this framework.

### 💰 A. Financial Health (The Truth)

- **Revenue Quality**: Is it recurring (SaaS) or one-off? What is the concentration (do 3 clients = 80% revenue?)?
- **Unit Economics**: LTV/CAC ratio (Target > 3:1). Payback period?
- **Burn Rate & Runway**: How many months until they die?
- **Margins**: Gross vs. Net. Are they improving with scale?
- **Debt Load**: Any convertible notes or venture debt ticking?

### 🌍 B. Market Position (The Opportunity)

- **TAM/SAM/SOM**: Is the market actually big enough to support a venture return?
- **Growth Rate**: Year-over-year growth vs. competitors.
- **Moat**: Network effects? High switching costs? IP? Or just "first mover"?
- **Regulatory Tailwinds**: Is the government subsidizing this sector (e.g., Green Energy)?

### 🛠️ C. Product & Technology (The Asset)

- **Tech Debt**: Is the codebase a mess? (Source: GitHub analysis if open source).
- **Scalability**: Can it handle 10x users tomorrow?
- **Dependency Risk**: Built entirely on top of OpenAI? (Platform risk).
- **IP Ownership**: Do they actually own the code? (Check contractor agreements).

### 👥 D. Team & Culture (The Driver)

- **Founder Fit**: Do they have "Founder-Market Fit"? (e.g., A doctor building medtech).
- **Churn Rate**: Are employees leaving en masse? (Glassdoor/LinkedIn signal).
- **Incentive Alignment**: Is the Cap Table clean? Do employees have equity?
- **Integrity**: Any past lawsuits or fraud allegations against leadership?

### ⚖️ E. Legal & Compliance (The Shield)

- **Litigation**: Any active lawsuits?
- **Data Privacy**: GDPR/CCPA compliance (Critical for AI/Data companies).
- **IP Infringement**: Are they being sued for patent violation?

### 🚪 F. Exit Strategy (The Return)

- **Potential Acquirers**: Who would buy this? (Google? Salesforce? PE Firm?).
- **IPO Path**: Is the business model suitable for public markets?
- **Secondary Market**: Is there demand for shares today?
