import sys
import os

sys.path.append(os.getcwd())

print("Importing src.core.types.research_brief...")
try:
    import src.core.types.research_brief

    print("Import src.core.types.research_brief successful.")
except Exception as e:
    print(f"Import src.core.types.research_brief failed: {e}")

print("Importing src.core.types.base...")
try:
    import src.core.types.base

    print("Import src.core.types.base successful.")
except Exception as e:
    print(f"Import src.core.types.base failed: {e}")
