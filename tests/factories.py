"""
Test data factories for generating realistic test data.

Uses Faker library for generating diverse, realistic test data.
Provides factories for all major domain objects.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import string

try:
    from faker import Faker
    fake = Faker()
    FAKER_AVAILABLE = True
except ImportError:
    fake = None
    FAKER_AVAILABLE = False


# =============================================================================
# Company Data Factory
# =============================================================================


class CompanyFactory:
    """Factory for generating company profile data."""

    INDUSTRIES = [
        "Technology",
        "Healthcare",
        "Finance",
        "Manufacturing",
        "Retail",
        "Energy",
        "Telecommunications",
        "Automotive",
        "Aerospace",
        "Biotechnology",
        "E-commerce",
        "SaaS",
        "Fintech",
        "Real Estate",
        "Education",
    ]

    COUNTRIES = [
        "USA",
        "UK",
        "Germany",
        "France",
        "Japan",
        "China",
        "Canada",
        "Australia",
        "India",
        "Brazil",
        "Netherlands",
        "Switzerland",
        "Singapore",
        "South Korea",
    ]

    @classmethod
    def create(
        cls,
        name: Optional[str] = None,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        description: Optional[str] = None,
        employees: Optional[int] = None,
        founded: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a company profile with realistic data.

        Args:
            name: Company name (generated if not provided)
            website: Company website URL
            industry: Industry sector
            country: Headquarters country
            description: Company description
            employees: Employee count
            founded: Year founded

        Returns:
            Dictionary with company profile data
        """
        if FAKER_AVAILABLE:
            _name = name or fake.company()
            _website = website or f"https://{_name.lower().replace(' ', '').replace(',', '')[:20]}.com"
            _description = description or fake.paragraph(nb_sentences=3)
            _founded = founded or fake.random_int(min=1900, max=2023)
        else:
            _name = name or f"Company_{random.randint(1000, 9999)}"
            _website = website or f"https://company{random.randint(1000, 9999)}.com"
            _description = description or "A company that does business things."
            _founded = founded or random.randint(1900, 2023)

        return {
            "name": _name,
            "website": _website,
            "industry": industry or random.choice(cls.INDUSTRIES),
            "country": country or random.choice(cls.COUNTRIES),
            "description": _description,
            "employees": employees or random.randint(10, 100000),
            "founded": _founded,
        }

    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple company profiles."""
        return [cls.create(**kwargs) for _ in range(count)]


# =============================================================================
# Financial Data Factory
# =============================================================================


class FinancialDataFactory:
    """Factory for generating financial data."""

    SECTORS = ["Technology", "Healthcare", "Finance", "Consumer", "Industrial"]

    @classmethod
    def create(
        cls,
        ticker: Optional[str] = None,
        name: Optional[str] = None,
        market_cap: Optional[float] = None,
        revenue: Optional[float] = None,
        profit_margin: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create financial data with realistic values.

        Args:
            ticker: Stock ticker symbol
            name: Company name
            market_cap: Market capitalization
            revenue: Annual revenue
            profit_margin: Profit margin (0-1)

        Returns:
            Dictionary with financial data
        """
        _ticker = ticker or ''.join(random.choices(string.ascii_uppercase, k=4))
        _market_cap = market_cap or random.uniform(1e8, 1e12)
        _revenue = revenue or random.uniform(1e6, 1e11)
        _profit_margin = profit_margin or random.uniform(-0.2, 0.4)

        if FAKER_AVAILABLE:
            _name = name or fake.company()
        else:
            _name = name or f"Company {_ticker}"

        return {
            "ticker": _ticker,
            "basic_info": {
                "name": _name,
                "sector": random.choice(cls.SECTORS),
                "industry": random.choice(CompanyFactory.INDUSTRIES),
            },
            "market_data": {
                "market_cap": _market_cap,
                "current_price": random.uniform(10, 1000),
                "52_week_high": random.uniform(100, 2000),
                "52_week_low": random.uniform(5, 500),
                "volume": random.randint(100000, 10000000),
                "pe_ratio": random.uniform(5, 100),
            },
            "financials": {
                "revenue": _revenue,
                "net_income": _revenue * _profit_margin,
                "profit_margin": _profit_margin,
                "gross_margin": random.uniform(0.2, 0.8),
                "operating_margin": random.uniform(0.05, 0.3),
            },
            "employees": random.randint(100, 500000),
        }


