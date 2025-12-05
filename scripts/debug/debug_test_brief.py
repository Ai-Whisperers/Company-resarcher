import sys
import os

sys.path.append(os.getcwd())

print("Importing src.core.types.test_brief...")
try:
    import src.core.types.test_brief

    print("Import src.core.types.test_brief successful.")
except Exception as e:
    print(f"Import src.core.types.test_brief failed: {e}")
