"""
HTML Cache Service - Saves raw HTML from scraped websites for debugging and verification.

This allows reviewing:
- What content was actually fetched
- Whether the extraction is working correctly
- The raw source for troubleshooting
"""

import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import urlparse

from ..core.logger import setup_logger

logger = setup_logger("html_cache")


class HTMLCache:
    """
    Caches raw HTML content from scraped websites.

    Saves to: outputs/{company_name}/99-Sources/html/{filename}.html
    """

    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir)
        self._current_company: Optional[str] = None
        self._cache_dir: Optional[Path] = None
        self._index: Dict[str, dict] = {}  # URL -> metadata

    def set_company(self, company_name: str) -> None:
        """Set the current company context for caching."""
        # Sanitize company name
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        self._current_company = safe_name
        self._cache_dir = self.base_dir / safe_name / "99-Sources" / "html"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._index = {}
        logger.info(f"HTML cache initialized for: {company_name}")

    def _url_to_filename(self, url: str) -> str:
        """
        Convert URL to a safe filename.

        Uses a combination of domain + path hash for uniqueness.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").replace(".", "_")

        # Create a short hash of the full URL for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        # Extract meaningful path component
        path_parts = [p for p in parsed.path.split("/") if p]
        path_hint = path_parts[-1] if path_parts else "index"

        # Sanitize path hint
        path_hint = re.sub(r'[<>:"/\\|?*]', '_', path_hint)
        path_hint = path_hint[:50]  # Limit length

        return f"{domain}_{path_hint}_{url_hash}.html"

    def save_html(
        self,
        url: str,
        html_content: str,
        title: Optional[str] = None,
        fetch_status: str = "success",
    ) -> Optional[Path]:
        """
        Save raw HTML content to cache.

        Args:
            url: Source URL
            html_content: Raw HTML string
            title: Page title (optional)
            fetch_status: Status of fetch (success, error, timeout, etc.)

        Returns:
            Path to saved file, or None if caching is disabled
        """
        if not self._cache_dir:
            logger.warning("HTML cache not initialized - call set_company() first")
            return None

        try:
            filename = self._url_to_filename(url)
            filepath = self._cache_dir / filename

            # Add metadata header to HTML
            timestamp = datetime.now().isoformat()
            header = f"""<!--
HTML Cache - Company Researcher
================================
URL: {url}
Title: {title or 'Unknown'}
Fetched: {timestamp}
Status: {fetch_status}
Size: {len(html_content)} bytes
================================
-->
"""
            # Save HTML with metadata header
            full_content = header + html_content
            filepath.write_text(full_content, encoding="utf-8")

            # Update index
            self._index[url] = {
                "filename": filename,
                "title": title,
                "timestamp": timestamp,
                "status": fetch_status,
                "size": len(html_content),
            }

            logger.debug(f"Cached HTML: {filename} ({len(html_content)} bytes)")
            return filepath

        except Exception as e:
            logger.warning(f"Failed to cache HTML for {url}: {e}")
            return None

    def save_index(self) -> Optional[Path]:
        """
        Save an index file listing all cached HTML files.

        Creates: 99-Sources/html/_index.md
        """
        if not self._cache_dir or not self._index:
            return None

        try:
            index_path = self._cache_dir / "_index.md"

            lines = [
                f"# HTML Cache Index",
                f"",
                f"**Company:** {self._current_company}",
                f"**Generated:** {datetime.now().isoformat()}",
                f"**Total Files:** {len(self._index)}",
                f"",
                f"## Cached Pages",
                f"",
                f"| # | Status | File | Title | Size |",
                f"|---|--------|------|-------|------|",
            ]

            for i, (url, meta) in enumerate(self._index.items(), 1):
                status_icon = "OK" if meta["status"] == "success" else "ERR"
                title = (meta["title"] or "Unknown")[:40]
                size_kb = meta["size"] / 1024
                lines.append(
                    f"| {i} | {status_icon} | [{meta['filename']}]({meta['filename']}) | {title} | {size_kb:.1f}KB |"
                )

            lines.extend([
                f"",
                f"## URLs",
                f"",
            ])

            for url, meta in self._index.items():
                lines.append(f"- [{meta['filename']}]({meta['filename']}): {url}")

            index_path.write_text("\n".join(lines), encoding="utf-8")
            logger.info(f"Saved HTML cache index: {index_path}")
            return index_path

        except Exception as e:
            logger.warning(f"Failed to save HTML cache index: {e}")
            return None

    def get_cached_path(self, url: str) -> Optional[Path]:
        """Get the cache path for a URL if it exists."""
        if not self._cache_dir:
            return None

        filename = self._url_to_filename(url)
        filepath = self._cache_dir / filename
        return filepath if filepath.exists() else None


# Global instance for easy access
_html_cache: Optional[HTMLCache] = None


def get_html_cache() -> HTMLCache:
    """Get the global HTML cache instance."""
    global _html_cache
    if _html_cache is None:
        _html_cache = HTMLCache()
    return _html_cache


def reset_html_cache() -> None:
    """Reset the global HTML cache instance."""
    global _html_cache
    _html_cache = None
