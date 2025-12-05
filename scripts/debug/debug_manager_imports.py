import sys

print("Starting debug manager imports...")

try:
    print("Importing .base...")
    from src.tools.search.base import SearchProvider

    print(".base imported.")
except Exception as e:
    print(f"Error importing .base: {e}")

try:
    print("Importing .providers.duckduckgo...")
    from src.tools.search.providers.duckduckgo import DuckDuckGoProvider

    print(".providers.duckduckgo imported.")
except Exception as e:
    print(f"Error importing .providers.duckduckgo: {e}")

try:
    print("Importing .providers.jina...")
    from src.tools.search.providers.jina import JinaSearchProvider

    print(".providers.jina imported.")
except Exception as e:
    print(f"Error importing .providers.jina: {e}")

try:
    print("Importing .providers.langsearch...")
    from src.tools.search.providers.langsearch import LangSearchProvider

    print(".providers.langsearch imported.")
except Exception as e:
    print(f"Error importing .providers.langsearch: {e}")

try:
    print("Importing .providers.serper...")
    from src.tools.search.providers.serper import SerperProvider

    print(".providers.serper imported.")
except Exception as e:
    print(f"Error importing .providers.serper: {e}")

try:
    print("Importing .providers.tavily_provider...")
    from src.tools.search.providers.tavily_provider import TavilyProvider

    print(".providers.tavily_provider imported.")
except Exception as e:
    print(f"Error importing .providers.tavily_provider: {e}")

try:
    print("Importing .providers.brave...")
    from src.tools.search.providers.brave import BraveSearchProvider

    print(".providers.brave imported.")
except Exception as e:
    print(f"Error importing .providers.brave: {e}")

try:
    print("Importing .providers.bing...")
    from src.tools.search.providers.bing import BingSearchProvider

    print(".providers.bing imported.")
except Exception as e:
    print(f"Error importing .providers.bing: {e}")

try:
    print("Importing ...core.resilience.rate_limiting...")
    from src.core.resilience.rate_limiting import rate_limiter_manager

    print("...core.resilience.rate_limiting imported.")
except Exception as e:
    print(f"Error importing ...core.resilience.rate_limiting: {e}")

print("Debug manager imports finished.")
