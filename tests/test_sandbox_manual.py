import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.sandbox import DockerSandbox

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("Starting Docker Sandbox Test...")
    sandbox = None

    try:
        # Initialize sandbox
        sandbox = DockerSandbox(image="python:3.10-slim")

        # Start container
        sandbox.start()

        # 1. Test Command Execution
        print("\nTest 1: Simple Command")
        exit_code, stdout, stderr = sandbox.execute("echo 'Hello from Sandbox'")
        print(f"Exit Code: {exit_code}")
        print(f"Stdout: {stdout.strip()}")
        print(f"Stderr: {stderr.strip()}")

        if exit_code == 0 and "Hello from Sandbox" in stdout:
            print("[PASS] Command Execution Passed")
        else:
            print("[FAIL] Command Execution Failed")

        # 2. Test File Copying and Execution
        print("\nTest 2: File Copy and Execution")
        python_script = """
print("Running Python inside Docker")
import os
print(f"Working Dir: {os.getcwd()}")
"""
        sandbox.copy_to_container(python_script, "/workspace/test_script.py")

        exit_code, stdout, stderr = sandbox.execute("python /workspace/test_script.py")
        print(f"Exit Code: {exit_code}")
        print(f"Stdout: {stdout.strip()}")
        print(f"Stderr: {stderr.strip()}")

        if exit_code == 0 and "Running Python inside Docker" in stdout:
            print("[PASS] File Copy & Execution Passed")
        else:
            print("[FAIL] File Copy & Execution Failed")

    except Exception as e:
        print(f"\n[FAIL] Test Failed with Exception: {e}")
    finally:
        # Cleanup
        print("\nCleaning up...")
        if sandbox:
            sandbox.stop()
        print("Done.")


if __name__ == "__main__":
    main()
