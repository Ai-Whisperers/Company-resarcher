import sys
import os

print("Importing pydantic...")
try:
    from pydantic import BaseModel, Field

    print("Import pydantic successful.")
except Exception as e:
    print(f"Import pydantic failed: {e}")
