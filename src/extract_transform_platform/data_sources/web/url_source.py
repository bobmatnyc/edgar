"""
Generic URL Data Source

Simple HTTP/HTTPS data source for fetching content from URLs.
Supports JSON and plain text responses.

Use Cases:
- REST APIs without complex authentication
- Public data endpoints
- Simple webhook callbacks
- Health check endpoints

For advanced features, use:
- APIDataSource: REST APIs with auth, headers, rate limiting
- JinaDataSource: Web page content extraction (clean markdown)
"""

import hashlib
import logging
from typing import Any, Dict, Optional

import httpx

from extract_transform_platform.core.base import BaseDataSource

logger = logging.getLogger(__name__)


class URLDataSource(BaseDataSource):
    """Simple HTTP URL data source for fetching content.

    Design Decision: Minimalist approach
    - No auth (use APIDataSource for that)
    - No custom headers (use APIDataSource for that)
    - Auto-detect JSON vs text
    - Focus: Simplicity for public endpoints

    Example:
        # Public JSON API
        url_source = URLDataSource()
        data = await url_source.fetch("https://api.github.com/users/github")
        print(data['login'])  # 'github'

        # Plain text
        text_source = URLDataSource()
        result = await text_source.fetch("https://example.com/robots.txt")
        print(result['content'])  # robots.txt content
    """

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        **kwargs,
    ):
        """Initialize URL data source.

        Args:
            timeout_seconds: Request timeout (default: 30s)
            **kwargs: Additional arguments passed to BaseDataSource

        Design Trade-offs:
        - Timeout: 30s balances patience vs hanging requests
        - Rate limiting: 60/min default (conservative for public APIs)
        - Caching: 1 hour TTL (good for semi-static content)
        """
        super().__init__(**kwargs)
        self.timeout_seconds = timeout_seconds

        logger.info(f"Initialized URLDataSource with timeout={timeout_seconds}s")

    async def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch content from URL.

        Args:
            url: Full URL to fetch (must start with http:// or https://)
            **kwargs: Reserved for future use

        Returns:
            Dictionary containing:
            - For JSON responses: Parsed JSON data
            - For text responses:
                - content: Raw text content
                - url: Original URL
                - content_type: MIME type from headers

        Raises:
            ValueError: If URL is invalid (not http/https)
            httpx.HTTPError: For HTTP errors (4xx, 5xx)
            httpx.TimeoutException: If request exceeds timeout

        Performance:
        - Time Complexity: O(n) where n = response size
        - Network I/O: Varies by endpoint (typically 100ms - 5s)
        - Caching: Critical for repeated access (O(1) cache hit)

        Example:
            # JSON API
            data = await url_source.fetch("https://api.ipify.org?format=json")
            print(data['ip'])  # Your IP address

            # Plain text
            text = await url_source.fetch("https://www.ietf.org/rfc/rfc2616.txt")
            print(text['content'][:100])  # First 100 chars
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid URL: {url} (must start with http:// or https://)"
            )

        cache_key = self.get_cache_key(url=url)

        async def _fetch() -> Dict[str, Any]:
            logger.debug(f"Fetching URL: {url}")

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()

                # Try JSON first
                if "application/json" in content_type:
                    try:
                        data = response.json()
                        logger.info(
                            f"Fetched JSON from {url}: {response.status_code}, "
                            f"{len(response.content)} bytes"
                        )
                        return data
                    except ValueError:
                        # Content-Type says JSON but isn't valid JSON
                        logger.warning(
                            f"Content-Type is JSON but parsing failed: {url}"
                        )

                # Fallback to text
                text_content = response.text
                logger.info(
                    f"Fetched text from {url}: {response.status_code}, "
                    f"{len(text_content)} chars, "
                    f"content_type={content_type}"
                )

                return {
                    "content": text_content,
                    "url": url,
                    "content_type": content_type,
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                }

        return await self.fetch_with_cache(cache_key, _fetch)

    async def validate_config(self) -> bool:
        """Validate URL data source configuration.

        URLs are always "valid" from a configuration perspective.
        Actual validation happens at fetch time (URL format, network access).

        Returns:
            Always True (no configuration to validate)

        Design Decision: No upfront validation
        - URLs can't be validated without making requests
        - Validation would consume rate limits
        - Errors should be caught at fetch time with proper context
        """
        logger.debug("URLDataSource has no configuration to validate")
        return True

    def get_cache_key(self, url: str, **kwargs) -> str:
        """Generate cache key from URL.

        Design Decision: Hash URL for privacy and consistent length
        - URL might contain sensitive query params
        - Hash hides URL details in cache keys
        - MD5 for speed (not cryptographic use)

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
