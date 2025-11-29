"""Unit tests for Sonnet4_5Service."""

import pytest
from unittest.mock import Mock, AsyncMock

from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager


class TestSonnet4_5Service:
    """Test suite for Sonnet4_5Service."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create mock OpenRouter client."""
        client = Mock(spec=OpenRouterClient)
        client.chat_completion = AsyncMock()
        return client

    @pytest.fixture
    def context_manager(self) -> ContextManager:
        """Create context manager."""
        return ContextManager(max_messages=10)

    @pytest.fixture
    def service(
        self,
        mock_client: Mock,
        context_manager: ContextManager,
    ) -> Sonnet4_5Service:
        """Create Sonnet4_5Service instance."""
        return Sonnet4_5Service(
            client=mock_client,
            context=context_manager,
        )

    @pytest.mark.asyncio
    async def test_analyze_examples_not_implemented(
        self,
        service: Sonnet4_5Service,
    ) -> None:
        """Test analyze_examples raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await service.analyze_examples(
                examples=[{"temp": 72}],
                target_schema=dict,
            )

    @pytest.mark.asyncio
    async def test_generate_code_not_implemented(
        self,
        service: Sonnet4_5Service,
    ) -> None:
        """Test generate_code raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await service.generate_code(
                strategy={"data_source_type": "REST_API"},
                constraints={},
            )
