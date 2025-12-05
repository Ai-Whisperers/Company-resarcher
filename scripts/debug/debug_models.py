import sys
import os

sys.path.append(os.getcwd())

print("Importing src.domain.models.base...")
try:
    import src.domain.models.base

    print(f"File: {src.domain.models.base.__file__}")
    print(f"Dir: {dir(src.domain.models.base)}")
except Exception as e:
    print(f"Failed to import src.domain.models.base: {e}")
