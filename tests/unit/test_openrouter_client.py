"""Unit tests for OpenRouterClient."""

import pytest
from unittest.mock import Mock, AsyncMock

from edgar.services.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
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

    def test_client_initialization(self, client: OpenRouterClient) -> None:
        """Test client initializes with correct attributes."""
        assert client.api_key == "test-key"
        assert client.base_url == "https://openrouter.ai/api/v1"
        assert client.model == "anthropic/claude-sonnet-4.5"
        assert client.timeout == 60.0

    def test_get_headers(self, client: OpenRouterClient) -> None:
        """Test HTTP headers include authorization."""
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_chat_completion_not_implemented(
        self,
        client: OpenRouterClient,
    ) -> None:
        """Test chat_completion raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await client.chat_completion(
                messages=[{"role": "user", "content": "test"}],
            )
