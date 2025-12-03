"""
Test script for the three new research tools.

Run this script after installing dependencies:
    pip install yfinance newsapi-python

And adding your API keys to .env:
    NEWSAPI_KEY=your_key_here
"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.data.market.stock_data import FinancialDataTool
from src.tools.data.content.news_aggregator import NewsAggregatorTool
from src.tools.data.content.structured_extractor import StructuredExtractorTool


async def test_financial_tool():
    """Test the Financial Data Tool with real data."""
    print("\n" + "=" * 60)
    print("📊 TESTING FINANCIAL DATA TOOL")
    print("=" * 60)

    tool = FinancialDataTool()

    # Test with a well-known company
    ticker = "AAPL"
    print(f"\n🔍 Fetching data for ticker: {ticker}")

    data = await tool.get_company_info(ticker)

    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return False

    print(f"\n✅ Successfully fetched data!")
    print(f"Company: {data['basic_info']['name']}")
    print(f"Sector: {data['basic_info']['sector']}")
    print(f"Industry: {data['basic_info']['industry']}")

    if data["market_data"]["market_cap"]:
        market_cap = data["market_data"]["market_cap"]
        print(f"Market Cap: ${market_cap:,}")

    if data["employees"]:
        print(f"Employees: {data['employees']:,}")

    if data["financials"]["revenue"]:
        revenue = data["financials"]["revenue"]
        print(f"Revenue: ${revenue:,}")

    # Test ticker guessing
    print(f"\n🔍 Testing ticker guess for 'Microsoft'")
    guessed = tool.guess_ticker_from_name("Microsoft")
    print(f"Guessed ticker: {guessed}")

    return True


async def test_news_tool():
    """Test the News Aggregator Tool."""
    print("\n" + "=" * 60)
    print("📰 TESTING NEWS AGGREGATOR TOOL")
    print("=" * 60)

    tool = NewsAggregatorTool()

    if not tool.client:
        print("⚠️  NewsAPI client not initialized (missing NEWSAPI_KEY in .env)")
        print("Skipping news tool tests...")
        return False

    company = "Tesla"
    print(f"\n🔍 Fetching recent news for: {company}")

    # Get news articles
    news = await tool.get_company_news(company, days_back=7, max_results=5)

    if not news:
        print("❌ No news articles found")
        return False

    print(f"\n✅ Found {len(news)} articles!")
    for i, article in enumerate(news[:3], 1):
        print(f"\n{i}. {article.title}")
        print(f"   Source: {article.metadata.get('source_name', 'Unknown')}")
        print(f"   URL: {article.url[:60]}...")

    # Test signal detection
    print(f"\n🔍 Detecting signals for {company}...")
    signals = await tool.detect_signals(company, days_back=30)

    print(f"\n✅ Signal Detection Results:")
    print(f"   Total articles analyzed: {signals['total_articles']}")
    print(f"   Funding signals: {len(signals['funding'])}")
    print(f"   Partnerships: {len(signals['partnerships'])}")
    print(f"   Product launches: {len(signals['product_launches'])}")
    print(f"   Leadership changes: {len(signals['leadership_changes'])}")

    if signals["funding"]:
        print(f"\n💰 Recent funding news:")
        print(f"   {signals['funding'][0]['title']}")

    return True


async def test_structured_extractor():
    """Test the Structured Extractor Tool."""
    print("\n" + "=" * 60)
    print("🧠 TESTING STRUCTURED EXTRACTOR TOOL")
    print("=" * 60)

    tool = StructuredExtractorTool()

    # Test metric extraction
    sample_text = """
    Our platform has grown to 10 million active users with a 95% customer 
    satisfaction rate. Revenue increased by 150% year-over-year to $50 million. 
    We now serve customers in 30 countries and have a 99.9% uptime guarantee.
    Our team has grown to 200 employees.
    """

    print(f"\n🔍 Extracting metrics from sample text...")
    metrics = await tool.extract_key_metrics(sample_text)

    if not metrics:
        print("❌ No metrics extracted")
        return False

    print(f"\n✅ Extracted {len(metrics)} metrics!")
    for metric in metrics:
        print(f"   • {metric.metric_name}: {metric.value} {metric.unit or ''}")
        if metric.context:
            print(f"     Context: {metric.context}")

    # Test pricing extraction
    pricing_sample = """
    **Basic Plan** - $29/month
    - Up to 5 users
    - 10GB storage
    - Email support
    
    **Pro Plan (Most Popular)** - $99/month  
    - Up to 50 users
    - 100GB storage
    - Priority support
    - Advanced analytics
    
    **Enterprise** - Contact Sales
    - Unlimited users
    - Unlimited storage
    - Dedicated support
    - Custom integrations
    """

    print(f"\n🔍 Extracting pricing tiers...")
    tiers = await tool.extract_pricing(pricing_sample, "Example SaaS")

    if not tiers:
        print("❌ No pricing tiers extracted")
        return False

    print(f"\n✅ Extracted {len(tiers)} pricing tiers!")
    for tier in tiers:
        popular = " ⭐ POPULAR" if tier.is_popular else ""
        print(f"\n   {tier.name} - {tier.price}{popular}")
        print(f"   Features: {len(tier.features)}")
        for feature in tier.features[:3]:
            print(f"      • {feature}")

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 TESTING NEW RESEARCH TOOLS")
    print("=" * 60)

    results = {}

    # Test each tool
    results["financial"] = await test_financial_tool()
    results["news"] = await test_news_tool()
    results["extractor"] = await test_structured_extractor()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for tool_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{tool_name.title()}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Tools are ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check error messages above for details.")
        print("\nCommon issues:")
        print("1. NewsAPI tests require NEWSAPI_KEY in .env file")
        print("2. Structured extractor tests require a working AI client")
        print("3. Financial tool requires internet connection for yfinance")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
