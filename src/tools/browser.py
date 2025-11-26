import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from ..core.logger import setup_logger
from ..core.types import ResearchSource

logger = setup_logger("browser_tool")


class BrowserTool:
    """
    Tool for fetching and parsing web content using Playwright.
    Handles dynamic content and basic anti-bot measures.
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def start(self):
        """Initialize the browser instance"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("Browser initialized")

    async def stop(self):
        """Close the browser instance"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser stopped")

    async def fetch_page(
        self, url: str, wait_for_selector: str = "body"
    ) -> ResearchSource:
        """
        Fetch a single page and extract its content with metadata.
        """
        if not self.browser:
            await self.start()

        page = await self.browser.new_page()
        try:
            logger.info(f"Navigating to: {url}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")

            # Wait for content to load
            try:
                await page.wait_for_selector(wait_for_selector, timeout=5000)
            except Exception:
                logger.warning(
                    f"Timeout waiting for selector '{wait_for_selector}' on {url}"
                )

            # Get content
            content = await page.content()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Extract Metadata
            metadata = self._extract_metadata(soup)
            title = metadata.get("title") or await page.title()

            # Remove unwanted elements
            for element in soup.find_all(
                [
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
            ):
                element.decompose()

            # Smart Content Extraction
            # Try to find main content area
            main_content = None
            for selector in [
                "article",
                "main",
                "[role='main']",
                ".content",
                "#content",
                ".post-content",
                ".entry-content",
            ]:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.body or soup

            text_content = main_content.get_text(separator="\n", strip=True)

            # Classify source type
            source_type = self.classify_source_type(url, text_content)

            return ResearchSource(
                url=url,
                title=title,
                content=text_content[:20000],  # Limit content size
                source_type=source_type,
                category="general",  # Will be updated by agent
            )

        except Exception as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return ResearchSource(
                url=url,
                title="Error Fetching Page",
                content=f"Error: {str(e)}",
                source_type="error",
                category="error",
            )
        finally:
            if page:
                await page.close()

    def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract metadata from HTML."""
        metadata = {}

        # Title
        if soup.title:
            metadata["title"] = soup.title.string

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            metadata["description"] = meta_desc.get("content", "")

        # Meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            metadata["keywords"] = meta_keywords.get("content", "")

        # Author
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author:
            metadata["author"] = meta_author.get("content", "")

        # Published date
        for attr in ["article:published_time", "datePublished", "pubdate"]:
            date_meta = soup.find("meta", attrs={"property": attr}) or soup.find(
                "meta", attrs={"name": attr}
            )
            if date_meta:
                metadata["published"] = date_meta.get("content", "")
                break

        return metadata

    def classify_source_type(self, url: str, content: str) -> str:
        """
        Classify the type of source based on URL and content.
        Ported from web_fetcher.py
        """
        url_lower = url.lower()
        content_lower = content.lower()

        # Check for specific source types
        if any(
            x in url_lower for x in ["statista", "euromonitor", "nielsen", "ibisworld"]
        ):
            return "industry_report"

        if any(x in url_lower for x in ["news", "press", "article", "blog"]):
            return "news_article"

        if any(x in url_lower for x in ["study", "research", "journal", "academic"]):
            return "academic"

        if any(
            x in url_lower
            for x in ["facebook", "twitter", "instagram", "linkedin", "tiktok"]
        ):
            return "social_media"

        if any(x in url_lower for x in ["gov", "gob", "gobierno"]):
            return "government"

        if "%" in content_lower or any(
            x in content_lower for x in ["growth", "market size", "revenue"]
        ):
            return "market_data"

        return "web"

    async def fetch_multiple(self, urls: List[str]) -> List[ResearchSource]:
        """
        Fetch multiple URLs concurrently.
        """
        tasks = [self.fetch_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {result}")
                continue

            if result:
                # Classify source type
                source_type = self.classify_source_type(
                    url, result.content
                )  # Access content via .content attribute

                sources.append(
                    ResearchSource(
                        url=url,
                        title=result.title,  # Access title via .title attribute
                        content=result.content,  # Access content via .content attribute
                        source_type=source_type,  # Use source_type instead of type
                        category="general",  # Will be updated by agent
                    )
                )

        return sources
