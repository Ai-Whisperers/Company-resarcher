"""
Research-related core functionality.

Provides:
- ResearchPhases: Research phase management
- QueryGenerator: Query generation
- FollowUp: Follow-up question handling
- ComprehensiveQueries: Comprehensive query generation
- AdaptiveQueryStrategy: Adaptive query strategies
- PhaseSelector: Research phase selection
- CompetitorKnowledge: Pre-defined competitor data (FIX-004)
- QueryLocalizer: Country-specific query generation (FIX-006)
- EnhancedQueryGenerator: Improved queries (#21-28 improvements)
"""

from .research_phases import *
from .query_generator import *
from .follow_up import *
from .comprehensive_queries import *
from .adaptive_query_strategy import *
from .phase_selector import *
from .competitor_knowledge import (
    CompetitorKnowledge,
    CompetitorInfo,
    IndustryCompetitors,
    get_competitor_knowledge,
    PARAGUAY_TELECOM_COMPETITORS,
    INDUSTRY_COMPETITORS_BY_COUNTRY,
)
from .query_localizer import (
    QueryLocalizer,
    CountryConfig,
    Language,
    create_query_localizer,
    localize_queries_for_country,
    COUNTRY_CONFIGS,
    SPANISH_TRANSLATIONS,
)

# Enhanced query generation (#21-28 improvements)
from .enhanced_queries import (
    EnhancedQueryGenerator,
    QueryConfig,
    QueryType,
    generate_enhanced_queries,
    COUNTRY_REGULATORS,
    COUNTRY_DOMAINS,
    SPANISH_QUERY_TEMPLATES,
)
