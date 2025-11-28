"""
Property-based tests for Pydantic models.

Uses Hypothesis to generate random valid inputs and verify
that model invariants hold.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pydantic import ValidationError


# =============================================================================
# Custom Strategies
# =============================================================================


# Strategy for valid company names
valid_company_name = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=200,
).filter(lambda x: x.strip())  # Must have non-whitespace content


# Strategy for valid URLs
valid_url = st.from_regex(
    r'https?://[a-z][a-z0-9\-]*(\.[a-z][a-z0-9\-]*)+(/[a-z0-9\-._~:/?#\[\]@!$&\'()*+,;=]*)?',
    fullmatch=True,
)


# Strategy for industries
industry = st.sampled_from([
    "Technology", "Healthcare", "Finance", "Manufacturing",
    "Retail", "Energy", "Telecommunications", "Automotive",
    None,
])


# Strategy for countries
country = st.sampled_from([
    "USA", "UK", "Germany", "France", "Japan", "China",
    "Canada", "Australia", "India", "Brazil",
])


# =============================================================================
# ResearchRequest Property Tests
# =============================================================================


class TestResearchRequestProperties:
    """Property-based tests for ResearchRequest model."""

    @pytest.mark.property
    @given(company_name=valid_company_name)
    @settings(max_examples=100)
    def test_valid_company_name_accepted(self, company_name):
        """Property: Any valid company name should be accepted."""
        from src.api.models import ResearchRequest

        # Skip if name becomes empty after strip
        assume(company_name.strip())

        request = ResearchRequest(company_name=company_name)
        assert request.company_name == company_name.strip()

    @pytest.mark.property
    @given(company_name=valid_company_name, country_val=country)
    @settings(max_examples=50)
    def test_country_defaults_to_usa(self, company_name, country_val):
        """Property: Country defaults to USA when not provided."""
        from src.api.models import ResearchRequest

        assume(company_name.strip())

        if country_val is None:
            request = ResearchRequest(company_name=company_name)
            assert request.country == "USA"
        else:
            request = ResearchRequest(company_name=company_name, country=country_val)
            assert request.country == country_val

    @pytest.mark.property
    @given(whitespace=st.text(alphabet=' \t\n\r', min_size=1, max_size=10))
    @settings(max_examples=20)
    def test_whitespace_only_rejected(self, whitespace):
        """Property: Whitespace-only company names are rejected."""
        from src.api.models import ResearchRequest

        with pytest.raises(ValidationError):
            ResearchRequest(company_name=whitespace)

    @pytest.mark.property
    @given(
        company_name=valid_company_name,
        padding=st.text(alphabet=' \t', min_size=0, max_size=5),
    )
    @settings(max_examples=50)
    def test_company_name_stripped(self, company_name, padding):
        """Property: Company name whitespace is stripped."""
        from src.api.models import ResearchRequest

        assume(company_name.strip())

        padded_name = padding + company_name + padding
        request = ResearchRequest(company_name=padded_name)

        assert request.company_name == company_name.strip()

    @pytest.mark.property
    @given(length=st.integers(min_value=201, max_value=500))
    @settings(max_examples=20)
    def test_long_company_name_rejected(self, length):
        """Property: Company names over 200 chars are rejected."""
        from src.api.models import ResearchRequest

        long_name = "A" * length

        with pytest.raises(ValidationError):
            ResearchRequest(company_name=long_name)

    @pytest.mark.property
    @given(
        company_name=valid_company_name,
        industry_val=industry,
    )
    @settings(max_examples=50)
    def test_industry_can_be_none(self, company_name, industry_val):
        """Property: Industry can be None or a valid string."""
        from src.api.models import ResearchRequest

        assume(company_name.strip())

        request = ResearchRequest(company_name=company_name, industry=industry_val)

        if industry_val and industry_val.strip():
            assert request.industry == industry_val.strip()
        else:
            assert request.industry is None


# =============================================================================
# TaskStatusResponse Property Tests
# =============================================================================


class TestTaskStatusResponseProperties:
    """Property-based tests for TaskStatusResponse model."""

    @pytest.mark.property
    @given(
        task_id=st.text(min_size=1, max_size=100),
        status=st.sampled_from(["pending", "running", "completed", "failed"]),
    )
    @settings(max_examples=50)
    def test_required_fields_always_present(self, task_id, status):
        """Property: Required fields are always present in response."""
        from src.api.models import TaskStatusResponse

        response = TaskStatusResponse(task_id=task_id, status=status)

        assert response.task_id == task_id
        assert response.status == status

    @pytest.mark.property
    @given(
        task_id=st.text(min_size=1, max_size=50),
        result_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)),
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_result_preserved(self, task_id, result_data):
        """Property: Result data is preserved exactly."""
        from src.api.models import TaskStatusResponse

        response = TaskStatusResponse(
            task_id=task_id,
            status="completed",
            result=result_data,
        )

        assert response.result == result_data


# =============================================================================
# CompanyProfile Property Tests
# =============================================================================


class TestCompanyProfileProperties:
    """Property-based tests for CompanyProfile model."""

    @pytest.mark.property
    @given(
        name=valid_company_name,
        industry_val=industry,
    )
    @settings(max_examples=50)
    def test_name_stripped_and_validated(self, name, industry_val):
        """Property: Name is always stripped."""
        from src.core.types import CompanyProfile

        assume(name.strip())

        profile = CompanyProfile(name=name, industry=industry_val)
        assert profile.name == name.strip()

    @pytest.mark.property
    @given(
        name=valid_company_name,
        website=st.one_of(st.none(), st.just("example.com"), st.just("https://example.com")),
    )
    @settings(max_examples=30)
    def test_website_normalized(self, name, website):
        """Property: Website is normalized with https:// prefix."""
        from src.core.types import CompanyProfile

        assume(name.strip())

        profile = CompanyProfile(name=name, website=website)

        if website and not website.startswith("http"):
            assert profile.website.startswith("https://")
        elif website:
            assert profile.website == website

    @pytest.mark.property
    @given(
        name=valid_company_name,
        competitors=st.lists(st.text(min_size=0, max_size=50), max_size=10),
    )
    @settings(max_examples=30)
    def test_competitors_filtered(self, name, competitors):
        """Property: Empty competitor names are filtered out."""
        from src.core.types import CompanyProfile

        assume(name.strip())

        profile = CompanyProfile(name=name, competitors=competitors)

        # All competitors should be non-empty after filtering
        for comp in profile.competitors:
            assert comp.strip()


