import sys
import os

sys.path.append(os.getcwd())


def test_import(module_name):
    try:
        print(f"Importing {module_name}...")
        __import__(module_name)
        print(f"Successfully imported {module_name}")
    except Exception as e:
        print(f"Failed to import {module_name}: {e}")


print("Starting import debug...")

# Core/Infrastructure imports
test_import("src.infrastructure.ai")
test_import("src.infrastructure.ai.langchain_models")
test_import("src.infrastructure.ai.wrappers")
test_import("src.infrastructure.ai.routing")

# Agents
test_import("src.agents.base_agent")
test_import("src.agents.specialists")
test_import("src.agents.writer")
test_import("src.agents.insight_generator")
test_import("src.agents.critic")

print("Debug complete.")
