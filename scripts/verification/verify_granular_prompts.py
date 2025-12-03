import asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.services.deep_research import DeepResearchService, EXTRACTION_PROMPTS
from src.core.types import CompanyProfile, ResearchSource


async def verify_granular_extraction():
    with open("verify_output.txt", "w") as f:
        f.write("Verifying Granular Extraction Prompts...\n")

        # Mock AI Client
        mock_ai_client = AsyncMock()
        mock_ai_client.generate.return_value = '{"learnings": ["Test learning"], "entities": {}, "metrics": {}, "gaps": []}'

        service = DeepResearchService(mock_ai_client)

        company = CompanyProfile(name="Test Corp", industry="Tech")
        sources = [
            ResearchSource(url="http://test.com", title="Test", content="Test content")
        ]

        research_types = [
            "market",
            "financial",
            "competitor",
            "brand",
            "sales",
            "unknown_type",
        ]

        for r_type in research_types:
            f.write(f"\nTesting research type: {r_type}\n")
            await service.extract_learnings(sources, company, r_type)

            # Verify the prompt used
            call_args = mock_ai_client.generate.call_args
            prompt_used = call_args[0][0]

            expected_template = EXTRACTION_PROMPTS.get(
                r_type, EXTRACTION_PROMPTS["default"]
            )
            expected_snippet = expected_template.split("\n")[0].format(
                company_name=company.name, industry=company.industry
            )

            if expected_snippet in prompt_used:
                f.write(f"✅ Correct prompt used for {r_type}\n")
            else:
                f.write(f"❌ Incorrect prompt used for {r_type}\n")
                f.write(f"Expected snippet: {expected_snippet}\n")
                f.write(f"Actual prompt start: {prompt_used[:100]}\n")


if __name__ == "__main__":
    asyncio.run(verify_granular_extraction())