# =============================================================================
# ResearchState Property Tests
# =============================================================================


class TestResearchStateProperties:
    """Property-based tests for ResearchState model."""

    @pytest.mark.property
    @given(
        company_name=st.text(min_size=0, max_size=100),
        website=st.text(min_size=0, max_size=200),
    )
    @settings(max_examples=50)
    def test_defaults_are_consistent(self, company_name, website):
        """Property: Default values are always consistent."""
        from src.graph.state import ResearchState

        state = ResearchState(company_name=company_name, website=website)

        # Verify all defaults
        assert state.raw_data == []
        assert state.source_log == []
        assert state.financial_data == {}
        assert state.market_data == {}
        assert state.sales_data == {}
        assert state.competitor_data == {}
        assert state.brand_data == {}
        assert state.drafts == {}
        assert state.current_wave == "init"
        assert state.messages == []
        assert state.errors == []
        assert state.critique_feedback is None
        assert state.feedback_loop_count == 0

    @pytest.mark.property
    @given(
        company_name=st.text(min_size=1, max_size=50),
        loop_count=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=30)
    def test_feedback_loop_count_preserved(self, company_name, loop_count):
        """Property: Feedback loop count is preserved."""
        from src.graph.state import ResearchState

        state = ResearchState(
            company_name=company_name,
            website="https://test.com",
            feedback_loop_count=loop_count,
        )

        assert state.feedback_loop_count == loop_count


# =============================================================================
# DataSourceResult Property Tests
# =============================================================================


class TestDataSourceResultProperties:
    """Property-based tests for DataSourceResult."""

    @pytest.mark.property
    @given(data=st.one_of(st.text(), st.integers(), st.dictionaries(st.text(), st.text())))
    @settings(max_examples=50)
    def test_ok_always_succeeds(self, data):
        """Property: ok() always creates successful result."""
        from src.agents.specialists import DataSourceResult

        result = DataSourceResult.ok(data)

        assert result.success is True
        assert result.data == data
        assert result.error is None

    @pytest.mark.property
    @given(error_msg=st.text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_fail_always_fails(self, error_msg):
        """Property: fail() always creates failed result."""
        from src.agents.specialists import DataSourceResult

        result = DataSourceResult.fail(error_msg)

        assert result.success is False
        assert result.error == error_msg
        assert result.data is None

    @pytest.mark.property
    @given(
        data=st.text(),
        warning=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=50)
    def test_warn_has_data_and_warning(self, data, warning):
        """Property: warn() has both data and warning."""
        from src.agents.specialists import DataSourceResult

        result = DataSourceResult.warn(data, warning)

        assert result.success is True
        assert result.data == data
        assert result.warning == warning
        assert result.error is None
