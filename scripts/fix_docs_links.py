import os
import re


def fix_links(root_dir, project_root):
    # Known files/dirs in project root that might be linked
    root_items = {
        "CONTRIBUTING.md",
        "LICENSE",
        "README.md",
        "main.py",
        "src",
        "tests",
        "data",
        "scripts",
        "docs",
    }

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".md"):
                filepath = os.path.join(dirpath, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Calculate relative path from current file to project root
                rel_to_root = os.path.relpath(project_root, dirpath)

                def replace_link(match):
                    link_text = match.group(0)
                    url = match.group(1)

                    if (
                        url.startswith("http")
                        or url.startswith("#")
                        or url.startswith("mailto:")
                    ):
                        return link_text

                    # Fix links starting with docs/
                    if url.startswith("docs/"):
                        new_url = os.path.normpath(
                            os.path.join(rel_to_root, url)
                        ).replace("\\", "/")
                        return f"[{match.group(2)}]({new_url})"

                    # Fix links to root items
                    first_part = url.split("/")[0]
                    if first_part in root_items:
                        new_url = os.path.normpath(
                            os.path.join(rel_to_root, url)
                        ).replace("\\", "/")
                        return f"[{match.group(2)}]({new_url})"

                    return link_text

                # Regex to match [text](url)
                # Group 1: url, Group 2: text (we need to capture text to reconstruct)
                # Wait, re.sub passes match object.
                # Regex: \[([^\]]+)\]\(([^)]+)\) -> Group 1 is text, Group 2 is url
                new_content = re.sub(
                    r"\[([^\]]+)\]\(([^)]+)\)",
                    lambda m: replace_link_match(m, rel_to_root, root_items),
                    content,
                )

                if new_content != content:
                    print(f"Fixing links in {filepath}")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)


def replace_link_match(match, rel_to_root, root_items):
    text = match.group(1)
    url = match.group(2)

    if url.startswith("http") or url.startswith("#") or url.startswith("mailto:"):
        return match.group(0)

    # Fix links starting with docs/
    if url.startswith("docs/"):
        new_url = os.path.normpath(os.path.join(rel_to_root, url)).replace("\\", "/")
        return f"[{text}]({new_url})"

    # Fix links to root items
    first_part = url.split("/")[0]
    if first_part in root_items:
        new_url = os.path.normpath(os.path.join(rel_to_root, url)).replace("\\", "/")
        return f"[{text}]({new_url})"

    return match.group(0)


if __name__ == "__main__":
    docs_root = r"c:\Users\Alejandro\Documents\Ivan\Work\Company-resarcher\docs"
    proj_root = r"c:\Users\Alejandro\Documents\Ivan\Work\Company-resarcher"
    fix_links(docs_root, proj_root)
