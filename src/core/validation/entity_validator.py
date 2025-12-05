"""
Entity Validation - FIX-001: Validate that sources are about the correct company.

Prevents confusion between similarly named companies (e.g., Tigo Paraguay vs Tigo Energy).
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from src.core.logging import setup_logger

logger = setup_logger("entity_validator")


@dataclass
class EntityMatch:
    """Result of entity validation."""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    matched_entity: Optional[str]  # Which entity was detected
    rejection_reason: Optional[str]
    wrong_entity_detected: Optional[str]  # If we found a different company


# Known company disambiguation rules
# Maps company names to their identifying characteristics and exclusions
COMPANY_DISAMBIGUATION: Dict[str, Dict] = {
    # Tigo Paraguay (telecom) vs Tigo Energy (solar)
    "tigo paraguay": {
        "required_keywords": ["paraguay", "telecom", "millicom", "mobile", "celular", "telefon"],
        "exclude_keywords": ["solar", "energy", "photovoltaic", "inverter", "panel", "watt", "kwh", "pv system", "tigo energy", "tygo"],
        "exclude_domains": ["tigoenergy.com", "photovoltaikforum.com", "solarweb.com", "pvforum.de"],
        "country": "paraguay",
        "industry": "telecommunications",
    },
    # COPACO Paraguay (telecom) vs Copaco Belgium/Netherlands (IT distributor)
    "copaco": {
        "required_keywords": ["paraguay", "telecom", "comunicaciones", "vox", "copaco.com.py"],
        "exclude_keywords": ["belgium", "netherlands", "nederland", "distributor", "it distribution", "cloudchampion", "copaco.be", "copaco.nl"],
        "exclude_domains": ["copaco.be", "copaco.nl", "copaco.com", "cloudchampion.be", "werkenbijcopaco.com"],
        "country": "paraguay",
        "industry": "telecommunications",
    },
    # Claro Paraguay vs Claro in other countries
    "claro paraguay": {
        "required_keywords": ["paraguay"],
        "exclude_keywords": [],
        "exclude_domains": [],
        "country": "paraguay",
        "industry": "telecommunications",
    },
    # Personal Paraguay vs Personal Argentina
    "personal paraguay": {
        "required_keywords": ["paraguay", "núcleo"],
        "exclude_keywords": [],
        "exclude_domains": [],
        "country": "paraguay",
        "industry": "telecommunications",
    },
    # Vox Paraguay (MVNO) vs other Vox companies
    "vox paraguay": {
        "required_keywords": ["paraguay", "copaco", "mvno"],
        "exclude_keywords": ["vox media", "vox.com", "vox news", "vox eu", "vox populi"],
        "exclude_domains": ["vox.com", "voxmedia.com", "voxeu.org"],
        "country": "paraguay",
        "industry": "telecommunications",
    },
}


class EntityValidator:
    """
    Validates that sources are about the correct company entity.

    Prevents wrong-company contamination in research results.
    """

    # Minimum confidence to accept a source
    MIN_CONFIDENCE = 0.3

    # Strong negative indicators weight
    WRONG_ENTITY_PENALTY = -0.8

    def __init__(
        self,
        company_name: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        custom_exclude_keywords: Optional[List[str]] = None,
        custom_exclude_domains: Optional[List[str]] = None,
    ):
        """
        Initialize entity validator.

        Args:
            company_name: Target company name
            country: Target country (for disambiguation)
            industry: Target industry (for disambiguation)
            custom_exclude_keywords: Additional keywords to exclude
            custom_exclude_domains: Additional domains to exclude
        """
        self.company_name = company_name.lower().strip()
        self.country = country.lower() if country else None
        self.industry = industry.lower() if industry else None

        # Load disambiguation rules if available
        self.rules = self._load_rules()

        # Add custom exclusions
        self.exclude_keywords: Set[str] = set(self.rules.get("exclude_keywords", []))
        self.exclude_domains: Set[str] = set(self.rules.get("exclude_domains", []))
        self.required_keywords: Set[str] = set(self.rules.get("required_keywords", []))

        if custom_exclude_keywords:
            self.exclude_keywords.update(kw.lower() for kw in custom_exclude_keywords)
        if custom_exclude_domains:
            self.exclude_domains.update(d.lower() for d in custom_exclude_domains)

        logger.info(
            f"Entity validator initialized: company='{company_name}', "
            f"excludes={len(self.exclude_keywords)} keywords, {len(self.exclude_domains)} domains"
        )

    def _load_rules(self) -> Dict:
        """Load disambiguation rules for the company."""
        # Try exact match first
        if self.company_name in COMPANY_DISAMBIGUATION:
            return COMPANY_DISAMBIGUATION[self.company_name]

        # Try partial match
        for name, rules in COMPANY_DISAMBIGUATION.items():
            if name in self.company_name or self.company_name in name:
                return rules

        # Return empty rules if no match
        return {}

    def validate(
        self,
        url: str,
        title: str,
        content: str,
    ) -> EntityMatch:
        """
        Validate that a source is about the correct company.

        Args:
            url: Source URL
            title: Source title
            content: Source content (snippet or full text)

        Returns:
            EntityMatch with validation result
        """
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        combined = f"{title_lower} {content_lower}"

        # Extract domain
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = ""

        confidence = 0.5  # Start neutral
        wrong_entity = None
        rejection_reason = None

        # Check for excluded domains (highest priority)
        for excluded in self.exclude_domains:
            if excluded in domain or excluded in url_lower:
                wrong_entity = f"Wrong domain: {excluded}"
                rejection_reason = f"Source from excluded domain: {excluded}"
                return EntityMatch(
                    is_valid=False,
                    confidence=0.0,
                    matched_entity=None,
                    rejection_reason=rejection_reason,
                    wrong_entity_detected=wrong_entity,
                )

        # Check for excluded keywords (strong negative signal)
        excluded_found = []
        for keyword in self.exclude_keywords:
            if keyword in combined:
                excluded_found.append(keyword)

        if excluded_found:
            # Check if this is clearly about a different entity
            wrong_entity = f"Wrong entity keywords: {', '.join(excluded_found[:3])}"
            confidence -= self.WRONG_ENTITY_PENALTY * (len(excluded_found) / max(len(self.exclude_keywords), 1))
            confidence = max(0.0, confidence)

            if confidence < self.MIN_CONFIDENCE:
                rejection_reason = f"Contains excluded keywords: {', '.join(excluded_found[:3])}"
                logger.debug(f"Entity rejected: {url[:60]} - {rejection_reason}")
                return EntityMatch(
                    is_valid=False,
                    confidence=confidence,
                    matched_entity=None,
                    rejection_reason=rejection_reason,
                    wrong_entity_detected=wrong_entity,
                )

        # Check for required keywords (positive signal)
        required_found = []
        for keyword in self.required_keywords:
            if keyword in combined:
                required_found.append(keyword)

        if required_found:
            # Boost confidence for each required keyword found
            confidence += 0.1 * len(required_found)
            confidence = min(1.0, confidence)

        # Check if company name is present
        if self.company_name in combined:
            confidence += 0.2
        else:
            # Check for partial name match
            name_parts = self.company_name.split()
            matches = sum(1 for part in name_parts if len(part) > 3 and part in combined)
            if matches > 0:
                confidence += 0.1 * (matches / len(name_parts))
            else:
                confidence -= 0.2  # Company name not found at all

        # Check country match
        if self.country and self.country in combined:
            confidence += 0.15

        confidence = max(0.0, min(1.0, confidence))

        is_valid = confidence >= self.MIN_CONFIDENCE and not excluded_found

        if not is_valid and not rejection_reason:
            rejection_reason = f"Low entity confidence: {confidence:.2f}"

        return EntityMatch(
            is_valid=is_valid,
            confidence=confidence,
            matched_entity=self.company_name if is_valid else None,
            rejection_reason=rejection_reason,
            wrong_entity_detected=wrong_entity,
        )

    def filter_sources(
        self,
        sources: List[Dict],
        log_rejections: bool = True,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter sources to keep only those about the correct company.

        Args:
            sources: List of source dicts with url, title, content/snippet
            log_rejections: Whether to log rejected sources

        Returns:
            Tuple of (valid_sources, rejected_sources)
        """
        valid = []
        rejected = []

        for source in sources:
            url = source.get("url", "")
            title = source.get("title", "")
            content = source.get("content", source.get("snippet", ""))

            result = self.validate(url, title, content)

            if result.is_valid:
                source["_entity_confidence"] = result.confidence
                valid.append(source)
            else:
                source["_rejection_reason"] = result.rejection_reason
                source["_wrong_entity"] = result.wrong_entity_detected
                rejected.append(source)

                if log_rejections:
                    logger.info(
                        f"Entity filter rejected: {url[:60]}... "
                        f"reason='{result.rejection_reason}'"
                    )

        logger.info(
            f"Entity validation: {len(valid)}/{len(sources)} sources valid "
            f"(rejected {len(rejected)} as wrong entity)"
        )

        return valid, rejected


def create_entity_validator(
    company_name: str,
    country: Optional[str] = None,
    industry: Optional[str] = None,
) -> EntityValidator:
    """Factory function to create an entity validator."""
    return EntityValidator(
        company_name=company_name,
        country=country,
        industry=industry,
    )


# Common wrong-entity patterns for telecom industry
TELECOM_WRONG_ENTITY_PATTERNS = {
    "tigo": {
        "wrong_entities": [
            ("tigo energy", ["solar", "inverter", "photovoltaic", "panel", "energy"]),
            ("tigo sports", ["deportes", "futbol", "football"]),  # This is actually OK for Tigo
        ],
    },
    "claro": {
        "wrong_entities": [
            ("claro (adjective)", ["clearly", "obviously", "of course"]),
        ],
    },
}
