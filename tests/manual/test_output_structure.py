import os
import shutil
from src.core.output_manager import OutputManager


def test_output_manager():
    print("Testing OutputManager...")

    company_name = "TestStructure"
    base_dir = "outputs_test"

    # Clean up previous test
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)

    manager = OutputManager(base_output_dir=base_dir)

    drafts = {
        "00-Strategic-Context/01-Overview.md": "# Overview\nContent",
        "01-Market-Intelligence/01-Size.md": "# Market Size\nContent",
        "01-Market-Intelligence/02-Trends.md": "# Trends\nContent",
        "99-Sources/Source-Log.md": "# Sources\nContent",
    }

    manager.save_research_output(company_name, drafts)

    # Verify
    expected_files = [
        f"{base_dir}/{company_name}/00-Strategic-Context/01-Overview.md",
        f"{base_dir}/{company_name}/01-Market-Intelligence/01-Size.md",
        f"{base_dir}/{company_name}/01-Market-Intelligence/02-Trends.md",
        f"{base_dir}/{company_name}/99-Sources/Source-Log.md",
    ]

    for f in expected_files:
        if os.path.exists(f):
            print(f"✅ Found {f}")
        else:
            print(f"❌ Missing {f}")


if __name__ == "__main__":
    test_output_manager()
