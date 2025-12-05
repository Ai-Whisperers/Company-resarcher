"""
Validation framework for the Company Researcher.

Provides:
- Validators: Common validation functions
- URLValidator: URL validation
- DataGuard: Data validation and sanitization
- EntityValidator: Entity/company name validation (FIX-001)
"""

from .validators import *
from .url_validator import *
from .data_guard import *
from .evaluation import *
from .quality_thresholds import *
from .entity_validator import (
    EntityValidator,
    EntityMatch,
    create_entity_validator,
    COMPANY_DISAMBIGUATION,
)

__all__ = [
    "URLValidator",
    "DataGuard",
    "Evaluation",
    "QualityThresholds",
    # Entity validation (FIX-001)
    "EntityValidator",
    "EntityMatch",
    "create_entity_validator",
    "COMPANY_DISAMBIGUATION",
]
