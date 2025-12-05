import sys

print("Starting debug...")
try:
    print("Importing SearchTool...")
    from src.tools.search.tool import SearchTool

    print("SearchTool imported.")
except Exception as e:
    print(f"Error importing SearchTool: {e}")
    import traceback

    traceback.print_exc()

print("Debug finished.")
