# Task: Business Registry API Integrations

## Priority: 3 (Future Enhancement)
## Effort: Medium
## Impact: +5% (company verification, ownership data)
## Status: IMPLEMENTED

---

## Current State

### What's Configured
- `OPENCORPORATES_API_KEY` - Optional (free tier works without key)
- `WHOIS_API_KEY` - Required for domain lookups

### Implementation Complete
- [x] `src/tools/opencorporates_tool.py` - Full OpenCorporatesTool with:
  - Company search by name and jurisdiction
  - Officer/director fetching
  - Filing retrieval
  - Formatted markdown output
- [x] `src/tools/whois_tool.py` - Full WhoisTool with:
  - Domain lookup and parsing
  - Age calculation
  - Ownership verification
  - Formatted markdown output
- [x] `src/core/config.py` - API keys added (INT-006, INT-007)
- [x] `src/pipeline/orchestrator.py` - `research_corporate_registry()` method
- [x] `tests/unit/test_registry_tools.py` - Comprehensive unit tests

---

## Why This Matters

### Use Cases
1. **Company Verification**: Is this a real, registered company?
2. **Ownership Structure**: Who owns the company? Parent/subsidiaries?
3. **Registration Details**: When founded, where registered, status
4. **Officer Information**: Directors, executives
5. **Domain Ownership**: Who owns the website domain?

### Value for Research
- Due diligence verification
- Corporate structure mapping
- Fraud detection
- Competitive intelligence

---

## Part A: OpenCorporates Integration

### What is OpenCorporates?
- World's largest open database of companies
- 200+ million companies from 140+ jurisdictions
- Free tier: 500 requests/month
- Paid: Starts at $99/month

### Step 1: Get API Key
1. Go to https://api.opencorporates.com/
2. Register for account
3. Get API token

### Step 2: Create OpenCorporates Tool
**File**: `src/tools/opencorporates_tool.py`

