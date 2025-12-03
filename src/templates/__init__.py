"""
Templates package - Markdown templates for research report generation.

Folder structure:
- strategic_context/     - Company overview and strategic info
- market_intelligence/   - Market size, trends, regulations
- target_audience/       - ICP, personas, customer journey
- competitive_landscape/ - Competitors, pricing, market share
- brand_strategy/        - Positioning, messaging, brand voice
- marketing_execution/   - Channel strategy, content, funnels
- data_room/            - Financial data and statistics
- creative_inspiration/ - Visual style, ad examples, campaigns
- sales_intelligence/   - Sales strategy and analysis
- investment_analysis/  - Investment memos, social media analysis
- common/               - Shared base templates
- schemas/              - Pydantic models for report validation
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent

# Template path constants for easy reference
STRATEGIC_CONTEXT = TEMPLATES_DIR / "strategic_context"
MARKET_INTELLIGENCE = TEMPLATES_DIR / "market_intelligence"
TARGET_AUDIENCE = TEMPLATES_DIR / "target_audience"
COMPETITIVE_LANDSCAPE = TEMPLATES_DIR / "competitive_landscape"
BRAND_STRATEGY = TEMPLATES_DIR / "brand_strategy"
MARKETING_EXECUTION = TEMPLATES_DIR / "marketing_execution"
DATA_ROOM = TEMPLATES_DIR / "data_room"
CREATIVE_INSPIRATION = TEMPLATES_DIR / "creative_inspiration"
SALES_INTELLIGENCE = TEMPLATES_DIR / "sales_intelligence"
INVESTMENT_ANALYSIS = TEMPLATES_DIR / "investment_analysis"
COMMON = TEMPLATES_DIR / "common"
SCHEMAS = TEMPLATES_DIR / "schemas"
