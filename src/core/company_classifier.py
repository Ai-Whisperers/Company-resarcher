"""
Company Classifier - FE-008: Automatic company type detection.

Detects company characteristics (public/private, startup/enterprise,
industry vertical, geography) to adapt research phases and data sources.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

from ..core.logger import setup_logger


logger = setup_logger("company_classifier")


class OwnershipType(str, Enum):
    """Company ownership classification."""
    PUBLIC = "public"
    PRIVATE = "private"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    UNKNOWN = "unknown"


class CompanyStage(str, Enum):
    """Company growth stage."""
    STARTUP = "startup"       # Early stage, <50 employees
    GROWTH = "growth"         # Scaling, 50-500 employees
    MATURE = "mature"         # Established, 500-5000 employees
    ENTERPRISE = "enterprise" # Large, >5000 employees
    UNKNOWN = "unknown"


class CompanySize(str, Enum):
    """Company size classification."""
    SMALL = "small"           # <50 employees
    MEDIUM = "medium"         # 50-250 employees
    LARGE = "large"           # 250-1000 employees
    ENTERPRISE = "enterprise" # >1000 employees
    UNKNOWN = "unknown"


@dataclass
class CompanyClassification:
    """
    Classification results for a company.

    Used to determine appropriate research phases, data sources,
    and output structure.
    """
    ownership: OwnershipType = OwnershipType.UNKNOWN
    stage: CompanyStage = CompanyStage.UNKNOWN
    size: CompanySize = CompanySize.UNKNOWN
    industry_vertical: str = "unknown"
    geography: str = "unknown"
    has_funding: bool = False
    is_b2b: bool = True  # Default to B2B
    is_tech: bool = False
    confidence: float = 0.0

    # Additional signals detected
    detected_signals: List[str] = field(default_factory=list)
    stock_ticker: Optional[str] = None
    parent_company: Optional[str] = None
    headquarters_country: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ownership": self.ownership.value,
            "stage": self.stage.value,
            "size": self.size.value,
            "industry_vertical": self.industry_vertical,
            "geography": self.geography,
            "has_funding": self.has_funding,
            "is_b2b": self.is_b2b,
            "is_tech": self.is_tech,
            "confidence": self.confidence,
            "detected_signals": self.detected_signals,
            "stock_ticker": self.stock_ticker,
            "parent_company": self.parent_company,
            "headquarters_country": self.headquarters_country,
        }

    def get_profile_key(self) -> str:
        """Get the profile key for phase selection."""
        if self.ownership == OwnershipType.PUBLIC:
            return f"public_{self.stage.value}"
        elif self.has_funding:
            return "venture_backed_startup"
        elif self.ownership == OwnershipType.GOVERNMENT:
            return "government"
        elif self.ownership == OwnershipType.NONPROFIT:
            return "nonprofit"
        elif self.size in (CompanySize.SMALL, CompanySize.MEDIUM):
            return "private_smb"
        else:
            return "private_enterprise"


class CompanyClassifier:
    """
    Classifier for detecting company characteristics.

    Uses heuristics and patterns to classify companies based on
    name, website, and initial research signals.
    """

    # Known public company indicators
    PUBLIC_INDICATORS = [
        r"nasdaq[:\s]",
        r"nyse[:\s]",
        r"stock\s+symbol",
        r"ticker[:\s]",
        r"sec\s+filing",
        r"10-k\s+report",
        r"quarterly\s+earnings",
        r"shareholder",
        r"publicly\s+traded",
        r"ipo\s+",
        r"market\s+cap",
    ]

    # Startup/VC indicators
    STARTUP_INDICATORS = [
        r"series\s+[a-d]",
        r"seed\s+round",
        r"funding\s+round",
        r"raised\s+\$",
        r"venture\s+capital",
        r"backed\s+by",
        r"accelerator",
        r"incubator",
        r"y\s+combinator",
        r"techstars",
    ]

    # B2B indicators
    B2B_INDICATORS = [
        r"enterprise",
        r"b2b",
        r"business\s+solution",
        r"saas",
        r"platform\s+for\s+businesses",
        r"corporate",
        r"wholesale",
    ]

    # B2C indicators
    B2C_INDICATORS = [
        r"consumer",
        r"b2c",
        r"retail",
        r"shopping",
        r"e-commerce",
        r"personal\s+use",
        r"individual",
    ]

    # Tech company indicators
    TECH_INDICATORS = [
        r"software",
        r"technology",
        r"tech",
        r"digital",
        r"platform",
        r"saas",
        r"cloud",
        r"ai\s",
        r"machine\s+learning",
        r"app\s+",
        r"api\s",
    ]

    # Industry vertical patterns
    INDUSTRY_PATTERNS = {
        "telecommunications": [r"telecom", r"mobile\s+operator", r"carrier", r"network\s+provider", r"cellular"],
        "fintech": [r"fintech", r"financial\s+technology", r"payment", r"banking\s+app", r"digital\s+bank"],
        "saas": [r"saas", r"software\s+as\s+a\s+service", r"cloud\s+platform", r"subscription\s+software"],
        "retail": [r"retail", r"store", r"shop", r"e-commerce", r"ecommerce"],
        "healthcare": [r"health", r"medical", r"hospital", r"clinic", r"pharma"],
        "manufacturing": [r"manufacturing", r"factory", r"production", r"industrial"],
        "energy": [r"energy", r"oil", r"gas", r"renewable", r"solar", r"wind"],
        "real_estate": [r"real\s+estate", r"property", r"construction", r"building"],
        "transportation": [r"transport", r"logistics", r"shipping", r"delivery"],
        "education": [r"education", r"university", r"school", r"learning", r"edtech"],
    }

    # Geography patterns
    GEOGRAPHY_PATTERNS = {
        "US": [r"\.com$", r"usa", r"united\s+states", r"america"],
        "LATAM": [r"\.ar$", r"\.br$", r"\.mx$", r"\.co$", r"\.cl$", r"\.pe$", r"latin\s+america"],
        "Paraguay": [r"\.py$", r"paraguay", r"asuncion"],
        "EU": [r"\.eu$", r"\.de$", r"\.fr$", r"\.uk$", r"europe"],
        "APAC": [r"\.cn$", r"\.jp$", r"\.kr$", r"\.au$", r"asia"],
    }

    def classify(
        self,
        name: str,
        website: Optional[str] = None,
        description: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        initial_content: Optional[str] = None,
    ) -> CompanyClassification:
        """
        Classify a company based on available information.

        Args:
            name: Company name
            website: Company website URL
            description: Company description
            country: Company country
            industry: Known industry (if any)
            initial_content: Initial research content for signal detection

        Returns:
            CompanyClassification with detected characteristics
        """
        classification = CompanyClassification()
        signals = []
        confidence_factors = []

        # Combine all text for pattern matching
        combined_text = " ".join(filter(None, [
            name.lower(),
            website.lower() if website else "",
            description.lower() if description else "",
            initial_content.lower() if initial_content else "",
        ]))

        # Detect ownership type
        if self._matches_patterns(combined_text, self.PUBLIC_INDICATORS):
            classification.ownership = OwnershipType.PUBLIC
            signals.append("public_company_signals")
            confidence_factors.append(0.8)
        elif self._matches_patterns(combined_text, self.STARTUP_INDICATORS):
            classification.ownership = OwnershipType.PRIVATE
            classification.has_funding = True
            signals.append("venture_backed_signals")
            confidence_factors.append(0.7)
        else:
            classification.ownership = OwnershipType.PRIVATE

        # Detect B2B vs B2C
        b2b_score = self._count_pattern_matches(combined_text, self.B2B_INDICATORS)
        b2c_score = self._count_pattern_matches(combined_text, self.B2C_INDICATORS)
        classification.is_b2b = b2b_score >= b2c_score

        # Detect tech company
        if self._matches_patterns(combined_text, self.TECH_INDICATORS):
            classification.is_tech = True
            signals.append("tech_company_signals")

        # Detect industry vertical
        if industry:
            classification.industry_vertical = industry.lower()
            confidence_factors.append(0.9)
        else:
            detected_industry = self._detect_industry(combined_text)
            if detected_industry:
                classification.industry_vertical = detected_industry
                signals.append(f"detected_industry:{detected_industry}")
                confidence_factors.append(0.6)

        # Detect geography
        if country:
            classification.geography = self._normalize_geography(country)
            classification.headquarters_country = country
            confidence_factors.append(0.9)
        else:
            detected_geo = self._detect_geography(website or "", combined_text)
            if detected_geo:
                classification.geography = detected_geo
                signals.append(f"detected_geography:{detected_geo}")
                confidence_factors.append(0.5)

        # Estimate stage/size based on signals
        if classification.has_funding:
            classification.stage = CompanyStage.STARTUP
            classification.size = CompanySize.SMALL
        elif classification.ownership == OwnershipType.PUBLIC:
            classification.stage = CompanyStage.MATURE
            classification.size = CompanySize.LARGE

        # Calculate confidence
        if confidence_factors:
            classification.confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            classification.confidence = 0.3  # Low confidence without signals

        classification.detected_signals = signals

        logger.info(
            f"Classified {name}: {classification.ownership.value}, "
            f"{classification.stage.value}, {classification.industry_vertical}, "
            f"confidence={classification.confidence:.2f}"
        )

        return classification

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _count_pattern_matches(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match the text."""
        count = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                count += 1
        return count

    def _detect_industry(self, text: str) -> Optional[str]:
        """Detect industry vertical from text."""
        best_match = None
        best_count = 0

        for industry, patterns in self.INDUSTRY_PATTERNS.items():
            count = self._count_pattern_matches(text, patterns)
            if count > best_count:
                best_count = count
                best_match = industry

        return best_match if best_count >= 2 else None

    def _detect_geography(self, website: str, text: str) -> Optional[str]:
        """Detect geography from website TLD and text."""
        combined = website + " " + text

        for geo, patterns in self.GEOGRAPHY_PATTERNS.items():
            if self._matches_patterns(combined, patterns):
                return geo

        return None

    def _normalize_geography(self, country: str) -> str:
        """Normalize country name to region."""
        country_lower = country.lower()

        # Direct country mappings
        mappings = {
            "paraguay": "Paraguay",
            "argentina": "LATAM",
            "brazil": "LATAM",
            "mexico": "LATAM",
            "colombia": "LATAM",
            "chile": "LATAM",
            "peru": "LATAM",
            "united states": "US",
            "usa": "US",
            "germany": "EU",
            "france": "EU",
            "uk": "EU",
            "united kingdom": "EU",
            "china": "APAC",
            "japan": "APAC",
            "australia": "APAC",
        }

        return mappings.get(country_lower, country)


# Singleton instance
_classifier: Optional[CompanyClassifier] = None


def get_company_classifier() -> CompanyClassifier:
    """Get singleton company classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = CompanyClassifier()
    return _classifier
