"""
Services module - Contains all business logic services organized by domain.

Submodules:
- ai: AI/ML services (embeddings, query optimization, semantic caching)
- content: Content processing (compression, HTML caching, JSON parsing)
- data: Data management (caching, source tracking, crawling, metrics)
- quality: Quality assurance (fact verification, contradiction detection, scoring)
- research: Research execution (deep, incremental, iterative research)
- security: Security services (encryption, input sanitization)
"""

# AI Services
from .ai import (
    EmbeddingService,
    SemanticCache,
    QueryExpander,
    get_embedding_service,
    get_semantic_cache,
    generate_fallback_queries,
    simplify_query,
    extract_key_terms,
)

# Content Services
from .content import (
    ContextCompressor,
    HTMLCache,
    robust_json_parse,
    get_html_cache,
    reset_html_cache,
)

# Data Services
from .data import (
    PersistentSourceRegistry,
    SourceTracker,
    TrackedSource,
    SourceReprocessor,
    CrossCompanyReader,
    OfficialSiteCrawler,
    CacheService,
    FinancialDataService,
    MarketConsolidator,
    MetricsService,
    get_source_registry,
    get_source_tracker,
    reset_source_tracker,
    get_cross_company_reader,
    get_priority_paths_for_data,
    get_cache_service,
    reset_cache_service,
    get_financial_data_service,
    consolidate_from_batch,
    get_metrics_service,
)

# Quality Services
from .quality import (
    SourceQualityAssessor,
    SourceQualityScore,
    RecencyCategory,
    RecencyInfo,
    FactVerifier,
    VerificationResult,
    ContradictionDetector,
    Contradiction,
    ReportScorer,
    ReportScore,
    SectionScore,
    DimensionScore,
    GroundingService,
    GroundedClaim,
    get_quality_assessor,
    get_recency_category,
    get_recency_description,
    get_domain_authority_score,
    get_improvement_suggestions,
)

# Research Services
from .research import (
    DeepResearchService,
    IncrementalResearchService,
    IncrementalResearchResult,
    IterativeResearchService,
    IterativeResearchResult,
    GapAnalyzer,
    GapAnalysisResult,
    DataGap,
    FollowupGenerator,
    FollowupResult,
    FollowupQuestion,
    ExistingDataAnalyzer,
    CompanyDataAnalysis,
    EXTRACTION_PROMPTS,
    fill_market_gaps,
    generate_gap_report,
    get_followup_generator,
    get_data_analyzer,
)

# Security Services
from .security import (
    EncryptionService,
    get_encryption_service,
    sanitize_company_name,
    sanitize_for_prompt,
    sanitize_url,
    escape_for_prompt,
)

__all__ = [
    # AI - Classes
    "EmbeddingService",
    "SemanticCache",
    "QueryExpander",
    # AI - Functions
    "get_embedding_service",
    "get_semantic_cache",
    "generate_fallback_queries",
    "simplify_query",
    "extract_key_terms",
    # Content - Classes
    "ContextCompressor",
    "HTMLCache",
    # Content - Functions
    "robust_json_parse",
    "get_html_cache",
    "reset_html_cache",
    # Data - Classes
    "PersistentSourceRegistry",
    "SourceTracker",
    "TrackedSource",
    "SourceReprocessor",
    "CrossCompanyReader",
    "OfficialSiteCrawler",
    "CacheService",
    "FinancialDataService",
    "MarketConsolidator",
    "MetricsService",
    # Data - Functions
    "get_source_registry",
    "get_source_tracker",
    "reset_source_tracker",
    "get_cross_company_reader",
    "get_priority_paths_for_data",
    "get_cache_service",
    "reset_cache_service",
    "get_financial_data_service",
    "consolidate_from_batch",
    "get_metrics_service",
    # Quality - Classes
    "SourceQualityAssessor",
    "SourceQualityScore",
    "RecencyCategory",
    "RecencyInfo",
    "FactVerifier",
    "VerificationResult",
    "ContradictionDetector",
    "Contradiction",
    "ReportScorer",
    "ReportScore",
    "SectionScore",
    "DimensionScore",
    "GroundingService",
    "GroundedClaim",
    # Quality - Functions
    "get_quality_assessor",
    "get_recency_category",
    "get_recency_description",
    "get_domain_authority_score",
    "get_improvement_suggestions",
    # Research - Classes
    "DeepResearchService",
    "IncrementalResearchService",
    "IncrementalResearchResult",
    "IterativeResearchService",
    "IterativeResearchResult",
    "GapAnalyzer",
    "GapAnalysisResult",
    "DataGap",
    "FollowupGenerator",
    "FollowupResult",
    "FollowupQuestion",
    "ExistingDataAnalyzer",
    "CompanyDataAnalysis",
    # Research - Constants/Functions
    "EXTRACTION_PROMPTS",
    "fill_market_gaps",
    "generate_gap_report",
    "get_followup_generator",
    "get_data_analyzer",
    # Security - Classes
    "EncryptionService",
    # Security - Functions
    "get_encryption_service",
    "sanitize_company_name",
    "sanitize_for_prompt",
    "sanitize_url",
    "escape_for_prompt",
]
