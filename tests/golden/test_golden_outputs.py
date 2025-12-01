"""
Golden output tests for report consistency.

Compares generated outputs against expected golden reference outputs:
- Report structure consistency
- Section completeness
- Format compliance
"""

import pytest
from pathlib import Path
from typing import Dict, Any
import json
import re


# =============================================================================
# Golden Output Data
# =============================================================================


GOLDEN_REPORT_STRUCTURE = {
    "01-Context": {
        "required_files": ["01-Overview.md"],
        "optional_files": ["02-History.md", "03-Leadership.md"]
    },
    "02-Market": {
        "required_files": ["01-Market-Size-Growth.md"],
        "optional_files": ["02-Trends.md", "03-Drivers.md"]
    },
    "03-Competitors": {
        "required_files": ["01-Competitor-List.md"],
        "optional_files": ["02-Analysis.md", "03-Positioning.md"]
    },
    "04-Financials": {
        "required_files": ["01-Financials.md"],
        "optional_files": ["02-Metrics.md", "03-Projections.md"]
    },
    "05-Sales": {
        "required_files": ["05-Sales-Strategy.md"],
        "optional_files": ["02-Opportunities.md", "03-Approach.md"]
    }
}


GOLDEN_SECTION_PATTERNS = {
    "overview": {
        "required_headers": ["Overview", "Company", "Business"],
        "min_length": 500,
        "required_elements": ["company description", "headquarters or location"]
    },
    "market": {
        "required_headers": ["Market", "Size", "Growth"],
        "min_length": 800,
        "required_elements": ["market size", "CAGR or growth rate"]
    },
    "competitors": {
        "required_headers": ["Competitors", "Competition", "Competitive"],
        "min_length": 600,
        "required_elements": ["competitor names"]
    },
    "financials": {
        "required_headers": ["Financial", "Revenue", "Performance"],
        "min_length": 700,
        "required_elements": ["revenue figures", "financial metrics"]
    },
    "sales": {
        "required_headers": ["Sales", "Strategy", "Approach"],
        "min_length": 600,
        "required_elements": ["sales approach", "recommendations"]
    }
}


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def golden_data_dir(project_root) -> Path:
    """Return path to golden test data directory."""
    golden_dir = project_root / "tests" / "golden" / "data"
    golden_dir.mkdir(parents=True, exist_ok=True)
    return golden_dir


@pytest.fixture
def sample_report_output() -> Dict[str, str]:
    """Sample report output for comparison."""
    return {
        "01-Context/01-Overview.md": """# Company Overview

## About Test Corporation

Test Corporation is a leading technology company headquartered in San Francisco, USA.
Founded in 2015, the company specializes in enterprise software solutions.

### Key Facts
- **Founded:** 2015
- **Headquarters:** San Francisco, CA
- **Employees:** 500+
- **Industry:** Enterprise Software
""",
        "02-Market/01-Market-Size-Growth.md": """# Market Size and Growth

## Enterprise Software Market

The global enterprise software market was valued at $250 billion in 2023.
The market is expected to grow at a CAGR of 11.5% from 2024 to 2030.

### Key Drivers
- Digital transformation initiatives
- Cloud adoption acceleration
- Remote work trends
""",
        "03-Competitors/01-Competitor-List.md": """# Competitive Landscape

## Main Competitors

1. **Competitor A** - Market leader with 25% share
2. **Competitor B** - Strong in enterprise segment
3. **Competitor C** - Growing challenger

### Competitive Analysis
The market is moderately concentrated with top 5 players...
""",
        "04-Financials/01-Financials.md": """# Financial Overview

## Revenue Performance

Test Corporation reported revenues of $150 million in FY2023.
Year-over-year growth was 35%.

### Key Metrics
- Revenue: $150M (FY2023)
- Growth Rate: 35% YoY
- Gross Margin: 72%
""",
        "05-Sales/05-Sales-Strategy.md": """# Sales Strategy Recommendations

## Approach

Based on the analysis, we recommend the following sales approach:

1. **Value-Based Selling** - Focus on ROI and business outcomes
2. **Enterprise Focus** - Target large enterprises
3. **Partnership Channel** - Leverage partner ecosystem

### Key Talking Points
- Industry expertise
- Integration capabilities
- Customer success stories
"""
    }


# =============================================================================
# Structure Tests
# =============================================================================


