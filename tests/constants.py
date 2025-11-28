"""
Test constants and shared values.

This module provides centralized constants for tests, avoiding magic numbers
and hardcoded values scattered throughout the test suite.
"""

# =============================================================================
# URLs
# =============================================================================

# API URLs
TEST_API_BASE_URL = "http://testserver"
TEST_API_V1_URL = f"{TEST_API_BASE_URL}/api/v1"

# Company URLs for testing
TEST_COMPANY_URL = "https://testcorp.com"
TEST_COMPANY_ABOUT_URL = "https://testcorp.com/about"
TEST_COMPANY_CAREERS_URL = "https://testcorp.com/careers"

# Mock external service URLs
MOCK_SEARCH_URL = "https://api.search-mock.test/search"
MOCK_NEWS_URL = "https://api.news-mock.test/articles"
MOCK_FINANCE_URL = "https://api.finance-mock.test/quote"

# Example URLs for testing
EXAMPLE_URL = "https://example.com"
EXAMPLE_ARTICLE_URL = "https://example.com/article/123"
EXAMPLE_BLOG_URL = "https://blog.example.com/post/456"


# =============================================================================
# API Keys (Fake/Test)
# =============================================================================

# Use these in tests - never real API keys
TEST_OPENAI_API_KEY = "sk-test-fake-openai-key-12345"
TEST_ANTHROPIC_API_KEY = "sk-ant-test-fake-key-12345"
TEST_TAVILY_API_KEY = "tvly-test-fake-key-12345"
TEST_NEWSAPI_KEY = "test-newsapi-fake-key-12345"
TEST_GEMINI_API_KEY = "test-gemini-fake-key-12345"
TEST_GROQ_API_KEY = "test-groq-fake-key-12345"


# =============================================================================
# Timeouts (in seconds)
# =============================================================================

# Test execution timeouts
TEST_TIMEOUT_FAST = 5
TEST_TIMEOUT_MEDIUM = 30
TEST_TIMEOUT_SLOW = 120
TEST_TIMEOUT_E2E = 300

# Mock response delays
MOCK_RESPONSE_DELAY_FAST = 0.01
MOCK_RESPONSE_DELAY_MEDIUM = 0.1
MOCK_RESPONSE_DELAY_SLOW = 1.0


# =============================================================================
# Limits & Sizes
# =============================================================================

# Search/Results
TEST_MAX_SEARCH_RESULTS = 10
TEST_DEFAULT_PAGE_SIZE = 20
TEST_MAX_PAGE_SIZE = 100

# Content limits
TEST_MAX_CONTENT_LENGTH = 50000
TEST_MAX_TITLE_LENGTH = 500
TEST_MAX_URL_LENGTH = 2048

# Batch sizes
TEST_SMALL_BATCH = 5
TEST_MEDIUM_BATCH = 20
TEST_LARGE_BATCH = 100


# =============================================================================
# Default Test Data
# =============================================================================

# Default test company
DEFAULT_COMPANY_NAME = "Test Corp"
DEFAULT_COMPANY_WEBSITE = "https://testcorp.com"
DEFAULT_COMPANY_INDUSTRY = "Technology"
DEFAULT_COMPANY_COUNTRY = "USA"

# Default test ticker
DEFAULT_TICKER = "TEST"

# Default test user
DEFAULT_USER_EMAIL = "test@example.com"
DEFAULT_USER_NAME = "Test User"


# =============================================================================
# HTTP Status Codes
# =============================================================================

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE = 422
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503


# =============================================================================
# Content Types
# =============================================================================

CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_HTML = "text/html"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_PDF = "application/pdf"
CONTENT_TYPE_XML = "application/xml"


# =============================================================================
# Task States
# =============================================================================

TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
TASK_STATUS_CANCELLED = "cancelled"

ALL_TASK_STATUSES = [
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_CANCELLED,
]


# =============================================================================
# AI/LLM Constants
# =============================================================================

# Model names for testing
TEST_MODEL_GPT4 = "gpt-4"
TEST_MODEL_GPT35 = "gpt-3.5-turbo"
TEST_MODEL_CLAUDE = "claude-3-sonnet"
TEST_MODEL_GEMINI = "gemini-pro"

# Token limits
TEST_MAX_TOKENS = 4096
TEST_DEFAULT_TOKENS = 1024

# Temperature settings
TEST_TEMPERATURE_DETERMINISTIC = 0.0
TEST_TEMPERATURE_DEFAULT = 0.7
TEST_TEMPERATURE_CREATIVE = 1.0


# =============================================================================
# File Paths (Relative to test data directory)
# =============================================================================

SAMPLE_PDF_FILENAME = "sample.pdf"
SAMPLE_HTML_FILENAME = "sample.html"
SAMPLE_JSON_FILENAME = "sample.json"
SAMPLE_CSV_FILENAME = "sample.csv"


# =============================================================================
# Regex Patterns
# =============================================================================

# Validation patterns
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
URL_PATTERN = r"^https?://[^\s<>\"{}|\\^`\[\]]+$"
TICKER_PATTERN = r"^[A-Z]{1,5}$"
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"


# =============================================================================
# Error Messages
# =============================================================================

ERROR_NOT_FOUND = "Resource not found"
ERROR_UNAUTHORIZED = "Authentication required"
ERROR_FORBIDDEN = "Access denied"
ERROR_INVALID_INPUT = "Invalid input"
ERROR_RATE_LIMITED = "Rate limit exceeded"
ERROR_TIMEOUT = "Request timed out"
ERROR_SERVER = "Internal server error"


# =============================================================================
# Industries
# =============================================================================

TEST_INDUSTRIES = [
    "Technology",
    "Healthcare",
    "Finance",
    "Manufacturing",
    "Retail",
    "Energy",
    "Telecommunications",
    "Automotive",
]


# =============================================================================
# Countries
# =============================================================================

TEST_COUNTRIES = [
    "USA",
    "UK",
    "Germany",
    "France",
    "Japan",
    "China",
    "Canada",
    "Australia",
]


# =============================================================================
# Parallel Test Configuration
# =============================================================================

# Number of workers for parallel tests (0 = auto-detect)
PARALLEL_WORKERS = 0

# Tests that must run serially
SERIAL_TEST_MARKERS = ["serial", "e2e", "load"]
