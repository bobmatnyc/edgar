"""OpenRouter API client for Sonnet 4.5 integration.

This module provides a type-safe HTTP client for the OpenRouter API,
handling authentication, request/response formatting, and error handling.

Design Decision: Retry with Exponential Backoff
Rationale: OpenRouter API can experience transient failures (rate limits, server errors).
Exponential backoff (2s, 4s, 8s) provides resilience without overwhelming the API.

Trade-offs:
- Latency: Additional 2-14 seconds on failures vs. immediate failure
- Reliability: 3x retry attempts vs. single failure point
- User Experience: Automatic recovery vs. manual retry required

Error Handling:
- 401/403: Auth errors (no retry - fail fast)
- 429: Rate limits (retry with backoff)
- 5xx: Server errors (retry with backoff)
- Network: Connection failures (retry with backoff)
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


class OpenRouterError(Exception):
    """Base exception for OpenRouter API errors."""

    pass


class OpenRouterAuthError(OpenRouterError):
    """API authentication failed (401/403)."""

    pass


class OpenRouterRateLimitError(OpenRouterError):
    """API rate limit exceeded (429)."""

    pass


class OpenRouterServerError(OpenRouterError):
    """OpenRouter server error (5xx)."""

    pass


# Legacy aliases for backwards compatibility
AuthenticationError = OpenRouterAuthError
RateLimitError = OpenRouterRateLimitError
APIError = OpenRouterError


@dataclass(frozen=True)
class OpenRouterClient:
    """HTTP client for OpenRouter API.

    Handles authentication, request formatting, and error handling for
    OpenRouter API calls with automatic retry logic.

    Performance:
    - Typical latency: 1-3 seconds for successful requests
    - Retry overhead: +2-14 seconds on failures (2s, 4s, 8s backoff)
    - Timeout: 60 seconds per request

    Retry Strategy:
    - Max retries: 3 attempts
    - Backoff: Exponential (2^(attempt+1) seconds)
    - Retryable: 429, 5xx, network errors
    - Non-retryable: 401, 403 (auth errors)

    Attributes:
        api_key: OpenRouter API key
        base_url: OpenRouter API base URL
        model: Model identifier (default: anthropic/claude-sonnet-4.5)
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum retry attempts (default: 3)
    """

    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "anthropic/claude-sonnet-4.5"
    timeout: float = 60.0
    max_retries: int = 3

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send chat completion request to OpenRouter API with retry logic.

        Implements exponential backoff retry for transient failures (rate limits,
        server errors, network issues). Auth errors fail immediately without retry.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            API response dictionary with completion, includes:
            - choices[0].message.content: Response text
            - usage: Token usage statistics
            - model: Model used for completion

        Raises:
            OpenRouterAuthError: If API key is invalid (401/403)
            OpenRouterRateLimitError: If rate limit exceeded after retries
            OpenRouterServerError: If server error persists after retries
            httpx.HTTPError: For network errors after retries

        Example:
            >>> client = OpenRouterClient(api_key="sk-...")
            >>> response = await client.chat_completion(
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
            >>> print(response["choices"][0]["message"]["content"])
            "Hi! How can I help you today?"
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                # Create async HTTP client with timeout
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Build request payload
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }

                    # Send POST request to OpenRouter API
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._get_headers(),
                        json=payload,
                    )

                    # Handle error responses
                    if not response.is_success:
                        self._handle_error_response(response)

                    # Parse and return successful response
                    result: dict[str, Any] = response.json()
                    return result

            except OpenRouterAuthError:
                # Auth errors are non-retryable - fail immediately
                raise

            except (
                OpenRouterRateLimitError,
                OpenRouterServerError,
                httpx.HTTPError,
            ) as e:
                last_error = e

                # If we have retries left, wait with exponential backoff
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = 2 ** (attempt + 1)
                    await asyncio.sleep(delay)
                # Otherwise, will raise after loop

        # All retries exhausted - raise last error
        if last_error:
            raise last_error
        else:
            raise OpenRouterError("Request failed with unknown error")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for OpenRouter API requests.

        Returns:
            Dictionary of HTTP headers including authorization
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/masa-cloud/edgar-platform",
            "X-Title": "EDGAR Platform",
        }

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from OpenRouter API.

        Args:
            response: HTTP response object

        Raises:
            OpenRouterAuthError: If status is 401 or 403
            OpenRouterRateLimitError: If status is 429
            OpenRouterServerError: If status is 5xx
            OpenRouterError: For other error statuses
        """
        status = response.status_code

        if status in (401, 403):
            raise OpenRouterAuthError(
                f"Authentication failed (status {status}): {response.text}"
            )
        elif status == 429:
            raise OpenRouterRateLimitError(
                f"Rate limit exceeded (status {status}): {response.text}"
            )
        elif 500 <= status < 600:
            raise OpenRouterServerError(
                f"Server error (status {status}): {response.text}"
            )
        else:
            raise OpenRouterError(
                f"API error (status {status}): {response.text}"
            )