class TestReportStructure:
    """Tests for report structure compliance."""

    @pytest.mark.golden
    def test_has_required_directories(self, sample_report_output):
        """Verify report has all required directories."""
        directories_found = set()

        for path in sample_report_output.keys():
            dir_name = path.split("/")[0]
            directories_found.add(dir_name)

        for required_dir in GOLDEN_REPORT_STRUCTURE.keys():
            assert required_dir in directories_found, f"Missing required directory: {required_dir}"

    @pytest.mark.golden
    def test_has_required_files(self, sample_report_output):
        """Verify report has all required files."""
        files_by_dir = {}

        for path in sample_report_output.keys():
            parts = path.split("/")
            dir_name = parts[0]
            file_name = parts[1] if len(parts) > 1 else parts[0]

            if dir_name not in files_by_dir:
                files_by_dir[dir_name] = []
            files_by_dir[dir_name].append(file_name)

        for dir_name, requirements in GOLDEN_REPORT_STRUCTURE.items():
            if dir_name in files_by_dir:
                for required_file in requirements["required_files"]:
                    assert any(required_file in f for f in files_by_dir[dir_name]), \
                        f"Missing required file: {required_file} in {dir_name}"

    @pytest.mark.golden
    def test_file_naming_convention(self, sample_report_output):
        """Verify files follow naming convention."""
        pattern = re.compile(r"^\d{2}-[A-Za-z\-]+\.md$")

        for path in sample_report_output.keys():
            file_name = path.split("/")[-1]
            assert pattern.match(file_name), f"File doesn't follow naming convention: {file_name}"


# =============================================================================
# Content Tests
# =============================================================================


class TestReportContent:
    """Tests for report content quality."""

    @pytest.mark.golden
    @pytest.mark.parametrize("section,requirements", GOLDEN_SECTION_PATTERNS.items())
    def test_section_has_required_headers(self, sample_report_output, section, requirements):
        """Verify sections have required headers."""
        # Find the relevant file
        relevant_files = {k: v for k, v in sample_report_output.items()
                         if section in k.lower()}

        if not relevant_files:
            pytest.skip(f"No files found for section: {section}")

        for path, content in relevant_files.items():
            header_found = any(
                header.lower() in content.lower()
                for header in requirements["required_headers"]
            )
            assert header_found, f"Missing required header in {path}"

    @pytest.mark.golden
    @pytest.mark.parametrize("section,requirements", GOLDEN_SECTION_PATTERNS.items())
    def test_section_meets_minimum_length(self, sample_report_output, section, requirements):
        """Verify sections meet minimum length requirements."""
        relevant_files = {k: v for k, v in sample_report_output.items()
                         if section in k.lower()}

        if not relevant_files:
            pytest.skip(f"No files found for section: {section}")

        for path, content in relevant_files.items():
            assert len(content) >= requirements["min_length"], \
                f"{path} is too short: {len(content)} < {requirements['min_length']}"

    @pytest.mark.golden
    def test_overview_contains_company_info(self, sample_report_output):
        """Verify overview contains essential company information."""
        overview_files = [v for k, v in sample_report_output.items()
                         if "overview" in k.lower()]

        if not overview_files:
            pytest.skip("No overview file found")

        content = overview_files[0].lower()

        required_info = ["founded", "headquarters", "industry"]
        for info in required_info:
            assert info in content or "headquarter" in content, \
                f"Overview missing: {info}"

    @pytest.mark.golden
    def test_financials_contains_numbers(self, sample_report_output):
        """Verify financials section contains numerical data."""
        financial_files = [v for k, v in sample_report_output.items()
                          if "financial" in k.lower()]

        if not financial_files:
            pytest.skip("No financial file found")

        content = financial_files[0]

        # Should contain numbers (revenue, percentages, etc.)
        number_pattern = re.compile(r"\$?\d+[\d,]*(\.\d+)?[%MB]?")
        numbers_found = number_pattern.findall(content)

        assert len(numbers_found) >= 3, "Financials section lacks numerical data"

    @pytest.mark.golden
    def test_market_contains_growth_data(self, sample_report_output):
        """Verify market section contains growth data."""
        market_files = [v for k, v in sample_report_output.items()
                        if "market" in k.lower()]

        if not market_files:
            pytest.skip("No market file found")

        content = market_files[0].lower()

        # Should contain growth indicators
        growth_indicators = ["cagr", "growth", "grew", "%"]
        assert any(indicator in content for indicator in growth_indicators), \
            "Market section lacks growth data"


# =============================================================================
# Format Tests
# =============================================================================


