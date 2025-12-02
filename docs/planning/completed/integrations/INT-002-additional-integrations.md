# INT-002: Additional Data Source Integrations

## Status: RESOLVED

## Resolved Date: 2024-12-01

## Summary

Implemented additional data source integrations for enhanced research coverage:
- Glassdoor (employee sentiment)
- LinkedIn (company profiles)
- Crunchbase (funding/startup data)

## Implementation

### Files Created

| File | Description |
|------|-------------|
| `src/tools/glassdoor_tool.py` | Glassdoor reviews and company ratings |
| `src/tools/linkedin_tool.py` | LinkedIn company profiles and employees |
| `src/tools/crunchbase_tool.py` | Crunchbase funding and investor data |

### Glassdoor Tool

**Purpose:** Employee sentiment, company culture, CEO approval ratings

**Features:**
- Company overview data (ratings, reviews count, CEO approval)
- Rating breakdowns (culture, work-life, compensation, career)
- Recent reviews retrieval
- Salary data lookup
- Research context formatting

**API Support:**
- RapidAPI Glassdoor scraper (recommended)
- Fallback placeholder for search-based retrieval

**Usage:**
```python
from src.tools.glassdoor_tool import GlassdoorTool

tool = GlassdoorTool()
data = await tool.get_company_data("Apple")
reviews = await tool.get_recent_reviews("Apple", limit=10)
formatted = tool.format_for_research(data)
```

**Environment Variables:**
```bash
GLASSDOOR_API_KEY=your-rapidapi-key
GLASSDOOR_RAPIDAPI_HOST=glassdoor-api.p.rapidapi.com
```

### LinkedIn Tool

**Purpose:** Company profiles, employee data, professional network insights

**Features:**
- Company profile retrieval (description, size, headquarters)
- Employee count history and growth metrics
- Key employee identification (C-suite, decision makers)
- Company search functionality
- Proxycurl API integration

**Usage:**
```python
from src.tools.linkedin_tool import LinkedInTool

tool = LinkedInTool()
data = await tool.get_company_profile(company_url="https://linkedin.com/company/apple")
employees = await tool.get_key_employees(company_url, role_filter="CEO")
formatted = tool.format_for_research(data)
```

**Environment Variables:**
```bash
PROXYCURL_API_KEY=your-proxycurl-key
# or
LINKEDIN_API_KEY=your-key
```

### Crunchbase Tool

**Purpose:** Startup data, funding rounds, investors, acquisitions

**Features:**
- Company profiles with funding totals
- Detailed funding round history
- Investor tracking
- Acquisition data
- Similar company discovery
- IPO/exit information

**Data Classes:**
- `CrunchbaseCompanyData`: Full company profile
- `FundingRound`: Individual funding round details
- `Investor`: Investor profiles
- `Acquisition`: M&A activity

**Usage:**
```python
from src.tools.crunchbase_tool import CrunchbaseTool

tool = CrunchbaseTool()
data = await tool.get_company_profile("stripe")
funding = await tool.get_funding_rounds("stripe")
investors = await tool.get_investors("stripe")
formatted = tool.format_for_research(data)
```

**Environment Variables:**
```bash
CRUNCHBASE_API_KEY=your-crunchbase-key
```

## Data Models

### GlassdoorCompanyData
```python
@dataclass
class GlassdoorCompanyData:
    company_name: str
    overall_rating: Optional[float]  # 1-5
    recommend_to_friend: Optional[float]  # percentage
    ceo_approval: Optional[float]  # percentage
    total_reviews: int
    culture_rating: Optional[float]
    work_life_rating: Optional[float]
    comp_benefits_rating: Optional[float]
    reviews: List[GlassdoorReview]
```

### LinkedInCompanyData
```python
@dataclass
class LinkedInCompanyData:
    company_name: str
    employee_count: Optional[int]
    employee_growth_6m: Optional[float]
    follower_count: Optional[int]
    key_employees: List[LinkedInEmployee]
    specialties: List[str]
```

### CrunchbaseCompanyData
```python
@dataclass
class CrunchbaseCompanyData:
    company_name: str
    total_funding_usd: Optional[float]
    num_funding_rounds: int
    funding_rounds: List[FundingRound]
    investors: List[Investor]
    acquisitions: List[Acquisition]
```

## Integration with Research Pipeline

These tools can be integrated with specialist agents:

```python
from src.tools.glassdoor_tool import GlassdoorTool
from src.tools.linkedin_tool import LinkedInTool
from src.tools.crunchbase_tool import CrunchbaseTool

# In agent initialization
self.glassdoor = GlassdoorTool()
self.linkedin = LinkedInTool()
self.crunchbase = CrunchbaseTool()

# In research method
glassdoor_data = await self.glassdoor.get_company_data(company_name)
linkedin_data = await self.linkedin.get_company_profile(company_name=company_name)
crunchbase_data = await self.crunchbase.get_company_profile(company_name.lower())

extra_context = {
    "glassdoor": self.glassdoor.format_for_research(glassdoor_data),
    "linkedin": self.linkedin.format_for_research(linkedin_data),
    "crunchbase": self.crunchbase.format_for_research(crunchbase_data),
}
```

## Verification

```bash
# Verify imports
python -c "from src.tools.glassdoor_tool import GlassdoorTool; print('Glassdoor OK')"
python -c "from src.tools.linkedin_tool import LinkedInTool; print('LinkedIn OK')"
python -c "from src.tools.crunchbase_tool import CrunchbaseTool; print('Crunchbase OK')"
```

## API Cost Considerations

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Glassdoor (RapidAPI) | Limited | ~$0.01/request |
| Proxycurl (LinkedIn) | 10 credits | $0.01-0.10/request |
| Crunchbase Basic | 200 requests/day | Unlimited |

## Original Backlog Items

- INT-001: Data Source Integrations (Glassdoor, LinkedIn, Crunchbase)
- FE-004: Team/Talent Phases (Glassdoor integration)
- FE-002: Financial Deep Dive (Crunchbase integration)
