import sys

print("Starting debug base...")
try:
    from src.tools.search.base import SearchProvider

    print("Base imported successfully.")
except Exception as e:
    print(f"Error importing base: {e}")
    import traceback

    traceback.print_exc()
