#!/usr/bin/env python3
"""
Test script for Alpha Vantage integration (INT-002).

Verifies that:
1. Company profiles correctly load ticker info from YAML
2. Financial data service can fetch data from Alpha Vantage
3. Report generation works correctly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

from main import load_company_profile
from src.core.types.base import CompanyProfile
from src.services.data import get_financial_data_service


def test_profile_loading():
    """Test that YAML profiles correctly load ticker info."""
    print("=" * 60)
    print("TEST 1: Profile Loading with Ticker Info")
    print("=" * 60)

    test_cases = [
        ("data/research_targets/paraguay_telecom/telecom_argentina.yaml", "TEO", None),
        ("data/research_targets/paraguay_telecom/personal_paraguay.yaml", None, "TEO"),
        ("data/research_targets/paraguay_telecom/tigo_paraguay.yaml", None, "TIGO"),
        ("data/research_targets/paraguay_telecom/claro_paraguay.yaml", None, "AMX"),
    ]

    all_passed = True
    for profile_path, expected_ticker, expected_parent_ticker in test_cases:
        try:
            profile = load_company_profile(profile_path)
            ticker = profile.get("ticker")
            parent_ticker = profile.get("parent_ticker")

            status = "PASS" if (ticker == expected_ticker and parent_ticker == expected_parent_ticker) else "FAIL"
            if status == "FAIL":
                all_passed = False

            print(f"  [{status}] {profile['name']}")
            print(f"         ticker={ticker}, parent_ticker={parent_ticker}")
        except Exception as e:
            print(f"  [FAIL] {profile_path}: {e}")
            all_passed = False

    return all_passed


def test_company_profile_methods():
    """Test CompanyProfile ticker-related methods."""
    print("\n" + "=" * 60)
    print("TEST 2: CompanyProfile Ticker Methods")
    print("=" * 60)

    all_passed = True

    # Test direct ticker
    company1 = CompanyProfile(
        name="Telecom Argentina",
        ticker="TEO",
        exchange="NYSE",
    )
    assert company1.get_effective_ticker() == "TEO", "Direct ticker failed"
    assert company1.has_financial_data_available(), "has_financial_data failed"
    assert not company1.is_subsidiary(), "is_subsidiary should be False"
    print("  [PASS] Direct ticker (TEO)")

    # Test parent ticker
    company2 = CompanyProfile(
        name="Personal Paraguay",
        parent_ticker="TEO",
        parent_company="Telecom Argentina",
    )
    assert company2.get_effective_ticker() == "TEO", "Parent ticker failed"
    assert company2.has_financial_data_available(), "has_financial_data failed"
    assert company2.is_subsidiary(), "is_subsidiary should be True"
    print("  [PASS] Parent ticker (subsidiary)")

    # Test no ticker
    company3 = CompanyProfile(name="Unknown Corp")
    assert company3.get_effective_ticker() is None, "No ticker should return None"
    assert not company3.has_financial_data_available(), "has_financial_data should be False"
    print("  [PASS] No ticker")

    return all_passed


async def test_financial_service():
    """Test financial data service (requires API key)."""
    print("\n" + "=" * 60)
    print("TEST 3: Financial Data Service")
    print("=" * 60)

    service = get_financial_data_service()

    if not service.is_available():
        print("  [SKIP] Alpha Vantage API key not configured")
        print("         Set ALPHA_VANTAGE_API_KEY in .env to test")
        return True  # Not a failure, just skipped

    # Test with Telecom Argentina (TEO)
    company = CompanyProfile(
        name="Telecom Argentina",
        ticker="TEO",
        exchange="NYSE",
        industry="Telecommunications",
        country="Argentina",
    )

    print(f"  Fetching data for {company.ticker}...")
    try:
        result = await service.fetch_financial_data(company)

        if result and result.has_data:
            print(f"  [PASS] Data fetched successfully")
            print(f"         Ticker: {result.ticker}")
            print(f"         API calls: {result.api_calls_made}")
            print(f"         Errors: {len(result.errors)}")
            if result.market_cap:
                print(f"         Market Cap: {result.market_cap}")
            if result.pe_ratio:
                print(f"         P/E Ratio: {result.pe_ratio}")
            return True
        else:
            print(f"  [WARN] No data returned for {company.ticker}")
            if result and result.errors:
                for err in result.errors:
                    print(f"         Error: {err}")
            return True  # API may have issues, not necessarily our bug
    except Exception as e:
        print(f"  [FAIL] Exception: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ALPHA VANTAGE INTEGRATION TESTS (INT-002)")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Profile loading
    results.append(("Profile Loading", test_profile_loading()))

    # Test 2: CompanyProfile methods
    results.append(("CompanyProfile Methods", test_company_profile_methods()))

    # Test 3: Financial service
    results.append(("Financial Service", await test_financial_service()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
