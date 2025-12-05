import sys
import sys
import os

sys.path.append(os.getcwd())

print("Importing ResearchGraphBuilder...")
try:
    import src.graph.state

    print("Import src.graph.state successful.")
    # import src.graph
    # from src.graph.graph_builder import ResearchGraphBuilder

    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")
