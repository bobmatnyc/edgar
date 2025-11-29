"""Unit tests for OpenRouterClient.

Tests cover:
1. Successful API requests
2. Authentication errors (401/403) - no retry
3. Rate limit errors (429) - retry with backoff
4. Server errors (5xx) - retry with backoff
5. Network errors - retry with backoff
6. Exponential backoff timing validation
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from edgar.services.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterServerError,
    # Legacy aliases
    AuthenticationError,
    RateLimitError,
    APIError,
)


class TestOpenRouterClient:
    """Test suite for OpenRouterClient."""

    @pytest.fixture
    def client(self) -> OpenRouterClient:
        """Create OpenRouterClient instance."""
        return OpenRouterClient(api_key="test-key")

    @pytest.fixture
    def mock_response_success(self) -> dict:
        """Mock successful OpenRouter API response."""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "anthropic/claude-sonnet-4.5",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

    def test_client_initialization(self, client: OpenRouterClient) -> None:
        """Test client initializes with correct attributes."""
        assert client.api_key == "test-key"
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert client.model == "anthropic/claude-sonnet-4.5"
        assert client.timeout == 60.0
        assert client.max_retries == 3

    def test_custom_initialization(self) -> None:
        """Test client with custom parameters."""
        client = OpenRouterClient(
            api_key="custom-key",
            base_url="https://custom.api",
            model="custom-model",
            timeout=30.0,
            max_retries=5,
        )
        assert client.api_key == "custom-key"
        assert client.base_url == "https://custom.api"
        assert client.model == "custom-model"
        assert client.timeout == 30.0
        assert client.max_retries == 5

    def test_get_headers(self, client: OpenRouterClient) -> None:
        """Test HTTP headers include all required fields."""
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["HTTP-Referer"] == "https://github.com/masa-cloud/edgar-platform"
        assert headers["X-Title"] == "EDGAR Platform"

    def test_handle_error_401(self, client: OpenRouterClient) -> None:
        """Test 401 error raises OpenRouterAuthError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"

        with pytest.raises(OpenRouterAuthError) as exc_info:
            client._handle_error_response(mock_response)

        assert "Authentication failed" in str(exc_info.value)
        assert "401" in str(exc_info.value)

    def test_handle_error_403(self, client: OpenRouterClient) -> None:
        """Test 403 error raises OpenRouterAuthError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        with pytest.raises(OpenRouterAuthError) as exc_info:
            client._handle_error_response(mock_response)

        assert "Authentication failed" in str(exc_info.value)
        assert "403" in str(exc_info.value)

    def test_handle_error_429(self, client: OpenRouterClient) -> None:
        """Test 429 error raises OpenRouterRateLimitError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.text = "Too many requests"

        with pytest.raises(OpenRouterRateLimitError) as exc_info:
            client._handle_error_response(mock_response)

        assert "Rate limit exceeded" in str(exc_info.value)
        assert "429" in str(exc_info.value)

    def test_handle_error_500(self, client: OpenRouterClient) -> None:
        """Test 500 error raises OpenRouterServerError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with pytest.raises(OpenRouterServerError) as exc_info:
            client._handle_error_response(mock_response)

        assert "Server error" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    def test_handle_error_502(self, client: OpenRouterClient) -> None:
        """Test 502 error raises OpenRouterServerError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 502
        mock_response.text = "Bad gateway"

        with pytest.raises(OpenRouterServerError):
            client._handle_error_response(mock_response)

    def test_handle_error_other(self, client: OpenRouterClient) -> None:
        """Test other errors raise generic OpenRouterError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with pytest.raises(OpenRouterError) as exc_info:
            client._handle_error_response(mock_response)

        assert "API error" in str(exc_info.value)
        assert "400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_completion_success(
        self,
        client: OpenRouterClient,
        mock_response_success: dict,
    ) -> None:
        """Test successful chat completion request."""
        # Mock httpx.AsyncClient
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = mock_response_success

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Make request
            messages = [{"role": "user", "content": "Hello"}]
            response = await client.chat_completion(messages)

            # Verify response
            assert response == mock_response_success
            assert response["choices"][0]["message"]["content"] == "Hello! How can I help you today?"

            # Verify request was made correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args

            # Check URL
            assert call_args[0][0] == "https://openrouter.ai/api/v1/chat/completions"

            # Check headers
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer test-key"
            assert headers["X-Title"] == "EDGAR Platform"

            # Check payload
            payload = call_args[1]["json"]
            assert payload["model"] == "anthropic/claude-sonnet-4.5"
            assert payload["messages"] == messages
            assert payload["temperature"] == 0.7
            assert payload["max_tokens"] == 4096

    @pytest.mark.asyncio
    async def test_chat_completion_custom_params(
        self,
        client: OpenRouterClient,
        mock_response_success: dict,
    ) -> None:
        """Test chat completion with custom temperature and max_tokens."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = True
        mock_response.json.return_value = mock_response_success

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Make request with custom params
            await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.5,
                max_tokens=2000,
            )

            # Verify custom params were sent
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["temperature"] == 0.5
            assert payload["max_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_chat_completion_auth_error_no_retry(
        self,
        client: OpenRouterClient,
    ) -> None:
        """Test auth error (401) fails immediately without retry."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should raise auth error immediately
            with pytest.raises(OpenRouterAuthError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Test"}]
                )

            # Verify only 1 attempt (no retries)
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_chat_completion_rate_limit_retry(
        self,
        client: OpenRouterClient,
        mock_response_success: dict,
    ) -> None:
        """Test rate limit (429) retries with exponential backoff."""
        # Mock rate limit on first 2 attempts, success on 3rd
        mock_rate_limit = Mock(spec=httpx.Response)
        mock_rate_limit.is_success = False
        mock_rate_limit.status_code = 429
        mock_rate_limit.text = "Too many requests"

        mock_success = Mock(spec=httpx.Response)
        mock_success.is_success = True
        mock_success.json.return_value = mock_response_success

        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep") as mock_sleep:
            mock_client = AsyncMock()
            # First 2 calls return rate limit, 3rd succeeds
            mock_client.post.side_effect = [
                mock_rate_limit,
                mock_rate_limit,
                mock_success,
            ]
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should succeed after retries
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )

            # Verify response
            assert response == mock_response_success

            # Verify 3 attempts
            assert mock_client.post.call_count == 3

            # Verify exponential backoff delays: 2s, 4s
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0][0][0] == 2  # 2^1
            assert mock_sleep.call_args_list[1][0][0] == 4  # 2^2

    @pytest.mark.asyncio
    async def test_chat_completion_rate_limit_max_retries(
        self,
        client: OpenRouterClient,
    ) -> None:
        """Test rate limit exhausts all retries and raises error."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 429
        mock_response.text = "Too many requests"

        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep"):
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should raise after max retries
            with pytest.raises(OpenRouterRateLimitError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Test"}]
                )

            # Verify 3 attempts (max_retries)
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_chat_completion_server_error_retry(
        self,
        client: OpenRouterClient,
        mock_response_success: dict,
    ) -> None:
        """Test server error (500) retries and recovers."""
        mock_error = Mock(spec=httpx.Response)
        mock_error.is_success = False
        mock_error.status_code = 500
        mock_error.text = "Internal server error"

        mock_success = Mock(spec=httpx.Response)
        mock_success.is_success = True
        mock_success.json.return_value = mock_response_success

        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep"):
            mock_client = AsyncMock()
            # First call fails, second succeeds
            mock_client.post.side_effect = [mock_error, mock_success]
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should succeed after retry
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )

            assert response == mock_response_success
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_completion_network_error_retry(
        self,
        client: OpenRouterClient,
        mock_response_success: dict,
    ) -> None:
        """Test network error retries and recovers."""
        mock_success = Mock(spec=httpx.Response)
        mock_success.is_success = True
        mock_success.json.return_value = mock_response_success

        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep"):
            mock_client = AsyncMock()
            # First call raises network error, second succeeds
            mock_client.post.side_effect = [
                httpx.NetworkError("Connection refused"),
                mock_success,
            ]
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should succeed after retry
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )

            assert response == mock_response_success
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_completion_network_error_max_retries(
        self,
        client: OpenRouterClient,
    ) -> None:
        """Test network error exhausts retries and raises."""
        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep"):
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.NetworkError("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should raise after max retries
            with pytest.raises(httpx.NetworkError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Test"}]
                )

            # Verify 3 attempts
            assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(
        self,
        client: OpenRouterClient,
    ) -> None:
        """Test exponential backoff uses correct delays."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Error"

        with patch("httpx.AsyncClient") as mock_client_class, \
             patch("asyncio.sleep") as mock_sleep:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should fail after retries
            with pytest.raises(OpenRouterServerError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Test"}]
                )

            # Verify backoff delays: 2s (2^1), 4s (2^2), 8s (2^3) - but only 2 sleeps (3 attempts)
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0][0][0] == 2  # First retry
            assert mock_sleep.call_args_list[1][0][0] == 4  # Second retry

    def test_legacy_exception_aliases(self) -> None:
        """Test legacy exception names are still available."""
        # These should be the same classes
        assert AuthenticationError is OpenRouterAuthError
        assert RateLimitError is OpenRouterRateLimitError
        assert APIError is OpenRouterError
