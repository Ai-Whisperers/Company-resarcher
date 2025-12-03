import subprocess
import json
import os
import base64
from pathlib import Path


def run_command(command):
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        print(result.stderr)
        return None
    return result.stdout


def main():
    # Create output directory
    output_dir = Path("repo_explanations")
    output_dir.mkdir(exist_ok=True)

    print("Fetching repository list...")
    # Get list of repos
    repos_json = run_command(
        "gh repo list Ai-Whisperers --limit 100 --json name,description,url,visibility"
    )
    if not repos_json:
        return

    repos = json.loads(repos_json)
    print(f"Found {len(repos)} repositories.")

    for repo in repos:
        name = repo["name"]
        print(f"Processing {name}...")

        # Get README content
        # Use gh api to get the json response and decode in python
        readme_json = run_command(f"gh api repos/Ai-Whisperers/{name}/readme")
        readme_content = "No README found."

        if readme_json:
            try:
                data = json.loads(readme_json)
                if "content" in data:
                    # GitHub API returns content with newlines, need to remove them before decoding
                    encoded_content = data["content"].replace("\n", "")
                    readme_content = base64.b64decode(encoded_content).decode(
                        "utf-8", errors="replace"
                    )
            except Exception as e:
                print(f"Error decoding README for {name}: {e}")

        # Create markdown file
        file_path = output_dir / f"{name}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n")
            f.write(f"**Description:** {repo.get('description', 'No description')}\n")
            f.write(f"**URL:** {repo.get('url', 'N/A')}\n")
            f.write(f"**Visibility:** {repo.get('visibility', 'N/A')}\n\n")
            f.write("---\n\n")
            f.write(readme_content)

        print(f"Saved {file_path}")


if __name__ == "__main__":
    main()
