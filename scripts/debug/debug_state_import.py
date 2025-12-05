import sys
import os

sys.path.append(os.getcwd())

print("Importing src.domain.models.base...")
try:
    import src.domain.models.base

    print("Import src.domain.models.base successful.")
except Exception as e:
    print(f"Import src.domain.models.base failed: {e}")

print("Importing src.core.types...")
try:
    import src.core.types

    print("Import src.core.types successful.")
except Exception as e:
    print(f"Import src.core.types failed: {e}")
