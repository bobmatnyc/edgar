"""
Jina.ai Data Source

Web content extraction using Jina.ai's Reader API.
Converts any URL to clean, LLM-ready markdown content.

Features:
- Clean markdown output (no HTML clutter)
- Main content extraction (removes ads, navigation)
- JavaScript rendering (JS-heavy sites like React/Vue/Angular)
- Automatic rate limiting (20/min free, 200/min paid)
- Built-in caching
- Metadata extraction (title, description, images)

Documentation: https://jina.ai/reader
"""

import hashlib
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from extract_transform_platform.core.base import BaseDataSource

logger = logging.getLogger(__name__)


class JinaDataSource(BaseDataSource):
    """Jina.ai reader data source for web content extraction.

    Design Decision: Jina over BeautifulSoup
    - Jina handles JavaScript-rendered content (React, Vue, Angular)
    - Better main content extraction (removes boilerplate)
    - Clean markdown output (LLM-friendly)
    - No need for custom selectors per site

    Rate Limits:
    - Free tier: 20 requests/minute
    - Paid tier: 200 requests/minute
    - Auto-configured based on API key presence

    Example:
        # With API key (200 req/min)
        jina = JinaDataSource(api_key=os.getenv("JINA_API_KEY"))
        result = await jina.fetch("https://example.com/article")
        print(result['content'])  # Clean markdown

        # Free tier (20 req/min)
        jina = JinaDataSource()
        result = await jina.fetch("https://example.com")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://r.jina.ai",
        timeout_seconds: float = 30.0,
        **kwargs,
    ):
        """Initialize Jina data source.

        Args:
            api_key: Optional Jina.ai API key (enables higher rate limits)
            base_url: Jina Reader API base URL (default: https://r.jina.ai)
            timeout_seconds: Request timeout (default: 30s)
            **kwargs: Additional arguments passed to BaseDataSource

        Design Trade-offs:
        - Auto-detect rate limit from API key presence
        - Higher cache TTL (1 hour) for static content
        - Timeout 30s accounts for page rendering time
        """
        # Resolve API key early to determine rate limit
        resolved_api_key = api_key or os.getenv("JINA_API_KEY")

        # Auto-configure rate limit based on API key
        if "rate_limit_per_minute" not in kwargs:
            kwargs["rate_limit_per_minute"] = 200 if resolved_api_key else 20

        # Set higher cache TTL for web content (less likely to change)
        if "cache_ttl_seconds" not in kwargs:
            kwargs["cache_ttl_seconds"] = 3600  # 1 hour

        super().__init__(**kwargs)

        self.api_key = resolved_api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        logger.info(
            f"Initialized JinaDataSource with "
            f"tier={'paid' if self.api_key else 'free'}, "
            f"rate_limit={self.rate_limit_per_minute}/min"
        )

    async def fetch(
        self,
        url: str,
        options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Extract content from URL using Jina.ai.

        Args:
            url: URL to extract content from
            options: Optional Jina API options (future: image mode, selector hints)
            **kwargs: Reserved for future use

        Returns:
            Dictionary containing:
            - content: Clean markdown content
            - title: Page title
            - url: Original URL
            - extracted_at: ISO timestamp
            - metadata: Additional page metadata (if available)

        Raises:
            httpx.HTTPError: For HTTP errors (4xx, 5xx)
            httpx.TimeoutException: If extraction exceeds timeout
            ValueError: If URL is invalid or response is malformed

        Performance:
        - Time Complexity: O(n) where n = page size
        - Network I/O: ~2-5 seconds typical for full page render
        - Caching: Critical for repeated access (O(1) cache hit)

        Example:
            result = await jina.fetch("https://news.ycombinator.com")
            print(result['title'])  # "Hacker News"
            print(result['content'][:100])  # First 100 chars of markdown
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid URL: {url} (must start with http:// or https://)"
            )

        cache_key = self.get_cache_key(url=url)

        async def _fetch() -> Dict[str, Any]:
            # Build Jina Reader URL: https://r.jina.ai/<target_url>
            jina_url = f"{self.base_url}/{url}"

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            logger.debug(f"Jina fetch: {url} (via {jina_url})")

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(jina_url, headers=headers)
                response.raise_for_status()

                # Jina returns clean markdown directly in response body
                # Content-Type: text/markdown or application/json (depends on version)
                content_type = response.headers.get("content-type", "").lower()

                if "application/json" in content_type:
                    # JSON response format
                    data = response.json()
                    return {
                        "content": data.get("data", {}).get("content", ""),
                        "title": data.get("data", {}).get("title", ""),
                        "url": url,
                        "extracted_at": datetime.now().isoformat(),
                        "metadata": data.get("data", {}).get("metadata", {}),
                    }
                else:
                    # Markdown text response (default)
                    markdown_content = response.text

                    # Extract title from first heading if present
                    title = ""
                    lines = markdown_content.split("\n")
                    for line in lines:
                        if line.startswith("# "):
                            title = line.lstrip("# ").strip()
                            break

                    logger.info(
                        f"Jina extraction successful: {len(markdown_content)} chars, "
                        f"title='{title[:50]}...'"
                    )

                    return {
                        "content": markdown_content,
                        "title": title,
                        "url": url,
                        "extracted_at": datetime.now().isoformat(),
                        "metadata": {},
                    }

        return await self.fetch_with_cache(cache_key, _fetch)

    async def validate_config(self) -> bool:
        """Validate Jina configuration by testing with example.com.

        Uses example.com as a test URL since it's:
        - Always available
        - Fast to load
        - Minimal content (won't exceed rate limits during testing)

        Returns:
            True if Jina API is accessible and functional
            False if API key is invalid, network issues, or service down
        """
        try:
            result = await self.fetch("https://example.com")
            is_valid = bool(result.get("content"))

            if is_valid:
                logger.info("Jina validation successful")
            else:
                logger.warning("Jina validation failed: empty content")

            return is_valid

        except Exception as e:
            logger.error(f"Jina validation error: {type(e).__name__}: {e}")
            return False

    def get_cache_key(self, url: str, **kwargs) -> str:
        """Generate cache key from URL.

        Design Decision: URL-only cache key
        - URL uniquely identifies content
        - Options (if added) would extend the key
        - Hash for consistent length and privacy

        Args:
            url: Target URL
            **kwargs: Ignored (for future options support)

        Returns:
            MD5 hash of URL (32 hex chars)

        Complexity:
        - Time: O(n) where n = URL length
        - Space: O(1) - fixed 32 byte hash
        """
        cache_key = hashlib.md5(url.encode()).hexdigest()
        logger.debug(f"Generated cache key {cache_key} for URL {url[:50]}...")
        return cache_key