```python
"""
OpenCorporates API Tool.

Provides company registry data from jurisdictions worldwide.
https://api.opencorporates.com/documentation/API-Reference
"""

import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core.logger import setup_logger
from ..core.config import get_settings

logger = setup_logger("tools.opencorporates")


@dataclass
class CompanyRegistration:
    """Company registration data."""
    name: str
    company_number: str
    jurisdiction_code: str
    incorporation_date: Optional[str]
    dissolution_date: Optional[str]
    company_type: str
    status: str  # active, dissolved, etc.
    registered_address: Optional[str]
    opencorporates_url: str


@dataclass
class Officer:
    """Company officer/director."""
    name: str
    position: str
    start_date: Optional[str]
    end_date: Optional[str]
    nationality: Optional[str]


@dataclass
class Filing:
    """Company filing/document."""
    title: str
    date: str
    filing_type: str
    url: Optional[str]


class OpenCorporatesTool:
    """Tool for company registry data."""

    BASE_URL = "https://api.opencorporates.com/v0.4"

    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self._api_key = api_key

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key:
            return self._api_key
        key = getattr(self.settings, "OPENCORPORATES_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request."""
        params = params or {}
        if self.api_key:
            params["api_token"] = self.api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/{endpoint}",
                params=params
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"OpenCorporates error: {response.status}")
                return await response.json()

    async def search_companies(
        self,
        query: str,
        jurisdiction_code: Optional[str] = None,
        limit: int = 10
    ) -> List[CompanyRegistration]:
        """
        Search for companies by name.

        Args:
            query: Company name to search
            jurisdiction_code: e.g., "us_de" (Delaware), "py" (Paraguay)
            limit: Max results
        """
        params = {"q": query, "per_page": limit}
        if jurisdiction_code:
            params["jurisdiction_code"] = jurisdiction_code

        data = await self._request("companies/search", params)

        companies = []
        for item in data.get("results", {}).get("companies", []):
            company = item.get("company", {})
            companies.append(self._parse_company(company))

        return companies

    async def get_company(
        self,
        jurisdiction_code: str,
        company_number: str
    ) -> Optional[CompanyRegistration]:
        """Get company by jurisdiction and registration number."""
        try:
            data = await self._request(
                f"companies/{jurisdiction_code}/{company_number}"
            )
            company = data.get("results", {}).get("company", {})
            return self._parse_company(company) if company else None
        except:
            return None

    async def get_company_officers(
        self,
        jurisdiction_code: str,
        company_number: str
    ) -> List[Officer]:
        """Get company officers/directors."""
        try:
            data = await self._request(
                f"companies/{jurisdiction_code}/{company_number}/officers"
            )
            officers = []
            for item in data.get("results", {}).get("officers", []):
                officer = item.get("officer", {})
                officers.append(Officer(
                    name=officer.get("name", ""),
                    position=officer.get("position", ""),
                    start_date=officer.get("start_date"),
                    end_date=officer.get("end_date"),
                    nationality=officer.get("nationality"),
                ))
            return officers
        except:
            return []

    async def get_company_filings(
        self,
        jurisdiction_code: str,
        company_number: str
    ) -> List[Filing]:
        """Get company filings/documents."""
        try:
            data = await self._request(
                f"companies/{jurisdiction_code}/{company_number}/filings"
            )
            filings = []
            for item in data.get("results", {}).get("filings", []):
                filing = item.get("filing", {})
                filings.append(Filing(
                    title=filing.get("title", ""),
                    date=filing.get("date", ""),
                    filing_type=filing.get("filing_type", ""),
                    url=filing.get("url"),
                ))
            return filings
        except:
            return []

    async def search_in_jurisdiction(
        self,
        company_name: str,
        country: str
    ) -> List[CompanyRegistration]:
        """Search for company in likely jurisdictions based on country."""
        # Map countries to jurisdiction codes
        country_jurisdictions = {
            "Paraguay": ["py"],
            "Argentina": ["ar"],
            "United States": ["us_de", "us_ny", "us_ca"],  # Common US states
            "Brazil": ["br"],
            "Mexico": ["mx"],
        }

        jurisdictions = country_jurisdictions.get(country, [])
        all_results = []

        for jur in jurisdictions:
            results = await self.search_companies(
                company_name,
                jurisdiction_code=jur,
                limit=5
            )
            all_results.extend(results)

        return all_results

    def _parse_company(self, data: dict) -> CompanyRegistration:
        """Parse company data from API response."""
        return CompanyRegistration(
            name=data.get("name", ""),
            company_number=data.get("company_number", ""),
            jurisdiction_code=data.get("jurisdiction_code", ""),
            incorporation_date=data.get("incorporation_date"),
            dissolution_date=data.get("dissolution_date"),
            company_type=data.get("company_type", ""),
            status=data.get("current_status", "unknown"),
            registered_address=data.get("registered_address_in_full"),
            opencorporates_url=data.get("opencorporates_url", ""),
        )

    def is_available(self) -> bool:
        """Check if API is available (works without key, limited)."""
        return True  # Free tier available without key


# Jurisdiction codes reference
JURISDICTION_CODES = {
    "Paraguay": "py",
    "Argentina": "ar",
    "Brazil": "br",
    "Chile": "cl",
    "Colombia": "co",
    "Mexico": "mx",
    "Peru": "pe",
    "United States - Delaware": "us_de",
    "United States - New York": "us_ny",
    "United States - California": "us_ca",
    "United Kingdom": "gb",
    "Luxembourg": "lu",
}
```

---

## Part B: WHOIS API Integration

### What is WHOIS?
- Domain registration data
- Shows who owns a domain
- Registration/expiration dates
- Contact information (if not private)

### Step 1: Get API Key
1. Go to https://www.whoisxmlapi.com/
2. Register for free account
3. Get API key (500 free queries)

### Step 2: Create WHOIS Tool
**File**: `src/tools/whois_tool.py`

