"""
LangFuse Setup Guide - Step-by-step helper script.

This script helps you:
1. Check if Docker is running
2. Start LangFuse containers
3. Test the connection
4. Get your API keys

Run: python langfuse_setup_guide.py
"""
import subprocess
import time
import sys
import os

def run_command(cmd, description=""):
    """Run a shell command and return success status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"  ✓ Success")
            return True, result.stdout
        else:
            print(f"  ✗ Failed: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, str(e)

def check_docker():
    """Check if Docker is installed and running."""
    print("="*60)
    print("Step 1: Checking Docker")
    print("="*60)

    success, output = run_command("docker --version", "Checking Docker installation")
    if not success:
        print("\n❌ Docker is not installed!")
        print("Download from: https://www.docker.com/products/docker-desktop")
        return False

    success, output = run_command("docker ps", "Checking if Docker is running")
    if not success:
        print("\n❌ Docker is not running!")
        print("Please start Docker Desktop and try again.")
        return False

    print("\n✓ Docker is ready!")
    return True

def start_langfuse():
    """Start LangFuse containers."""
    print("\n" + "="*60)
    print("Step 2: Starting LangFuse")
    print("="*60)

    # Check if already running
    success, output = run_command(
        "docker ps --filter name=langfuse",
        "Checking existing LangFuse containers"
    )

    if "langfuse" in output and "Up" in output:
        print("\n✓ LangFuse is already running!")
        return True

    # Start containers
    print("\nStarting LangFuse containers (this will take 2-3 minutes)...")
    print("Docker is downloading images...")

    cmd = "docker-compose -f docker-compose-langfuse.yml up -d"
    success, output = run_command(cmd, "Starting containers")

    if not success:
        print("\n❌ Failed to start LangFuse")
        print("Output:", output)
        return False

    # Wait for containers to be ready
    print("\nWaiting for containers to start...")
    for i in range(30):
        time.sleep(2)
        success, output = run_command(
            "docker ps --filter name=langfuse-app --filter status=running",
            f"Checking status ({i+1}/30)"
        )
        if success and "langfuse-app" in output:
            print("\n✓ LangFuse containers started!")
            return True

    print("\n⚠ Containers taking longer than expected...")
    print("Check status: docker ps")
    print("View logs: docker logs langfuse-app")
    return False

def check_langfuse_ready():
    """Check if LangFuse is accessible."""
    print("\n" + "="*60)
    print("Step 3: Checking LangFuse Web UI")
    print("="*60)

    print("\nWaiting for LangFuse to be ready...")
    for i in range(20):
        time.sleep(3)
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:3000", timeout=5)
            if response.status == 200:
                print(f"\n✓ LangFuse is ready at: http://localhost:3000")
                return True
        except:
            print(f"  Still starting... ({i+1}/20)")

    print("\n⚠ LangFuse may still be initializing")
    print("Try opening: http://localhost:3000 in your browser")
    return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n" + "="*60)
    print("Step 4: Setup Your Account")
    print("="*60)

    print("\nNext steps:")
    print("\n1. Open LangFuse in your browser:")
    print("   http://localhost:3000")

    print("\n2. Create your local account:")
    print("   - Email: your@email.com (any email)")
    print("   - Password: (your choice)")
    print("   - This is stored locally, not in the cloud!")

    print("\n3. Create a project:")
    print("   - Name: company-researcher")

    print("\n4. Get your API keys:")
    print("   - Go to Settings → API Keys")
    print("   - Click 'Create new secret key'")
    print("   - Copy the Public Key and Secret Key")

    print("\n5. Add to your .env file:")
    print("   LANGFUSE_PUBLIC_KEY=pk-lf-...")
    print("   LANGFUSE_SECRET_KEY=sk-lf-...")
    print("   LANGFUSE_HOST=http://localhost:3000")

    print("\n6. Test the integration:")
    print("   python test_langfuse_integration.py")

    print("\n" + "="*60)

def main():
    """Main setup process."""
    print("="*60)
    print("LangFuse Local Setup Guide")
    print("="*60)

    # Check Docker
    if not check_docker():
        sys.exit(1)

    # Start LangFuse
    if not start_langfuse():
        print("\n❌ Failed to start LangFuse")
        print("\nTroubleshooting:")
        print("1. Check Docker Desktop is running")
        print("2. Check port 3000 and 5432 are not in use")
        print("3. View logs: docker logs langfuse-app")
        sys.exit(1)

    # Check if ready
    check_langfuse_ready()

    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
