"""
Content Data Extractor (P0 Fix)

Extracts structured data types from source content and maps them to appropriate sections.
This fixes the source-to-section mapping bug where financial data, market share, etc.
were only assigned to 'strategic_context' instead of their proper sections.

The key insight: A single source can contain data relevant to MULTIPLE sections.
For example, a news article about a company might contain:
- Revenue figures -> data_room/01-Financials.md
- Market share % -> competitive_landscape/04-Market-Share.md
- Employee count -> strategic_context/01-Company-Overview.md
- Executive names -> strategic_context/04-Key-People.md
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

from ..logging import setup_logger

logger = setup_logger("content_data_extractor")


class DataType(str, Enum):
    """Types of structured data that can be extracted from content."""
    REVENUE = "revenue"
    MARKET_SHARE = "market_share"
    SUBSCRIBERS = "subscribers"
    EMPLOYEES = "employees"
    FOUNDED_YEAR = "founded_year"
    HEADQUARTERS = "headquarters"
    EXECUTIVE = "executive"
    MARKET_SIZE = "market_size"
    GROWTH_RATE = "growth_rate"
    PRICING = "pricing"
    FUNDING = "funding"
    ACQUISITION = "acquisition"
    PARTNERSHIP = "partnership"
    PRODUCT_LAUNCH = "product_launch"


# Map data types to their target output sections
DATA_TYPE_TO_SECTIONS: Dict[DataType, List[str]] = {
    DataType.REVENUE: ["data_room", "investment_analysis"],
    DataType.MARKET_SHARE: ["competitive_landscape", "market_intelligence"],
    DataType.SUBSCRIBERS: ["data_room", "market_intelligence"],
    DataType.EMPLOYEES: ["strategic_context", "data_room"],
    DataType.FOUNDED_YEAR: ["strategic_context"],
    DataType.HEADQUARTERS: ["strategic_context"],
    DataType.EXECUTIVE: ["strategic_context"],
    DataType.MARKET_SIZE: ["market_intelligence", "investment_analysis"],
    DataType.GROWTH_RATE: ["market_intelligence", "investment_analysis"],
    DataType.PRICING: ["competitive_landscape", "sales_intelligence"],
    DataType.FUNDING: ["data_room", "investment_analysis"],
    DataType.ACQUISITION: ["strategic_context", "investment_analysis"],
    DataType.PARTNERSHIP: ["strategic_context"],
    DataType.PRODUCT_LAUNCH: ["strategic_context", "marketing_execution"],
}


@dataclass
class ExtractedData:
    """A piece of structured data extracted from content."""
    data_type: DataType
    value: str
    confidence: float  # 0.0 to 1.0
    context: str  # Surrounding text
    target_sections: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.target_sections:
            self.target_sections = DATA_TYPE_TO_SECTIONS.get(self.data_type, [])


@dataclass
class ExtractionResult:
    """Result of extracting data from content."""
    source_url: str
    extracted_data: List[ExtractedData]
    sections_to_add: Set[str] = field(default_factory=set)

    def __post_init__(self):
        # Compute all sections this source should be mapped to
        for data in self.extracted_data:
            self.sections_to_add.update(data.target_sections)


class ContentDataExtractor:
    """
    Extracts structured data from source content for multi-section mapping.

    This solves the P0 bug where sources containing financial data were only
    mapped to strategic_context because that's what the query targeted.

    Usage:
        extractor = ContentDataExtractor()
        result = extractor.extract("https://example.com", page_content)

        # Get all sections this source should be mapped to
        additional_sections = result.sections_to_add

        # Get specific extracted values
        for data in result.extracted_data:
            print(f"{data.data_type}: {data.value}")
    """

    def __init__(self):
        self._patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[DataType, List[Tuple[re.Pattern, float]]]:
        """Build regex patterns for each data type with confidence scores."""
        patterns = {}

        # Revenue patterns (confidence varies by specificity)
        patterns[DataType.REVENUE] = [
            # "revenue of $X million/billion" - high confidence
            (re.compile(
                r'(?:revenue|ingresos|facturación|sales)\s+(?:of\s+)?'
                r'(?:USD?\s*\$?|€|G\.?\s*)?\s*'
                r'([\d,\.]+)\s*'
                r'(million|billion|millones|mil millones|M|B|MM)',
                re.IGNORECASE
            ), 0.9),
            # "facturó USD X millones" pattern
            (re.compile(
                r'factur[óo]\s+(?:USD?\s*\$?)?\s*([\d,\.]+)\s*(million|millones)',
                re.IGNORECASE
            ), 0.9),
            # "$X million in revenue"
            (re.compile(
                r'(?:USD?\s*\$?|€)\s*([\d,\.]+)\s*(million|billion|M|B)\s+(?:in\s+)?(?:revenue|sales)',
                re.IGNORECASE
            ), 0.85),
            # Generic "X million revenue"
            (re.compile(
                r'([\d,\.]+)\s*(million|billion|millones)\s+(?:in\s+)?(?:revenue|ingresos)',
                re.IGNORECASE
            ), 0.7),
        ]

        # Market share patterns
        patterns[DataType.MARKET_SHARE] = [
            # "X% market share" - high confidence
            (re.compile(
                r'([\d,\.]+)\s*%\s*(?:del\s+)?(?:market\s+share|cuota\s+de\s+mercado|participación)',
                re.IGNORECASE
            ), 0.9),
            # "market share of X%"
            (re.compile(
                r'(?:market\s+share|cuota|participación)\s+(?:of\s+|de\s+|del\s+)?([\d,\.]+)\s*%',
                re.IGNORECASE
            ), 0.9),
            # "leads with X%" or "holds X%"
            (re.compile(
                r'(?:leads?|holds?|has|tiene|posee)\s+(?:a\s+)?([\d,\.]+)\s*%\s*(?:of\s+)?(?:the\s+)?(?:market)?',
                re.IGNORECASE
            ), 0.7),
        ]

        # Subscriber/customer count patterns
        patterns[DataType.SUBSCRIBERS] = [
            # "X million subscribers/customers/users"
            (re.compile(
                r'([\d,\.]+)\s*(million|millones|M)?\s*'
                r'(?:subscribers?|customers?|users?|clientes?|usuarios?|abonados?|líneas?)',
                re.IGNORECASE
            ), 0.85),
            # "subscriber base of X"
            (re.compile(
                r'(?:subscriber|customer|user)\s+base\s+(?:of\s+)?([\d,\.]+)',
                re.IGNORECASE
            ), 0.8),
        ]

        # Employee count patterns
        patterns[DataType.EMPLOYEES] = [
            # "X employees" or "X funcionarios"
            (re.compile(
                r'([\d,\.]+)\s*(?:employees?|funcionarios?|trabajadores?|colaboradores?|staff)',
                re.IGNORECASE
            ), 0.85),
            # "workforce of X" or "plantel de X"
            (re.compile(
                r'(?:workforce|plantel|equipo)\s+(?:of\s+|de\s+)?([\d,\.]+)',
                re.IGNORECASE
            ), 0.8),
            # "reduced staff by X"
            (re.compile(
                r'(?:reduced|cut|eliminated|redujo)\s+(?:staff|plantel)?\s*(?:by\s+|en\s+)?([\d,\.]+)',
                re.IGNORECASE
            ), 0.7),
        ]

        # Founded year patterns
        patterns[DataType.FOUNDED_YEAR] = [
            # "founded in YYYY" or "established in YYYY"
            (re.compile(
                r'(?:founded|established|created|fundada?|creada?|establecida?)\s+'
                r'(?:in\s+|en\s+)?(\d{4})',
                re.IGNORECASE
            ), 0.9),
            # "since YYYY"
            (re.compile(r'(?:since|desde)\s+(\d{4})', re.IGNORECASE), 0.7),
        ]

        # Executive/leadership patterns
        patterns[DataType.EXECUTIVE] = [
            # "CEO/President/Director Name"
            (re.compile(
                r'(?:CEO|President|Director|Presidente|Gerente\s+General|Chairman)\s*'
                r'(?::\s*|,\s*|de\s+)?([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+)',
                re.IGNORECASE
            ), 0.85),
            # "Name is/was appointed CEO"
            (re.compile(
                r'([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+)\s+'
                r'(?:is|was|fue|es)\s+(?:appointed|named|designated|nombrado)\s+'
                r'(?:as\s+)?(?:CEO|President|Director)',
                re.IGNORECASE
            ), 0.8),
        ]

        # Market size patterns
        patterns[DataType.MARKET_SIZE] = [
            # "market size of $X billion"
            (re.compile(
                r'(?:market\s+size|TAM|total\s+addressable)\s+(?:of\s+)?'
                r'(?:USD?\s*\$?|€)?\s*([\d,\.]+)\s*(billion|million|B|M)',
                re.IGNORECASE
            ), 0.9),
            # "$X billion market"
            (re.compile(
                r'(?:USD?\s*\$?|€)\s*([\d,\.]+)\s*(billion|million)\s+market',
                re.IGNORECASE
            ), 0.8),
        ]

        # Growth rate patterns
        patterns[DataType.GROWTH_RATE] = [
            # "X% growth" or "grew X%"
            (re.compile(
                r'(?:growth|grew|crecimiento|creció)\s+(?:of\s+|del?\s+)?([\d,\.]+)\s*%',
                re.IGNORECASE
            ), 0.85),
            # "CAGR of X%"
            (re.compile(r'CAGR\s+(?:of\s+)?([\d,\.]+)\s*%', re.IGNORECASE), 0.9),
            # "increased X%"
            (re.compile(
                r'(?:increased|rose|subió|aumentó)\s+(?:by\s+)?([\d,\.]+)\s*%',
                re.IGNORECASE
            ), 0.7),
        ]

        # Pricing patterns
        patterns[DataType.PRICING] = [
            # "plan costs $X/month" or "Gs. X por mes"
            (re.compile(
                r'(?:USD?\s*\$?|G[s\.]+\s*|€)\s*([\d,\.]+)\s*'
                r'(?:/|per|por)\s*(?:month|mes|año|year)',
                re.IGNORECASE
            ), 0.8),
            # "starting at $X"
            (re.compile(
                r'(?:starting|desde|from)\s+(?:at\s+)?(?:USD?\s*\$?|G[s\.]+\s*)\s*([\d,\.]+)',
                re.IGNORECASE
            ), 0.7),
        ]

        # Funding patterns
        patterns[DataType.FUNDING] = [
            # "raised $X million"
            (re.compile(
                r'(?:raised|secured|received|recibió)\s+(?:USD?\s*\$?)?\s*'
                r'([\d,\.]+)\s*(million|billion|millones)',
                re.IGNORECASE
            ), 0.9),
            # "$X million investment"
            (re.compile(
                r'(?:USD?\s*\$?)\s*([\d,\.]+)\s*(million|billion)\s+'
                r'(?:investment|funding|inversión)',
                re.IGNORECASE
            ), 0.85),
        ]

        # Acquisition patterns
        patterns[DataType.ACQUISITION] = [
            # "acquired X" or "bought X"
            (re.compile(
                r'(?:acquired|bought|purchased|adquirió|compró)\s+'
                r'([A-Z][A-Za-záéíóúñ\s]+?)(?:\s+for|\s+por|\s+in|\.|,)',
                re.IGNORECASE
            ), 0.8),
            # "acquisition of X"
            (re.compile(
                r'(?:acquisition|adquisición)\s+(?:of|de)\s+([A-Z][A-Za-záéíóúñ\s]+)',
                re.IGNORECASE
            ), 0.85),
        ]

        return patterns

    def extract(self, url: str, content: str) -> ExtractionResult:
        """
        Extract structured data from content.

        Args:
            url: Source URL (for logging)
            content: Text content to analyze

        Returns:
            ExtractionResult with all extracted data and target sections
        """
        extracted = []

        if not content:
            return ExtractionResult(source_url=url, extracted_data=[])

        content_lower = content.lower()

        for data_type, pattern_list in self._patterns.items():
            for pattern, base_confidence in pattern_list:
                for match in pattern.finditer(content):
                    # Get matched value and context
                    value = match.group(1) if match.lastindex >= 1 else match.group(0)
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()

                    # Adjust confidence based on context
                    confidence = self._adjust_confidence(
                        base_confidence, data_type, content_lower, match
                    )

                    if confidence >= 0.5:  # Threshold for inclusion
                        extracted.append(ExtractedData(
                            data_type=data_type,
                            value=value.strip(),
                            confidence=confidence,
                            context=context,
                        ))

        # Deduplicate by data type (keep highest confidence)
        deduped = self._deduplicate(extracted)

        result = ExtractionResult(source_url=url, extracted_data=deduped)

        if deduped:
            logger.debug(
                f"Extracted {len(deduped)} data points from {url[:50]}... "
                f"-> sections: {result.sections_to_add}"
            )

        return result

    def _adjust_confidence(
        self,
        base_confidence: float,
        data_type: DataType,
        content_lower: str,
        match: re.Match,
    ) -> float:
        """Adjust confidence based on contextual signals."""
        confidence = base_confidence

        # Boost confidence if content mentions the company name near the match
        # (Would need company name passed in for this)

        # Reduce confidence for historical data (might be outdated)
        context_start = max(0, match.start() - 100)
        context = content_lower[context_start:match.end() + 100]

        if any(year in context for year in ['2018', '2019', '2020', '2021']):
            confidence *= 0.8  # Older data is less reliable

        # Boost for recent data
        if any(year in context for year in ['2024', '2025']):
            confidence *= 1.1

        # Reduce for projected/estimated values
        if any(word in context for word in ['projected', 'estimated', 'expected', 'forecast']):
            confidence *= 0.85

        return min(1.0, confidence)

    def _deduplicate(self, extracted: List[ExtractedData]) -> List[ExtractedData]:
        """Keep only the highest confidence extraction for each data type."""
        best_by_type: Dict[DataType, ExtractedData] = {}

        for data in extracted:
            existing = best_by_type.get(data.data_type)
            if existing is None or data.confidence > existing.confidence:
                best_by_type[data.data_type] = data

        return list(best_by_type.values())

    def get_additional_sections(
        self,
        content: str,
        current_section: str,
    ) -> Set[str]:
        """
        Get additional sections a source should be mapped to based on content.

        Args:
            content: Source content
            current_section: The section the source is already mapped to

        Returns:
            Set of additional section names to map this source to
        """
        result = self.extract("", content)
        additional = result.sections_to_add - {current_section}
        return additional


# Singleton instance
_extractor_instance: Optional[ContentDataExtractor] = None


def get_content_extractor() -> ContentDataExtractor:
    """Get the global content data extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = ContentDataExtractor()
    return _extractor_instance


def extract_data_types(url: str, content: str) -> ExtractionResult:
    """
    Convenience function to extract data types from content.

    Args:
        url: Source URL
        content: Text content

    Returns:
        ExtractionResult with extracted data and target sections
    """
    return get_content_extractor().extract(url, content)


__all__ = [
    "DataType",
    "ExtractedData",
    "ExtractionResult",
    "ContentDataExtractor",
    "get_content_extractor",
    "extract_data_types",
    "DATA_TYPE_TO_SECTIONS",
]
