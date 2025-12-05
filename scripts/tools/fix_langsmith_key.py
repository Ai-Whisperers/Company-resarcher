"""
Fix LangSmith API key to use project key instead of service key.

This enables professional tracing without workspace requirements.
"""
import os
from pathlib import Path

# Your project key (free tier, 5,000 traces/month)
PROJECT_KEY = "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"

# Old service key patterns to replace
OLD_KEYS = [
    "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",
    "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"
]

def fix_env_file():
    """Update .env file with project key."""
    env_path = Path(".env")

    if not env_path.exists():
        print("ERROR: .env file not found")
        return False

    # Read current content
    content = env_path.read_text()
    print("Current .env content (API keys):")
    print("=" * 60)
    for line in content.split("\n"):
        if "LANGCHAIN" in line:
            print(f"  {line}")
    print("=" * 60)

    # Replace old keys with project key
    updated = content
    for old_key in OLD_KEYS:
        if old_key in updated:
            updated = updated.replace(old_key, PROJECT_KEY)
            print(f"\nReplacing service key with project key...")

    # Write updated content
    if updated != content:
        # Backup first
        backup_path = env_path.with_suffix(".env.backup")
        backup_path.write_text(content)
        print(f"Backup saved to: {backup_path}")

        # Write updated
        env_path.write_text(updated)
        print("\nSUCCESS! Updated .env file")
        print("\nNew LangSmith configuration:")
        print("=" * 60)
        for line in updated.split("\n"):
            if "LANGCHAIN" in line:
                print(f"  {line}")
        print("=" * 60)
        return True
    else:
        print("\nNo changes needed - project key already configured!")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("LangSmith API Key Fix")
    print("=" * 60)
    print("\nThis will update your .env to use the project key")
    print("(Free tier: 5,000 traces/month)")
    print()

    success = fix_env_file()

    if success:
        print("\nNext steps:")
        print("1. Restart any running research processes")
        print("2. Run: python test_langsmith_clean.py")
        print("3. View traces at: https://smith.langchain.com")
        print("4. Project: maga-campaign-generator")
    else:
        print("\nManual fix needed:")
        print("1. Open .env file")
        print("2. Find: LANGCHAIN_API_KEY=lsv2_sk_...")
        print(f"3. Replace with: LANGCHAIN_API_KEY={PROJECT_KEY}")
