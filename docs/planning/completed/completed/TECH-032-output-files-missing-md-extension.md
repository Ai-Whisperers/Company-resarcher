# TECH-032: Output Files Missing .md Extension

## Priority: LOW
## Category: Technical Debt/UX
## Status: Backlog
## Discovered: 2025-11-28

## Summary

Output report files are saved without the `.md` extension, making them harder to identify as Markdown files and preventing proper syntax highlighting in editors and file browsers.

## Problem Statement

### Current Output:
```
outputs/Personal Paraguay/
├── market          ← No extension
├── financial       ← No extension
├── competitor      ← No extension
├── brand           ← No extension
└── sales           ← No extension
```

### Expected Output:
```
outputs/Personal Paraguay/
├── market.md       ← Proper extension
├── financial.md    ← Proper extension
├── competitor.md   ← Proper extension
├── brand.md        ← Proper extension
└── sales.md        ← Proper extension
```

## Impact

1. **Editor Experience**: Files don't open with Markdown syntax highlighting by default
2. **File Browsing**: Can't filter by `.md` extension in file browsers
3. **Version Control**: GitHub/GitLab won't render as Markdown in web UI
4. **Documentation**: Files aren't recognized as documentation by tools
5. **Professional Appearance**: Looks incomplete/unprofessional

## Root Cause Analysis

### Current Code in BaseAgent:

```python
# src/agents/base_agent.py

async def save_output(self, content: str, filename: str) -> None:
    """Save output to file."""
    output_path = self.output_dir / filename  # No extension added
    async with aiofiles.open(output_path, 'w') as f:
        await f.write(content)
```

### Caller Code:

```python
# Various agents
await self.save_output(report, "market")  # Should be "market.md"
await self.save_output(report, "financial")  # Should be "financial.md"
```

## Proposed Solutions

### Solution 1: Add Extension in save_output Method

```python
# src/agents/base_agent.py

async def save_output(self, content: str, filename: str, extension: str = ".md") -> None:
    """Save output to file with proper extension."""
    # Ensure filename has extension
    if not filename.endswith(extension):
        filename = f"{filename}{extension}"

    output_path = self.output_dir / filename
    async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
        await f.write(content)
```

### Solution 2: Update All Callers

```python
# Update each agent's save call
await self.save_output(report, "market.md")
await self.save_output(report, "financial.md")
await self.save_output(report, "competitor.md")
await self.save_output(report, "brand.md")
await self.save_output(report, "sales.md")
```

### Solution 3: Configuration-Based Extension

```python
# src/config.py

class OutputConfig:
    default_extension: str = ".md"
    format_extensions: Dict[str, str] = {
        "markdown": ".md",
        "json": ".json",
        "html": ".html",
        "pdf": ".pdf",
    }

# src/agents/base_agent.py

async def save_output(
    self,
    content: str,
    filename: str,
    format: str = "markdown"
) -> Path:
    """Save output with format-appropriate extension."""
    extension = self.config.output.format_extensions.get(format, ".md")

    if not filename.endswith(extension):
        filename = f"{filename}{extension}"

    output_path = self.output_dir / filename
    async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
        await f.write(content)

    return output_path
```

### Solution 4: Path Builder Utility

```python
# src/utils/paths.py

from pathlib import Path

class OutputPathBuilder:
    """Build output paths with proper extensions."""

    EXTENSIONS = {
        "markdown": ".md",
        "json": ".json",
        "html": ".html",
        "txt": ".txt",
    }

    @classmethod
    def build(
        cls,
        directory: Path,
        name: str,
        format: str = "markdown"
    ) -> Path:
        """Build output path with proper extension."""
        extension = cls.EXTENSIONS.get(format, ".md")

        # Handle if name already has extension
        if Path(name).suffix in cls.EXTENSIONS.values():
            return directory / name

        return directory / f"{name}{extension}"

# Usage
path = OutputPathBuilder.build(output_dir, "market")  # outputs/.../market.md
```

## Migration Considerations

### Handling Existing Files

When fixing this, consider:
1. **New runs**: Generate files with `.md` extension
2. **Existing files**: Optionally rename existing files during startup
3. **Backwards compatibility**: Read both with and without extension

```python
def find_output_file(directory: Path, name: str) -> Optional[Path]:
    """Find output file with or without extension."""
    # Try with extension first
    with_ext = directory / f"{name}.md"
    if with_ext.exists():
        return with_ext

    # Fall back to without extension
    without_ext = directory / name
    if without_ext.exists():
        return without_ext

    return None
```

## Files to Modify

1. `src/agents/base_agent.py` - Add extension handling in `save_output()`
2. `src/pipeline/stages/output.py` - Ensure pipeline output uses extensions
3. `src/utils/paths.py` - New utility for path building (optional)

## Acceptance Criteria

- [ ] All output files have `.md` extension
- [ ] Files open with Markdown highlighting in VS Code
- [ ] GitHub renders files as Markdown
- [ ] Existing functionality not broken
- [ ] JSON output (if any) uses `.json` extension

## Testing Plan

1. Run full research pipeline
2. Verify all output files have `.md` extension
3. Open files in VS Code - verify syntax highlighting
4. View files on GitHub - verify Markdown rendering
5. Test backwards compatibility with old files (if needed)

## Related Issues

- None directly related

## Notes

This is a minor UX issue but easy to fix. Should be addressed for professional output quality. Consider also adding a timestamp or version number to filenames for multiple runs:

```
outputs/Personal Paraguay/
├── market_2025-11-28.md
├── financial_2025-11-28.md
└── ...
```

Or versioning:
```
outputs/Personal Paraguay/
├── market_v1.md
├── market_v2.md
└── ...
```
