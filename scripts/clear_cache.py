#!/usr/bin/env python3
"""
Cache Clear Script - SCRIPT-003

Clears all caches used by Company Researcher:
- AI response cache
- HTML/web page cache
- Search results cache
- Semantic cache
- File system caches

Usage:
    python scripts/clear_cache.py           # Clear all caches
    python scripts/clear_cache.py --ai      # Clear only AI cache
    python scripts/clear_cache.py --html    # Clear only HTML cache
    python scripts/clear_cache.py --search  # Clear only search cache
    python scripts/clear_cache.py --dry-run # Show what would be cleared
"""

import argparse
import shutil
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

console = Console()


def get_cache_directories() -> dict[str, Path]:
    """Get all cache directories."""
    return {
        "ai_cache": PROJECT_ROOT / "data" / "cache" / "ai",
        "html_cache": PROJECT_ROOT / "data" / "cache" / "html",
        "search_cache": PROJECT_ROOT / "data" / "cache" / "search",
        "semantic_cache": PROJECT_ROOT / "data" / "cache" / "semantic",
        "general_cache": PROJECT_ROOT / "data" / "cache",
        "file_index": PROJECT_ROOT / "file_index",
        "outputs_test": PROJECT_ROOT / "outputs_test",
    }


def get_cache_size(path: Path) -> tuple[int, int]:
    """Get cache directory size in bytes and file count."""
    if not path.exists():
        return 0, 0

    total_size = 0
    file_count = 0

    try:
        for item in path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
    except PermissionError:
        pass

    return total_size, file_count


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def clear_cache(path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Clear a cache directory.

    Returns:
        Tuple of (success, message)
    """
    if not path.exists():
        return True, "Does not exist"

    if dry_run:
        size, count = get_cache_size(path)
        return True, f"Would clear {count} files ({format_size(size)})"

    try:
        if path.is_dir():
            shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)
            return True, "Cleared"
        else:
            path.unlink()
            return True, "Deleted"
    except PermissionError as e:
        return False, f"Permission denied: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Clear Company Researcher caches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/clear_cache.py              # Clear all caches
    python scripts/clear_cache.py --ai --html  # Clear AI and HTML caches
    python scripts/clear_cache.py --dry-run    # Preview what would be cleared
        """
    )

    parser.add_argument(
        "--ai", action="store_true",
        help="Clear AI response cache only"
    )
    parser.add_argument(
        "--html", action="store_true",
        help="Clear HTML/web page cache only"
    )
    parser.add_argument(
        "--search", action="store_true",
        help="Clear search results cache only"
    )
    parser.add_argument(
        "--semantic", action="store_true",
        help="Clear semantic/vector cache only"
    )
    parser.add_argument(
        "--index", action="store_true",
        help="Clear file index cache only"
    )
    parser.add_argument(
        "--test-outputs", action="store_true",
        help="Clear test outputs directory"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Show what would be cleared without actually clearing"
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Determine which caches to clear
    cache_dirs = get_cache_directories()

    # If no specific cache selected, clear all
    selected = []
    if args.ai:
        selected.append("ai_cache")
    if args.html:
        selected.append("html_cache")
    if args.search:
        selected.append("search_cache")
    if args.semantic:
        selected.append("semantic_cache")
    if args.index:
        selected.append("file_index")
    if args.test_outputs:
        selected.append("outputs_test")

    # If no specific flags, clear all caches (except test outputs)
    if not selected:
        selected = ["ai_cache", "html_cache", "search_cache", "semantic_cache", "general_cache", "file_index"]

    # Build results table
    table = Table(title="Cache Clear Status" if not args.dry_run else "Cache Clear Preview (Dry Run)")
    table.add_column("Cache", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Size", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("Status", style="green")

    # Calculate total size
    total_size = 0
    total_files = 0

    caches_to_clear = []
    for name in selected:
        if name in cache_dirs:
            path = cache_dirs[name]
            size, count = get_cache_size(path)
            total_size += size
            total_files += count
            caches_to_clear.append((name, path, size, count))

    # Confirmation (unless --force or --dry-run)
    if not args.dry_run and not args.force and total_files > 0:
        console.print(f"\n[yellow]About to clear {total_files} files ({format_size(total_size)})[/yellow]")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != "y":
            console.print("[red]Cancelled[/red]")
            return

    # Clear caches
    for name, path, size, count in caches_to_clear:
        success, message = clear_cache(path, dry_run=args.dry_run)
        status_style = "green" if success else "red"
        table.add_row(
            name,
            str(path.relative_to(PROJECT_ROOT)),
            format_size(size),
            str(count),
            f"[{status_style}]{message}[/{status_style}]"
        )

    console.print()
    console.print(table)
    console.print()

    if args.dry_run:
        console.print(f"[yellow]Total: {total_files} files ({format_size(total_size)}) would be cleared[/yellow]")
    else:
        console.print(f"[green]Cleared {total_files} files ({format_size(total_size)})[/green]")


if __name__ == "__main__":
    main()
