import os
import re


def check_links(root_dir):
    broken_links = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".md"):
                filepath = os.path.join(dirpath, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find all markdown links [text](url)
                links = re.findall(r"\[.*?\]\((.*?)\)", content)
                for link in links:
                    if (
                        link.startswith("http")
                        or link.startswith("#")
                        or link.startswith("mailto:")
                    ):
                        continue

                    # Resolve relative path
                    # Handle anchor links like file.md#anchor
                    link_path = link.split("#")[0]
                    if not link_path:
                        continue

                    target_path = os.path.normpath(os.path.join(dirpath, link_path))
                    if not os.path.exists(target_path):
                        broken_links.append((filepath, link))

    return broken_links


if __name__ == "__main__":
    root = r"c:\Users\Alejandro\Documents\Ivan\Work\Company-resarcher\docs"
    broken = check_links(root)
    if broken:
        print("Found broken links:")
        for file, link in broken:
            print(f"{file}: {link}")
    else:
        print("No broken links found.")