```python
"""
WHOIS API Tool.

Provides domain registration and ownership data.
https://www.whoisxmlapi.com/documentation/whois-api
"""

import aiohttp
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..core.logger import setup_logger
from ..core.config import get_settings

logger = setup_logger("tools.whois")


@dataclass
class DomainInfo:
    """Domain registration information."""
    domain_name: str
    registrar: str
    creation_date: Optional[datetime]
    expiration_date: Optional[datetime]
    updated_date: Optional[datetime]
    status: List[str]
    name_servers: List[str]
    registrant_name: Optional[str]
    registrant_organization: Optional[str]
    registrant_country: Optional[str]
    admin_email: Optional[str]
    tech_email: Optional[str]


class WhoisTool:
    """Tool for domain ownership lookup."""

    BASE_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self._api_key = api_key

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key:
            return self._api_key
        key = getattr(self.settings, "WHOIS_API_KEY", None)
        if key:
            return key.get_secret_value() if hasattr(key, "get_secret_value") else key
        return None

    async def lookup_domain(self, domain: str) -> Optional[DomainInfo]:
        """
        Look up domain registration information.

        Args:
            domain: Domain name (e.g., "claro.com.py")
        """
        if not self.api_key:
            raise ValueError("WHOIS API key not configured")

        params = {
            "apiKey": self.api_key,
            "domainName": domain,
            "outputFormat": "JSON",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.BASE_URL,
                params=params
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                return self._parse_whois(data, domain)

    async def get_domain_age(self, domain: str) -> Optional[int]:
        """Get domain age in years."""
        info = await self.lookup_domain(domain)
        if info and info.creation_date:
            age = (datetime.now() - info.creation_date).days // 365
            return age
        return None

    async def verify_domain_ownership(
        self,
        domain: str,
        expected_owner: str
    ) -> Dict[str, any]:
        """
        Verify if domain is owned by expected organization.

        Returns match confidence and details.
        """
        info = await self.lookup_domain(domain)
        if not info:
            return {"verified": False, "reason": "lookup_failed"}

        # Check registrant organization
        org = info.registrant_organization or ""
        name = info.registrant_name or ""

        expected_lower = expected_owner.lower()

        if expected_lower in org.lower() or expected_lower in name.lower():
            return {
                "verified": True,
                "matched_field": "registrant",
                "registrant": org or name,
            }

        return {
            "verified": False,
            "reason": "no_match",
            "registrant": org or name or "private",
        }

    def _parse_whois(self, data: dict, domain: str) -> Optional[DomainInfo]:
        """Parse WHOIS API response."""
        whois = data.get("WhoisRecord", {})
        if not whois:
            return None

        registrant = whois.get("registrant", {})
        admin = whois.get("administrativeContact", {})
        tech = whois.get("technicalContact", {})

        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                # Handle various date formats
                for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%d-%b-%Y"]:
                    try:
                        return datetime.strptime(date_str[:19], fmt[:len(date_str)])
                    except:
                        continue
                return None
            except:
                return None

        return DomainInfo(
            domain_name=domain,
            registrar=whois.get("registrarName", ""),
            creation_date=parse_date(whois.get("createdDate")),
            expiration_date=parse_date(whois.get("expiresDate")),
            updated_date=parse_date(whois.get("updatedDate")),
            status=whois.get("status", "").split() if whois.get("status") else [],
            name_servers=whois.get("nameServers", {}).get("hostNames", []),
            registrant_name=registrant.get("name"),
            registrant_organization=registrant.get("organization"),
            registrant_country=registrant.get("country"),
            admin_email=admin.get("email"),
            tech_email=tech.get("email"),
        )

    def is_available(self) -> bool:
        """Check if API is configured."""
        return bool(self.api_key)
```

---

## Output Structure

```
outputs/Company_Name/
├── corporate_registry/
│   ├── 01-Registration-Details.md  # OpenCorporates data
│   ├── 02-Officers-Directors.md    # Company officers
│   ├── 03-Domain-Ownership.md      # WHOIS data
│   └── 04-Corporate-Structure.md   # Parent/subsidiary mapping
```

---

## Pipeline Integration

```python
async def _research_corporate_registry(
    self,
    company_name: str,
    country: str,
    website: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Research corporate registration and domain ownership."""
    results = {}

    # OpenCorporates lookup
    from src.tools.opencorporates_tool import OpenCorporatesTool
    oc = OpenCorporatesTool()

    registrations = await oc.search_in_jurisdiction(company_name, country)
    if registrations:
        results["registration"] = registrations[0]

        # Get officers if found
        reg = registrations[0]
        officers = await oc.get_company_officers(
            reg.jurisdiction_code,
            reg.company_number
        )
        results["officers"] = officers

    # WHOIS lookup
    from src.tools.whois_tool import WhoisTool
    whois = WhoisTool()

    if whois.is_available() and website:
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        domain_info = await whois.lookup_domain(domain)
        results["domain"] = domain_info

    return results
```

---

## API Limits

### OpenCorporates
- Free: 500 requests/month (no key needed)
- Starter: $99/month - 10,000 requests
- Professional: $249/month - 50,000 requests

### WHOIS XML API
- Free: 500 requests (one-time)
- Basic: $29/month - 1,000 requests
- Professional: $99/month - 10,000 requests

---

## Testing Checklist

### OpenCorporates
- [ ] Search finds "Telecom Argentina"
- [ ] Jurisdiction code mapping works
- [ ] Officers endpoint returns data
- [ ] Handles companies not found gracefully

### WHOIS
- [ ] API key loads correctly
- [ ] lookup_domain returns data for claro.com.py
- [ ] Date parsing works
- [ ] Handles private registrations

---

## Related Files

- `src/tools/opencorporates_tool.py` - New tool
- `src/tools/whois_tool.py` - New tool
- `src/pipeline/comprehensive_research.py` - Integration
- `.env` - API keys
