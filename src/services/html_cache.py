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
        # Sanitize company name - must match output_manager.py sanitization
        # Replace dangerous chars AND spaces with underscores, collapse multiple
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        safe_name = re.sub(r'[\s_]+', '_', safe_name)  # Match output_manager.py line 164
        safe_name = safe_name.strip('_.')
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

    def get_cached_html(self, url: str) -> Optional[Dict[str, str]]:
        """
        Read cached HTML content for a URL if it exists.

        Returns:
            Dict with 'html', 'title', 'url' if cached, None otherwise
        """
        if not self._cache_dir:
            return None

        filename = self._url_to_filename(url)
        filepath = self._cache_dir / filename

        if not filepath.exists():
            return None

        try:
            content = filepath.read_text(encoding="utf-8")

            # Parse metadata from header comment
            title = "Cached Page"
            original_url = url

            # Extract metadata from header: <!--\nHTML Cache...\nTitle: xxx\n...-->
            if content.startswith("<!--"):
                header_end = content.find("-->")
                if header_end > 0:
                    header = content[:header_end]
                    for line in header.split("\n"):
                        if line.startswith("Title:"):
                            title = line[6:].strip()
                        elif line.startswith("URL:"):
                            original_url = line[4:].strip()

                    # Remove header from HTML content
                    content = content[header_end + 3:].strip()

            logger.debug(f"HTML cache hit: {filename}")
            return {
                "html": content,
                "title": title,
                "url": original_url,
            }

        except Exception as e:
            logger.warning(f"Failed to read cached HTML for {url}: {e}")
            return None

    def load_existing_cache(self) -> int:
        """
        Load index of existing cached HTML files.

        Call this when resuming to recognize previously cached pages.

        Returns:
            Number of cached files found
        """
        if not self._cache_dir or not self._cache_dir.exists():
            return 0

        count = 0
        for html_file in self._cache_dir.glob("*.html"):
            if html_file.name == "_index.md":
                continue
            try:
                # Read just the header to get URL
                content = html_file.read_text(encoding="utf-8", errors="ignore")
                if content.startswith("<!--"):
                    header_end = content.find("-->")
                    if header_end > 0:
                        header = content[:header_end]
                        for line in header.split("\n"):
                            if line.startswith("URL:"):
                                url = line[4:].strip()
                                self._index[url] = {
                                    "filename": html_file.name,
                                    "title": None,
                                    "timestamp": None,
                                    "status": "cached",
                                    "size": html_file.stat().st_size,
                                }
                                count += 1
                                break
            except Exception as e:
                logger.debug(f"Could not parse cached file {html_file.name}: {e}")

        if count > 0:
            logger.info(f"Loaded {count} cached HTML files from previous runs")
        return count

    def is_url_cached(self, url: str) -> bool:
        """Quick check if URL is in cache (either index or file exists)."""
        if url in self._index:
            return True
        return self.get_cached_path(url) is not None


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
