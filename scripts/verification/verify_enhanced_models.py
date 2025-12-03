import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from src.core.models.base import (
    ContactInfo,
    Leadership,
    ProductService,
    RegulatoryCompliance,
    Infrastructure,
    Partnership,
    ESGData,
    CompanyHistory,
    TypedResearchContext,
    CompanyProfile,
    ResearchSource,
)
from src.services.research import DeepResearchService


async def verify_models():
    print("Verifying Data Models...")
    try:
        # Instantiate new models
        contact = ContactInfo(email_addresses=["test@example.com"])
        leadership = Leadership(executives=[{"name": "CEO", "title": "Chief Exec"}])
        product = ProductService(catalog=[{"name": "Product A"}])
        regulatory = RegulatoryCompliance(licenses=["License A"])
        infrastructure = Infrastructure(facilities=["Factory 1"])
        partnership = Partnership(strategic_partners=["Partner A"])
        esg = ESGData(sustainability_initiatives=["Green Energy"])
        history = CompanyHistory(founded_date="2020")

        print("✅ All new models instantiated successfully.")

        # Verify TypedResearchContext integration
        context = TypedResearchContext(
            financial_data={},
            market_data={},
            competitor_data={},
            brand_data={},
            contact=contact.model_dump(),
            leadership=leadership.model_dump(),
            products=product.model_dump(),
            regulatory=regulatory.model_dump(),
            infrastructure=infrastructure.model_dump(),
            partnerships=partnership.model_dump(),
            esg=esg.model_dump(),
            history=history.model_dump(),
        )
        print("✅ TypedResearchContext integration verified.")

    except Exception as e:
        print(f"❌ Model verification failed: {e}")
        return


async def verify_extraction():
    print("\nVerifying Extraction Prompts...")

    # Mock AI Client
    mock_ai_client = AsyncMock()
    mock_ai_client.generate.return_value = json.dumps(
        {
            "learnings": ["Learning 1", "Learning 2"],
            "entities": {"CEO": "John Doe"},
            "metrics": {"Revenue": "$1M"},
            "gaps": ["Gap 1"],
        }
    )

    service = DeepResearchService(ai_client=mock_ai_client)

    company = CompanyProfile(name="Test Corp", industry="Tech")
    sources = [
        ResearchSource(
            url="http://test.com", title="Test Source", content="Test Content"
        )
    ]

    try:
        # Test default extraction
        print("Testing 'default' extraction...")
        await service.extract_learnings(sources, company, "default")
        call_args = mock_ai_client.generate.call_args[0][0]
        if "Organizational Structure" in call_args:
            print("✅ Default prompt contains new sections.")
        else:
            print("❌ Default prompt missing new sections.")

        # Test specific extraction (e.g., market)
        print("Testing 'market' extraction...")
        await service.extract_learnings(sources, company, "market")
        call_args = mock_ai_client.generate.call_args[0][0]
        if "Regulatory environment" in call_args:
            print("✅ Market prompt contains specific fields.")
        else:
            print("❌ Market prompt missing specific fields.")

    except Exception as e:
        print(f"❌ Extraction verification failed: {e}")


if __name__ == "__main__":
    asyncio.run(verify_models())
    asyncio.run(verify_extraction())
