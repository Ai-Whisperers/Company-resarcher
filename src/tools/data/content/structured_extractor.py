from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.infrastructure.ai import get_ai_manager
from src.core.logging import setup_logger
from src.infrastructure.content import robust_json_parse

logger = setup_logger("structured_extractor")


class PricingTier(BaseModel):
    """Structured pricing tier data."""

    name: str = Field(description="Tier name (e.g., 'Basic', 'Pro', 'Enterprise')")
    price: Optional[str] = Field(
        description="Price (e.g., '$99/month' or 'Contact Sales')"
    )
    features: List[str] = Field(description="List of features included in this tier")
    is_popular: bool = Field(
        default=False, description="Is this the recommended/most popular tier?"
    )


class Metric(BaseModel):
    """Structured metric data."""

    metric_name: str = Field(description="What is being measured")
    value: str = Field(description="The numeric value")
    unit: Optional[str] = Field(description="Unit of measurement (%, $, users, etc.)")
    context: Optional[str] = Field(
        description="Brief context about what this metric means"
    )


class StructuredExtractorTool:
    """
    Extract structured data from unstructured text using LLM function calling.
    Converts messy web content into clean, queryable data structures.
    """

    def __init__(self, ai_client=None):
        """
        Initialize the structured extractor.

        Args:
            ai_client: Optional AI client. If None, uses the global AI manager.
        """
        self.ai = ai_client if ai_client else get_ai_manager()

    async def extract_pricing(
        self, content: str, company_name: str
    ) -> List[PricingTier]:
        """
        Extract pricing tiers from a pricing page or content.

        Args:
            content: Raw HTML or text from pricing page
            company_name: Name of company (for context)

        Returns:
            List of structured PricingTier objects
        """
        prompt = f"""
Extract ALL pricing information from the following content for {company_name}.

Return a JSON array of pricing tiers. For each tier, extract:
- name: The tier/plan name (e.g., "Basic", "Pro", "Enterprise")
- price: The cost with currency and billing period (e.g., "$99/month", "Contact Sales")
- features: Array of key features included in this tier
- is_popular: true if this tier is marked as "Most Popular", "Recommended", or "Best Value"

If pricing is not clearly stated, use "Contact Sales" or "Custom" for the price field.

Content:
{content[:5000]}

IMPORTANT: Return ONLY a valid JSON array with no additional text, explanations, or markdown formatting.
Format: [{{ "name": "...", "price": "...", "features": [...], "is_popular": false }}, ...]
"""

        try:
            response = await self.ai.generate(prompt, response_format="json")

            # Parse JSON response
            tiers_data = robust_json_parse(response)

            # Ensure it's a list
            if isinstance(tiers_data, dict):
                tiers_data = tiers_data.get("tiers", [])

            # Convert to Pydantic models for validation
            tiers = [PricingTier(**tier) for tier in tiers_data]

            logger.info(f"Extracted {len(tiers)} pricing tiers for {company_name}")
            return tiers

        except Exception as e:
            logger.error(f"Failed to extract pricing for {company_name}: {str(e)}")
            return []

    async def extract_key_metrics(self, text: str) -> List[Metric]:
        """
        Extract key numbers, percentages, and metrics from text.

        Args:
            text: Text content to analyze (reports, articles, etc.)

        Returns:
            List of structured Metric objects
        """
        prompt = f"""
Extract ALL key metrics, statistics, and quantifiable data from the following text.

For each metric, extract:
- metric_name: Clear description of what is being measured
- value: The numeric value (preserve as string to maintain formatting)
- unit: The unit of measurement (%, $, million, users, customers, etc.)
- context: Brief explanation of what this metric represents

Examples:
- "revenue grew 150% to $50M" → {{ "metric_name": "Revenue Growth", "value": "150", "unit": "%", "context": "Year-over-year revenue increase" }}
- "10 million active users" → {{ "metric_name": "Active Users", "value": "10", "unit": "million users", "context": "Total active user base" }}

Text:
{text[:3000]}

IMPORTANT: Return ONLY a valid JSON array with no additional text.
Format: [{{ "metric_name": "...", "value": "...", "unit": "...", "context": "..." }}, ...]
"""

        try:
            response = await self.ai.generate(prompt, response_format="json")

            # Parse JSON response
            data = robust_json_parse(response)

            # Handle different response formats
            if isinstance(data, dict):
                metrics_data = data.get("metrics", [])
            else:
                metrics_data = data

            # Convert to Pydantic models
            metrics = [Metric(**metric) for metric in metrics_data]

            logger.info(f"Extracted {len(metrics)} metrics from text")
            return metrics

        except Exception as e:
            logger.error(f"Failed to extract metrics: {str(e)}")
            return []

    async def extract_product_features(
        self, content: str, product_name: str
    ) -> Dict[str, Any]:
        """
        Extract product features from a product page or description.

        Args:
            content: Product page content or description
            product_name: Name of the product

        Returns:
            Dictionary with categorized features
        """
        prompt = f"""
Extract product features from the following content for {product_name}.

Categorize features into:
- core_features: Main functionality
- integrations: Third-party integrations and APIs
- security: Security and compliance features
- support: Support and training options
- platforms: Supported platforms (web, mobile, desktop, etc.)

Return JSON format:
{{
  "product_name": "{product_name}",
  "core_features": ["feature 1", "feature 2"],
  "integrations": ["integration 1", "integration 2"],
  "security": ["security feature 1"],
  "support": ["support option 1"],
  "platforms": ["platform 1"]
}}

Content:
{content[:4000]}

Return ONLY valid JSON with no additional text.
"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            data = robust_json_parse(response)

            logger.info(
                f"Extracted {len(data.get('core_features', []))} core features for {product_name}"
            )
            return data

        except Exception as e:
            logger.error(f"Failed to extract product features: {str(e)}")
            return {
                "product_name": product_name,
                "core_features": [],
                "integrations": [],
                "security": [],
                "support": [],
                "platforms": [],
                "error": str(e),
            }

    async def extract_contact_info(self, content: str) -> Dict[str, Any]:
        """
        Extract contact information from text.

        Args:
            content: Text content (about page, footer, etc.)

        Returns:
            Dictionary with contact details
        """
        prompt = f"""
Extract contact information from the following content.

Return JSON with:
- email: Email address(es)
- phone: Phone number(s)
- address: Physical address
- social_media: Social media links (LinkedIn, Twitter, etc.)

Content:
{content[:2000]}

Return ONLY valid JSON.
"""

        try:
            response = await self.ai.generate(prompt, response_format="json")
            data = robust_json_parse(response)

            logger.info("Extracted contact information")
            return data

        except Exception as e:
            logger.error(f"Failed to extract contact info: {str(e)}")
            return {"error": str(e)}
