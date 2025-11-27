import asyncio
from src.agents.sector_analyst import SectorAnalyst
from src.core.vault import VaultManager


async def main():
    print("Testing Sector Analyst...")

    # 1. Seed the Vault with some dummy data (if not already present)
    vault = VaultManager()
    await vault.store_report(
        "Company A", "Company A is a leader in AI.", {"industry": "AI"}
    )
    await vault.store_report(
        "Company B", "Company B focuses on AI hardware.", {"industry": "AI"}
    )
    await vault.store_report(
        "Company C", "Company C sells coffee.", {"industry": "Food"}
    )

    # 2. Run Sector Analyst
    analyst = SectorAnalyst()
    report = await analyst.analyze_sector("AI")

    print("\n--- SECTOR REPORT ---")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
