"""
Cross-Company HTML Reader - Reads cached HTML from all company folders in a market.

This enables Phase 2 research enrichment by loading data gathered from sibling companies
to provide cross-company insights and competitive intelligence.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..core.logger import setup_logger

logger = setup_logger("cross_company_reader")


@dataclass
class CachedHTML:
    """Represents a cached HTML file with metadata."""
    company_name: str
    url: str
    title: str
    content: str
    filepath: Path
    size_bytes: int


@dataclass
class CompanyCache:
    """All cached HTML files for a single company."""
    company_name: str
    html_files: List[CachedHTML]
    total_size: int

    @property
    def file_count(self) -> int:
        return len(self.html_files)


class CrossCompanyReader:
    """
    Reads HTML cache from multiple company folders.

    Used for Phase 2 research enrichment where we analyze data
    from all companies in a market to provide cross-references.

    Example:
        reader = CrossCompanyReader("outputs")
        caches = reader.load_market_cache([
            "Personal Paraguay",
            "Tigo Paraguay",
            "Claro Paraguay",
        ])

        # Get all content mentioning a competitor
        mentions = reader.find_mentions(caches, "Personal")
    """

    def __init__(self, base_dir: str = "outputs"):
        self.base_dir = Path(base_dir).resolve()

    def get_company_folders(self) -> List[str]:
        """List all company folders in the output directory."""
        if not self.base_dir.exists():
            return []

        folders = []
        for item in self.base_dir.iterdir():
            if item.is_dir() and not item.name.startswith(("_", ".")):
                # Check if it has research output (not just test folders)
                if (item / "99-Sources").exists() or any(item.glob("*/*.md")):
                    folders.append(item.name)

        return sorted(folders)

    def load_company_cache(self, company_name: str) -> Optional[CompanyCache]:
        """
        Load all cached HTML files for a single company.

        Args:
            company_name: Name of the company folder

        Returns:
            CompanyCache with all HTML files, or None if not found
        """
        # Sanitize company name (same logic as HTMLCache)
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
        html_dir = self.base_dir / safe_name / "99-Sources" / "html"

        if not html_dir.exists():
            logger.debug(f"No HTML cache found for {company_name}")
            return None

        html_files = []
        total_size = 0

        for filepath in html_dir.glob("*.html"):
            if filepath.name.startswith("_"):
                continue  # Skip index files

            try:
                content = filepath.read_text(encoding="utf-8")
                metadata = self._parse_metadata(content)

                cached = CachedHTML(
                    company_name=company_name,
                    url=metadata.get("url", ""),
                    title=metadata.get("title", filepath.stem),
                    content=self._strip_metadata_header(content),
                    filepath=filepath,
                    size_bytes=len(content),
                )
                html_files.append(cached)
                total_size += cached.size_bytes

            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")

        if not html_files:
            return None

        logger.info(f"Loaded {len(html_files)} HTML files for {company_name} ({total_size / 1024:.1f}KB)")

        return CompanyCache(
            company_name=company_name,
            html_files=html_files,
            total_size=total_size,
        )

    def load_market_cache(
        self,
        company_names: Optional[List[str]] = None,
        exclude_company: Optional[str] = None,
    ) -> List[CompanyCache]:
        """
        Load cached HTML from multiple companies.

        Args:
            company_names: List of company names to load (default: all)
            exclude_company: Company to exclude (e.g., current research target)

        Returns:
            List of CompanyCache objects
        """
        if company_names is None:
            company_names = self.get_company_folders()

        if exclude_company:
            company_names = [c for c in company_names if c != exclude_company]

        caches = []
        for company in company_names:
            cache = self.load_company_cache(company)
            if cache:
                caches.append(cache)

        total_files = sum(c.file_count for c in caches)
        total_size = sum(c.total_size for c in caches)
        logger.info(
            f"Loaded market cache: {len(caches)} companies, "
            f"{total_files} files, {total_size / 1024:.1f}KB"
        )

        return caches

    def find_mentions(
        self,
        caches: List[CompanyCache],
        search_term: str,
        case_sensitive: bool = False,
    ) -> List[Dict]:
        """
        Find all mentions of a term across cached HTML files.

        Args:
            caches: List of company caches to search
            search_term: Term to search for
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of dicts with company, url, title, and excerpt
        """
        mentions = []
        pattern = search_term if case_sensitive else search_term.lower()

        for cache in caches:
            for html in cache.html_files:
                content = html.content if case_sensitive else html.content.lower()

                if pattern in content:
                    # Extract excerpt around mention
                    idx = content.find(pattern)
                    start = max(0, idx - 100)
                    end = min(len(html.content), idx + len(search_term) + 100)
                    excerpt = html.content[start:end].strip()

                    mentions.append({
                        "company": cache.company_name,
                        "url": html.url,
                        "title": html.title,
                        "excerpt": f"...{excerpt}...",
                    })

        return mentions

    def get_competitor_context(
        self,
        caches: List[CompanyCache],
        target_company: str,
    ) -> str:
        """
        Build a context string with competitor information for AI analysis.

        Args:
            caches: List of company caches
            target_company: The company being researched (to find mentions)

        Returns:
            Formatted context string for AI prompts
        """
        lines = [f"# Cross-Company Research Context\n"]
        lines.append(f"Target company: {target_company}\n")
        lines.append(f"Related companies analyzed: {len(caches)}\n\n")

        # Find mentions of target company in competitor data
        mentions = self.find_mentions(caches, target_company)
        if mentions:
            lines.append(f"## Mentions of {target_company} in competitor data ({len(mentions)} found)\n")
            for m in mentions[:10]:  # Limit to top 10
                lines.append(f"- **{m['company']}** - {m['title']}")
                lines.append(f"  > {m['excerpt'][:200]}...\n")

        # Summarize each competitor's data
        lines.append("\n## Competitor Summaries\n")
        for cache in caches:
            lines.append(f"### {cache.company_name}")
            lines.append(f"- Sources: {cache.file_count} pages")
            lines.append(f"- Data size: {cache.total_size / 1024:.1f}KB")

            # List key pages
            key_pages = sorted(cache.html_files, key=lambda x: x.size_bytes, reverse=True)[:5]
            lines.append("- Key sources:")
            for page in key_pages:
                lines.append(f"  - {page.title[:50]} ({page.size_bytes / 1024:.1f}KB)")
            lines.append("")

        return "\n".join(lines)

    def _parse_metadata(self, content: str) -> Dict[str, str]:
        """Parse metadata from the HTML header comment."""
        metadata = {}

        # Look for metadata block
        if content.startswith("<!--"):
            end = content.find("-->")
            if end > 0:
                header = content[4:end]
                for line in header.split("\n"):
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        metadata[key.strip().lower()] = value.strip()

        return metadata

    def _strip_metadata_header(self, content: str) -> str:
        """Remove the metadata header comment from HTML content."""
        if content.startswith("<!--"):
            end = content.find("-->")
            if end > 0:
                return content[end + 3:].strip()
        return content


# Global instance
_cross_company_reader: Optional[CrossCompanyReader] = None


def get_cross_company_reader(base_dir: str = "outputs") -> CrossCompanyReader:
    """Get or create the global cross-company reader instance."""
    global _cross_company_reader
    if _cross_company_reader is None:
        _cross_company_reader = CrossCompanyReader(base_dir)
    return _cross_company_reader


def reset_cross_company_reader() -> None:
    """Reset the global instance."""
    global _cross_company_reader
    _cross_company_reader = None