# =============================================================================
# Research Source Factory
# =============================================================================


class ResearchSourceFactory:
    """Factory for generating research source data."""

    SOURCE_TYPES = ["web", "news", "blog", "pdf", "social", "company_page"]

    CATEGORIES = [
        "market_intelligence",
        "company_info",
        "financial",
        "competitor",
        "news",
        "social_media",
    ]

    @classmethod
    def create(
        cls,
        url: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        source_type: Optional[str] = None,
        category: Optional[str] = None,
        reliability_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a research source with realistic data.

        Args:
            url: Source URL
            title: Article/page title
            content: Source content
            source_type: Type of source
            category: Content category
            reliability_score: Reliability score (0-1)

        Returns:
            Dictionary with research source data
        """
        if FAKER_AVAILABLE:
            _url = url or fake.url()
            _title = title or fake.sentence(nb_words=8)
            _content = content or fake.paragraphs(nb=3)
            if isinstance(_content, list):
                _content = "\n\n".join(_content)
        else:
            _url = url or f"https://example.com/article/{random.randint(1000, 9999)}"
            _title = title or f"Article Title {random.randint(1, 100)}"
            _content = content or "Sample content for testing purposes."

        return {
            "url": _url,
            "title": _title,
            "content": _content,
            "source_type": source_type or random.choice(cls.SOURCE_TYPES),
            "category": category or random.choice(cls.CATEGORIES),
            "reliability_score": reliability_score or random.uniform(0.5, 1.0),
            "fetched_at": datetime.now().isoformat(),
        }

    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple research sources."""
        return [cls.create(**kwargs) for _ in range(count)]


# =============================================================================
# Search Result Factory
# =============================================================================


class SearchResultFactory:
    """Factory for generating search result data."""

    @classmethod
    def create(
        cls,
        title: Optional[str] = None,
        url: Optional[str] = None,
        content: Optional[str] = None,
        score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a search result with realistic data.

        Args:
            title: Result title
            url: Result URL
            content: Result snippet/content
            score: Relevance score (0-1)

        Returns:
            Dictionary with search result data
        """
        if FAKER_AVAILABLE:
            _title = title or fake.sentence(nb_words=6)
            _url = url or fake.url()
            _content = content or fake.paragraph(nb_sentences=2)
        else:
            _title = title or f"Search Result {random.randint(1, 100)}"
            _url = url or f"https://example.com/{random.randint(1000, 9999)}"
            _content = content or "Search result content snippet."

        return {
            "title": _title,
            "url": _url,
            "content": _content,
            "score": score or random.uniform(0.5, 1.0),
        }

    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple search results."""
        return [cls.create(**kwargs) for _ in range(count)]


# =============================================================================
# AI Response Factory
# =============================================================================


class AIResponseFactory:
    """Factory for generating AI response data."""

    @classmethod
    def create_text(
        cls,
        content: Optional[str] = None,
        tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a text AI response.

        Args:
            content: Response content
            tokens: Token count

        Returns:
            Dictionary with AI response data
        """
        if FAKER_AVAILABLE:
            _content = content or fake.paragraph(nb_sentences=5)
        else:
            _content = content or "This is a mock AI response for testing."

        return {
            "content": _content,
            "format": "text",
            "usage": {
                "prompt_tokens": random.randint(100, 1000),
                "completion_tokens": tokens or random.randint(50, 500),
                "total_tokens": random.randint(150, 1500),
            },
        }

    @classmethod
    def create_json(
        cls,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a JSON AI response.

        Args:
            data: JSON data to include

        Returns:
            Dictionary with AI response data
        """
        import json

        if data is None:
            data = {
                "analysis": "Sample analysis result",
                "confidence": random.uniform(0.7, 0.99),
                "findings": ["Finding 1", "Finding 2", "Finding 3"],
            }

        return {
            "content": json.dumps(data),
            "format": "json",
            "parsed": data,
            "usage": {
                "prompt_tokens": random.randint(100, 1000),
                "completion_tokens": random.randint(100, 500),
                "total_tokens": random.randint(200, 1500),
            },
        }

    @classmethod
    def create_error(
        cls,
        message: Optional[str] = None,
        error_type: str = "api_error",
    ) -> Dict[str, Any]:
        """
        Create an error AI response.

        Args:
            message: Error message
            error_type: Type of error

        Returns:
            Dictionary with error response data
        """
        return {
            "error": True,
            "error_type": error_type,
            "message": message or "An error occurred during AI generation",
            "content": None,
        }


# =============================================================================
# Task Factory
# =============================================================================


class TaskFactory:
    """Factory for generating task data."""

    STATUSES = ["pending", "running", "completed", "failed", "cancelled"]

    @classmethod
    def create(
        cls,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a task with realistic data.

        Args:
            task_id: Task identifier
            status: Task status
            company_name: Company being researched

        Returns:
            Dictionary with task data
        """
        if FAKER_AVAILABLE:
            _task_id = task_id or fake.uuid4()
            _company_name = company_name or fake.company()
        else:
            _task_id = task_id or f"task-{random.randint(10000, 99999)}"
            _company_name = company_name or f"Company {random.randint(1, 100)}"

        return {
            "task_id": str(_task_id),
            "status": status or random.choice(cls.STATUSES),
            "company_name": _company_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }


# =============================================================================
# Edge Case Data Generators
# =============================================================================


class EdgeCaseGenerator:
    """Generator for edge case test data."""

    @classmethod
    def empty_strings(cls) -> List[str]:
        """Generate various empty/whitespace strings."""
        return ["", " ", "  ", "\t", "\n", "\r\n", "   \t\n   "]

    @classmethod
    def long_strings(cls, lengths: List[int] = None) -> List[str]:
        """Generate strings of various lengths."""
        lengths = lengths or [100, 500, 1000, 5000, 10000]
        return ["A" * length for length in lengths]

    @classmethod
    def unicode_strings(cls) -> List[str]:
        """Generate strings with various unicode characters."""
        return [
            "测试公司",  # Chinese
            "テスト会社",  # Japanese
            "مرحبا",  # Arabic
            "Тест",  # Cyrillic
            "🚀🎉💻",  # Emojis
            "Ñoño",  # Spanish
            "Ölkücü",  # Turkish
            "Cześć",  # Polish
        ]

    @classmethod
    def special_characters(cls) -> List[str]:
        """Generate strings with special characters."""
        return [
            "Test & Co.",
            "Test <Company>",
            'Test "Quoted"',
            "Test's Company",
            "Test/Slash",
            "Test\\Backslash",
            "Test|Pipe",
            "Test:Colon",
            "Test;Semicolon",
        ]

    @classmethod
    def injection_attempts(cls) -> List[str]:
        """Generate strings that attempt various injections."""
        return [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "${7*7}",
            "{{7*7}}",
            "{{constructor.constructor('return this')()}}",
            "' OR '1'='1",
            "<img src=x onerror=alert(1)>",
        ]

    @classmethod
    def boundary_numbers(cls) -> List[Any]:
        """Generate boundary case numbers."""
        return [
            0,
            -1,
            1,
            -0.0,
            float("inf"),
            float("-inf"),
            float("nan"),
            2**31 - 1,  # Max 32-bit signed
            2**31,  # Overflow 32-bit signed
            2**63 - 1,  # Max 64-bit signed
        ]

    @classmethod
    def all_edge_cases(cls) -> Dict[str, List[Any]]:
        """Get all edge cases organized by type."""
        return {
            "empty": cls.empty_strings(),
            "long": cls.long_strings(),
            "unicode": cls.unicode_strings(),
            "special": cls.special_characters(),
            "injection": cls.injection_attempts(),
            "numbers": cls.boundary_numbers(),
        }


# =============================================================================
# Bulk Data Generators
# =============================================================================


class BulkDataGenerator:
    """Generator for bulk test data."""

    @classmethod
    def research_workflow_data(cls, company_count: int = 5) -> List[Dict[str, Any]]:
        """Generate complete research workflow test data."""
        return [
            {
                "company": CompanyFactory.create(),
                "financial": FinancialDataFactory.create(),
                "sources": ResearchSourceFactory.create_batch(count=random.randint(3, 10)),
                "search_results": SearchResultFactory.create_batch(count=random.randint(5, 15)),
            }
            for _ in range(company_count)
        ]

    @classmethod
    def stress_test_companies(cls, count: int = 100) -> List[Dict[str, Any]]:
        """Generate large batch of companies for stress testing."""
        return CompanyFactory.create_batch(count=count)

    @classmethod
    def diverse_companies(cls) -> List[Dict[str, Any]]:
        """Generate companies across all industries and countries."""
        companies = []
        for industry in CompanyFactory.INDUSTRIES:
            for country in CompanyFactory.COUNTRIES[:5]:  # Top 5 countries
                companies.append(
                    CompanyFactory.create(industry=industry, country=country)
                )
        return companies

    @classmethod
    def mixed_quality_sources(cls, count: int = 20) -> List[Dict[str, Any]]:
        """Generate sources with mixed reliability scores."""
        sources = []
        reliability_buckets = [
            (0.0, 0.3, "low"),
            (0.3, 0.6, "medium"),
            (0.6, 0.8, "good"),
            (0.8, 1.0, "excellent"),
        ]
        for low, high, _ in reliability_buckets:
            bucket_count = count // len(reliability_buckets)
            for _ in range(bucket_count):
                sources.append(
                    ResearchSourceFactory.create(
                        reliability_score=random.uniform(low, high)
                    )
                )
        return sources


# =============================================================================
# Research State Factory
# =============================================================================


class ResearchStateFactory:
    """Factory for generating research state data."""

    @classmethod
    def create_initial(
        cls,
        company_name: Optional[str] = None,
        website: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create initial research state."""
        company = CompanyFactory.create(name=company_name)
        return {
            "company_name": company["name"],
            "website": website or company["website"],
            "industry": company["industry"],
            "country": company["country"],
            "raw_data": {},
            "source_log": [],
            "financial_data": {},
            "market_data": {},
            "competitor_data": {},
            "drafts": {},
            "errors": [],
            "iteration": 0,
            "max_iterations": 3,
        }

    @classmethod
    def create_with_data(cls, **kwargs) -> Dict[str, Any]:
        """Create research state with populated data."""
        state = cls.create_initial(**kwargs)
        state["financial_data"] = FinancialDataFactory.create()
        state["source_log"] = ResearchSourceFactory.create_batch(count=5)
        state["iteration"] = 1
        return state

    @classmethod
    def create_completed(cls, **kwargs) -> Dict[str, Any]:
        """Create completed research state."""
        state = cls.create_with_data(**kwargs)
        state["market_data"] = {
            "sector": CompanyFactory.INDUSTRIES[0],
            "market_size": random.uniform(1e9, 1e12),
            "growth_rate": random.uniform(0.01, 0.15),
        }
        state["competitor_data"] = {
            "competitors": [CompanyFactory.create()["name"] for _ in range(3)],
            "market_position": random.choice(["leader", "challenger", "follower"]),
        }
        state["drafts"] = {
            "executive_summary": "Executive summary content...",
            "financial_analysis": "Financial analysis content...",
            "market_analysis": "Market analysis content...",
        }
        state["iteration"] = state["max_iterations"]
        return state

    @classmethod
    def create_with_errors(cls, error_count: int = 2, **kwargs) -> Dict[str, Any]:
        """Create research state with errors."""
        state = cls.create_with_data(**kwargs)
        state["errors"] = [
            f"Error {i}: {random.choice(['API timeout', 'Rate limit', 'Parse error', 'Network error'])}"
            for i in range(error_count)
        ]
        return state