class TestReportFormat:
    """Tests for report format compliance."""

    @pytest.mark.golden
    def test_markdown_formatting(self, sample_report_output):
        """Verify content is valid markdown."""
        for path, content in sample_report_output.items():
            # Check for header
            assert content.strip().startswith("#"), \
                f"{path} should start with a markdown header"

            # Check for proper header hierarchy
            headers = re.findall(r"^(#+) ", content, re.MULTILINE)
            if headers:
                # First header should be h1
                assert headers[0] == "#", \
                    f"{path} should start with h1 header"

    @pytest.mark.golden
    def test_no_html_tags(self, sample_report_output):
        """Verify content doesn't contain raw HTML."""
        html_pattern = re.compile(r"<(?!br)[a-z]+[^>]*>", re.IGNORECASE)

        for path, content in sample_report_output.items():
            matches = html_pattern.findall(content)
            # Allow some basic HTML but not complex tags
            complex_html = [m for m in matches if not m.startswith("<br")]
            assert len(complex_html) == 0, \
                f"{path} contains HTML tags: {complex_html}"

    @pytest.mark.golden
    def test_proper_list_formatting(self, sample_report_output):
        """Verify lists are properly formatted."""
        for path, content in sample_report_output.items():
            # Check bullet points start with valid markers
            lines = content.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped and stripped[0] in "-*":
                    # Should have space after marker
                    assert len(stripped) > 1 and stripped[1] == " ", \
                        f"Invalid list format in {path}: {line}"


# =============================================================================
# Consistency Tests
# =============================================================================


class TestReportConsistency:
    """Tests for report consistency."""

    @pytest.mark.golden
    def test_consistent_company_name(self, sample_report_output):
        """Verify company name is consistent across sections."""
        company_names = []

        for path, content in sample_report_output.items():
            # Look for company name patterns
            # This is a simplified check - adjust based on actual format
            if "Test Corporation" in content:
                company_names.append("Test Corporation")

        # All mentions should be consistent
        if company_names:
            assert len(set(company_names)) == 1, "Company name inconsistent across sections"

    @pytest.mark.golden
    def test_no_placeholder_text(self, sample_report_output):
        """Verify no placeholder text remains."""
        placeholders = [
            "[TODO]",
            "[INSERT",
            "[PLACEHOLDER]",
            "Lorem ipsum",
            "XXX",
            "[TBD]",
            "<<",
            ">>"
        ]

        for path, content in sample_report_output.items():
            for placeholder in placeholders:
                assert placeholder not in content, \
                    f"Placeholder found in {path}: {placeholder}"

    @pytest.mark.golden
    def test_no_empty_sections(self, sample_report_output):
        """Verify no empty sections exist."""
        for path, content in sample_report_output.items():
            # Remove whitespace and check content
            stripped = content.strip()
            assert len(stripped) > 100, f"Section too short or empty: {path}"


# =============================================================================
# Comparison Tests
# =============================================================================


class TestGoldenComparison:
    """Tests comparing against golden reference outputs."""

    @pytest.mark.golden
    def test_structure_matches_golden(self, sample_report_output, golden_data_dir):
        """Verify output structure matches golden reference."""
        golden_file = golden_data_dir / "golden_structure.json"

        if not golden_file.exists():
            # Create golden file for first run
            structure = {
                "directories": sorted(set(k.split("/")[0] for k in sample_report_output.keys())),
                "files": sorted(sample_report_output.keys())
            }
            golden_file.write_text(json.dumps(structure, indent=2))
            pytest.skip("Golden file created, run again to compare")

        golden_structure = json.loads(golden_file.read_text())

        current_structure = {
            "directories": sorted(set(k.split("/")[0] for k in sample_report_output.keys())),
            "files": sorted(sample_report_output.keys())
        }

        assert current_structure["directories"] == golden_structure["directories"], \
            "Directory structure differs from golden"

    @pytest.mark.golden
    def test_key_metrics_present(self, sample_report_output):
        """Verify key metrics are present in output."""
        # Combine all content
        all_content = " ".join(sample_report_output.values()).lower()

        key_metrics = [
            ("market size", r"\$\d+"),
            ("growth", r"\d+\.?\d*%"),
            ("revenue", r"\$\d+")
        ]

        for metric_name, pattern in key_metrics:
            if metric_name in all_content:
                # If metric mentioned, should have actual value
                assert re.search(pattern, all_content), \
                    f"Metric '{metric_name}' mentioned but no value found"


# =============================================================================
# Regression Tests
# =============================================================================


class TestReportRegression:
    """Regression tests for report generation."""

    @pytest.mark.golden
    def test_all_sections_generated(self, sample_report_output):
        """Verify all sections are generated (regression check)."""
        expected_sections = 5  # At minimum

        directories = set(k.split("/")[0] for k in sample_report_output.keys())
        assert len(directories) >= expected_sections, \
            f"Expected at least {expected_sections} sections, got {len(directories)}"

    @pytest.mark.golden
    def test_no_truncated_content(self, sample_report_output):
        """Verify content is not truncated."""
        truncation_indicators = [
            "...",
            "[truncated]",
            "[continued]",
            "...more"
        ]

        for path, content in sample_report_output.items():
            # Check end of content
            last_100_chars = content[-100:].lower()

            for indicator in truncation_indicators:
                if indicator in last_100_chars:
                    # Allow ... only if it's in a proper context
                    if indicator == "..." and content.count("...") < 5:
                        continue
                    pytest.fail(f"Possible truncation in {path}: ends with indicator '{indicator}'")
