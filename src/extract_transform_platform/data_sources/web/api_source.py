"""
Generic REST API Data Source

Provides a flexible data source for REST APIs with:
- Configurable base URL and headers
- Bearer token authentication
- Query parameter support
- Automatic JSON parsing
- Built-in caching and rate limiting

Status: MIGRATED from edgar_analyzer (232 LOC, 100% generic)

Code Reuse: 100% from EDGAR APIDataSource
- Zero EDGAR-specific code removed (was already generic)
- Only import path changes (BaseDataSource location)
- All HTTP methods, auth, caching preserved
"""

import hashlib
import logging
from typing import Any, Dict, Optional

import httpx

from extract_transform_platform.core.base import BaseDataSource

logger = logging.getLogger(__name__)


class APIDataSource(BaseDataSource):
    """Generic REST API data source with authentication and error handling.

    Design Decision: Use httpx over requests
    - httpx supports async/await natively
    - Better HTTP/2 support
    - Modern API design
    - Type hints built-in

    Example:
        # OpenRouter API
        api = APIDataSource(
            base_url="https://openrouter.ai/api/v1",
            auth_token="sk-or-v1-...",
            rate_limit_per_minute=60
        )
        result = await api.fetch(endpoint="models", params={"limit": 10})

        # SEC EDGAR API
        edgar = APIDataSource(
            base_url="https://data.sec.gov",
            headers={"User-Agent": "MyCompany email@example.com"},
            rate_limit_per_minute=10  # SEC limit
        )
        data = await edgar.fetch(endpoint="submissions/CIK0000320193.json")
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        timeout_seconds: float = 30.0,
        **kwargs,
    ):
        """Initialize API data source.

        Args:
            base_url: Base URL for API (e.g., "https://api.example.com")
            headers: Optional custom headers
            auth_token: Optional bearer token for authentication
            timeout_seconds: Request timeout in seconds (default: 30.0)
            **kwargs: Additional arguments passed to BaseDataSource

        Design Trade-offs:
        - Timeout: 30s default balances responsiveness vs reliability
        - Headers: Mutable dict allows customization per-instance
        - Auth: Bearer token only (extend for OAuth, API key in future)
        """
        super().__init__(**kwargs)

        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds

        # Add bearer token if provided
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

        logger.info(
            f"Initialized APIDataSource with base_url={self.base_url}, "
            f"timeout={timeout_seconds}s"
        )

    async def fetch(
        self,
        endpoint: str = "",
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        **kwargs,
    ) -> Dict[str, Any]:
        """Fetch data from API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "users/123")
            params: Optional query parameters
            method: HTTP method (GET, POST, etc.) - default: GET
            **kwargs: Additional arguments (reserved for future use)

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: For HTTP errors (4xx, 5xx)
            httpx.TimeoutException: If request exceeds timeout
            ValueError: If response is not valid JSON

        Performance:
        - Time Complexity: O(1) for cache hit, O(n) for network call (n = response size)
        - Space Complexity: O(m) where m = response size
        - Caching reduces repeated calls to O(1)

        Example:
            # Simple GET
            data = await api.fetch("users/123")

            # GET with query params
            data = await api.fetch("search", params={"q": "python", "limit": 10})

            # Future: POST with body
            # data = await api.fetch("users", method="POST", body={"name": "Alice"})
        """
        cache_key = self.get_cache_key(endpoint=endpoint, params=params, method=method)

        async def _fetch() -> Dict[str, Any]:
            # Build full URL
            url = (
                f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
            )

            logger.debug(f"API {method} request to {url} with params={params}")

            # Make HTTP request
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=self.headers,
                )

                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()

                # Parse JSON response
                try:
                    data = response.json()
                    logger.debug(
                        f"API request successful: {response.status_code}, "
                        f"content_length={len(response.content)}"
                    )
                    return data
                except ValueError as e:
                    logger.error(
                        f"Invalid JSON response from {url}: {response.text[:200]}"
                    )
                    raise ValueError(f"API returned non-JSON response: {e}")

        return await self.fetch_with_cache(cache_key, _fetch)

    async def validate_config(self) -> bool:
        """Validate API configuration by testing connection.

        Tests base URL connectivity without authentication requirements.
        Does NOT validate auth credentials (use a test endpoint for that).

        Returns:
            True if base URL is accessible (status < 500)
            False if server errors or network issues

        Design Decision: Permissive validation
        - 4xx errors (auth, not found) return True (server is accessible)
        - 5xx errors return False (server issues)
        - Network errors return False (connectivity issues)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, headers=self.headers)
                is_valid = response.status_code < 500

                if is_valid:
                    logger.info(f"API validation successful: {response.status_code}")
                else:
                    logger.warning(
                        f"API validation failed: {response.status_code} - {response.text[:100]}"
                    )

                return is_valid

        except Exception as e:
            logger.error(f"API validation error: {type(e).__name__}: {e}")
            return False

    def get_cache_key(
        self,
        endpoint: str = "",
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        **kwargs,
    ) -> str:
        """Generate cache key from request parameters.

        Cache Key Design:
        - Includes: base_url, endpoint, params (sorted), method
        - Excludes: headers (may contain dynamic auth tokens)
        - Hash: MD5 for speed (not cryptographic use)

        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method
            **kwargs: Ignored (for compatibility)

        Returns:
            MD5 hash of request parameters (32 hex chars)

        Complexity:
        - Time: O(n) where n = total length of URL + params
        - Space: O(1) - fixed 32 byte hash
        """
        key_parts = [self.base_url, method, endpoint]

        if params:
            # Sort params for deterministic key
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))

        key_string = "||".join(key_parts)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()

        logger.debug(f"Generated cache key {cache_key} for {method} {endpoint}")
        return cache_key
