"""OpenRouter API client for Sonnet 4.5 integration.

This module provides a type-safe HTTP client for the OpenRouter API,
handling authentication, request/response formatting, and error handling.
"""

from dataclasses import dataclass
from typing import Any

import httpx


class OpenRouterError(Exception):
    """Base exception for OpenRouter API errors."""

    pass


class AuthenticationError(OpenRouterError):
    """API authentication failed."""

    pass


class RateLimitError(OpenRouterError):
    """API rate limit exceeded."""

    pass


class APIError(OpenRouterError):
    """General API error."""

    pass


@dataclass(frozen=True)
class OpenRouterClient:
    """HTTP client for OpenRouter API.

    Handles authentication, request formatting, and error handling for
    OpenRouter API calls.

    Attributes:
        api_key: OpenRouter API key
        base_url: OpenRouter API base URL
        model: Model identifier (default: anthropic/claude-sonnet-4.5)
        timeout: Request timeout in seconds (default: 60)
    """

    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "anthropic/claude-sonnet-4.5"
    timeout: float = 60.0

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send chat completion request to OpenRouter API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            API response dictionary with completion

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
            httpx.HTTPError: For network errors
        """
        # TODO: Implement OpenRouter API client
        raise NotImplementedError("OpenRouter client not yet implemented")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for OpenRouter API requests.

        Returns:
            Dictionary of HTTP headers including authorization
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/masa-cloud/edgar-platform",
        }

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from OpenRouter API.

        Args:
            response: HTTP response object

        Raises:
            AuthenticationError: If status is 401 or 403
            RateLimitError: If status is 429
            APIError: For other error statuses
        """
        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(f"Authentication failed: {response.text}")
        elif response.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {response.text}")
        else:
            raise APIError(f"API error (status {response.status_code}): {response.text}")
