import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    print("Importing src.agents.factory...")
    import src.agents.factory

    print("Successfully imported src.agents.factory")

    print("Importing src.pipeline.comprehensive_research...")
    import src.pipeline.comprehensive_research

    print("Successfully imported src.pipeline.comprehensive_research")

    print("Importing src.services.research.iterative...")
    import src.services.research.iterative

    print("Successfully imported src.services.research.iterative")

    print("All imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
