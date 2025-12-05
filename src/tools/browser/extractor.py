"""
Content Extractor - HTML Content Extraction and Cleaning

Handles:
- Content extraction from HTML
- Metadata extraction
- Content cleaning and filtering
- Smart selector caching
"""

import threading
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import Page

from src.core.logging import setup_logger
from src.infrastructure.sources.source_classifier import classify_source

logger = setup_logger("browser_extractor")


@dataclass
class ExtractedContent:
    """Result of content extraction."""

    text: str
    html: str
    title: str
    metadata: Dict[str, str] = field(default_factory=dict)
    source_type: str = "unknown"
    word_count: int = 0


@dataclass
class ExtractionConfig:
    """Configuration for content extraction."""

    max_content_length: int = 20000
    remove_elements: List[str] = field(
        default_factory=lambda: [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "iframe",
            "noscript",
            "ads",
            "advertising",
        ]
    )
    main_content_selectors: List[str] = field(
        default_factory=lambda: [
            "article",
            "main",
            "[role='main']",
            ".content",
            "#content",
            ".post-content",
            ".entry-content",
            ".article-content",
            ".post-body",
            "#main-content",
        ]
    )


class ContentExtractor:
    """
    Extracts and cleans content from web pages.

    Responsibilities:
    - Extract main content using smart selectors
    - Extract metadata (title, description, author, etc.)
    - Clean content by removing unwanted elements
    - Cache successful selectors per domain
    - Classify source types
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self._selector_cache: Dict[str, str] = {}
        self._selector_cache_lock = threading.Lock()
        self._combined_selector = ", ".join(self.config.main_content_selectors)

    async def extract_from_page(self, page: Page, url: str) -> ExtractedContent:
        """
        Extract content from a Playwright page.

        Args:
            page: Playwright page instance
            url: URL of the page (for caching and classification)

        Returns:
            ExtractedContent with text, metadata, and classification
        """
        html = await page.content()
        title = await page.title()

        return self.extract_from_html(html, url, title)

    def extract_from_html(
        self,
        html: str,
        url: str,
        fallback_title: Optional[str] = None,
    ) -> ExtractedContent:
        """
        Extract content from raw HTML.

        Args:
            html: Raw HTML content
            url: URL of the page
            fallback_title: Title to use if none found in HTML

        Returns:
            ExtractedContent with text, metadata, and classification
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata first (before cleaning)
        metadata = self._extract_metadata(soup)
        title = metadata.get("title") or fallback_title or self._get_fallback_title(url)

        # Clean the soup (remove unwanted elements)
        self._clean_soup(soup)

        # Extract main content using smart selectors
        main_content = self._extract_main_content(soup, url)
        text_content = main_content.get_text(separator="\n", strip=True)

        # Truncate if needed
        if len(text_content) > self.config.max_content_length:
            text_content = text_content[: self.config.max_content_length]

        # Classify source type
        source_type = classify_source(url, text_content)

        return ExtractedContent(
            text=text_content,
            html=str(main_content),
            title=title,
            metadata=metadata,
            source_type=source_type,
            word_count=len(text_content.split()),
        )

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML head."""
        metadata = {}

        # Title
        if soup.title and soup.title.string:
            metadata["title"] = soup.title.string.strip()

        # Meta tags
        meta_mappings = {
            "description": [("name", "description"), ("property", "og:description")],
            "keywords": [("name", "keywords")],
            "author": [("name", "author"), ("property", "article:author")],
            "published": [
                ("property", "article:published_time"),
                ("name", "datePublished"),
                ("name", "pubdate"),
            ],
            "image": [("property", "og:image")],
            "site_name": [("property", "og:site_name")],
        }

        for field_name, attrs_list in meta_mappings.items():
            for attr_name, attr_value in attrs_list:
                meta_tag = soup.find("meta", attrs={attr_name: attr_value})
                if meta_tag and meta_tag.get("content"):
                    metadata[field_name] = meta_tag["content"]
                    break

        return metadata

    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from soup in place."""
        for element in soup.find_all(self.config.remove_elements):
            element.decompose()

    def _extract_main_content(self, soup: BeautifulSoup, url: str) -> Any:
        """
        Extract main content using smart selector caching.

        Uses a per-domain cache to remember which selector worked,
        falling back to combined selector query.
        """
        domain = urlparse(url).netloc
        main_content = None

        # Try cached selector first (fast path)
        with self._selector_cache_lock:
            cached_selector = self._selector_cache.get(domain)

        if cached_selector:
            main_content = soup.select_one(cached_selector)
            if main_content:
                return main_content

        # Fall back to combined selector (O(1) instead of sequential O(n))
        main_content = soup.select_one(self._combined_selector)

        if main_content:
            # Cache the specific selector that matched
            matched_selector = self._determine_matched_selector(main_content)
            if matched_selector:
                with self._selector_cache_lock:
                    self._selector_cache[domain] = matched_selector
                logger.debug(f"Cached selector '{matched_selector}' for {domain}")

        # Final fallback to body
        if not main_content:
            main_content = soup.body or soup

        return main_content

    def _determine_matched_selector(self, element) -> Optional[str]:
        """Determine the best selector for a matched element."""
        if element.get("id"):
            return f"#{element['id']}"
        elif element.get("class"):
            return f".{element['class'][0]}"
        elif element.get("role"):
            return f"[role='{element['role']}']"
        elif element.name in ["article", "main"]:
            return element.name
        return None

    def _get_fallback_title(self, url: str) -> str:
        """Generate a fallback title from URL."""
        domain = urlparse(url).netloc
        return domain.replace("www.", "") if domain else url[:50]

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract all links from the page.

        Args:
            soup: BeautifulSoup instance
            base_url: Base URL for resolving relative links

        Returns:
            List of dicts with 'href' and 'text' keys
        """
        from urllib.parse import urljoin

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Resolve relative URLs
            if not href.startswith(("http://", "https://")):
                href = urljoin(base_url, href)

            # Skip non-HTTP links
            if not href.startswith(("http://", "https://")):
                continue

            links.append(
                {
                    "href": href,
                    "text": a.get_text(strip=True)[:100],  # Limit text length
                }
            )

        return links

    def clear_cache(self, domain: Optional[str] = None) -> None:
        """
        Clear selector cache.

        Args:
            domain: Specific domain to clear, or None to clear all
        """
        with self._selector_cache_lock:
            if domain:
                self._selector_cache.pop(domain, None)
            else:
                self._selector_cache.clear()
