import sys

print("Starting debug imports...")

try:
    print("Importing src.core.config...")
    from src.core.config import get_settings

    print("src.core.config imported.")
except Exception as e:
    print(f"Error importing src.core.config: {e}")

try:
    print("Importing src.core.logging...")
    from src.core.logging import setup_logger

    print("src.core.logging imported.")
except Exception as e:
    print(f"Error importing src.core.logging: {e}")

try:
    print("Importing src.core.types.base...")
    from src.core.types.base import ResearchSource

    print("src.core.types.base imported.")
except Exception as e:
    print(f"Error importing src.core.types.base: {e}")

try:
    print("Importing src.domain.models.base...")
    from src.domain.models.base import SearchResults

    print("src.domain.models.base imported.")
except Exception as e:
    print(f"Error importing src.domain.models.base: {e}")

try:
    print("Importing src.tools.search.manager...")
    from src.tools.search.manager import SearchManager

    print("src.tools.search.manager imported.")
except Exception as e:
    print(f"Error importing src.tools.search.manager: {e}")

print("Debug imports finished.")
