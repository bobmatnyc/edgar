"""Tests for setup CLI commands."""
import asyncio
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, AsyncMock

from edgar_analyzer.cli.commands.setup import setup, _test_openrouter, _test_jina


class TestSetupTestCommand:
    """Test setup test command."""

    def test_openrouter_success(self, monkeypatch):
        """Test successful OpenRouter connection."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-12345")

        # Mock OpenRouterClient
        with patch('extract_transform_platform.ai.openrouter_client.OpenRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client.chat_completion = AsyncMock(return_value="Test response")
            mock_client_class.return_value = mock_client

            result = _test_openrouter()
            assert result is True

    def test_openrouter_missing_key(self, monkeypatch):
        """Test OpenRouter with missing API key."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        result = _test_openrouter()
        assert result is False

    def test_openrouter_api_failure(self, monkeypatch):
        """Test OpenRouter API failure."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-12345")

        # Mock OpenRouterClient that raises exception
        with patch('extract_transform_platform.ai.openrouter_client.OpenRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client.chat_completion = AsyncMock(side_effect=Exception("API Error"))
            mock_client_class.return_value = mock_client

            result = _test_openrouter()
            assert result is False

    def test_jina_missing_key(self, monkeypatch):
        """Test Jina.ai with missing API key (should pass as optional)."""
        monkeypatch.delenv("JINA_API_KEY", raising=False)

        result = _test_jina()
        assert result is True  # Optional service

    def test_jina_success(self, monkeypatch):
        """Test successful Jina.ai connection."""
        monkeypatch.setenv("JINA_API_KEY", "jina_test_key_12345")

        # Mock httpx client
        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            mock_client_class.return_value = mock_client

            result = _test_jina()
            assert result is True

    def test_cli_command_all_services(self, monkeypatch):
        """Test CLI command with all services."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        monkeypatch.delenv("JINA_API_KEY", raising=False)

        runner = CliRunner()

        with patch('edgar_analyzer.cli.commands.setup._test_openrouter', return_value=True), \
             patch('edgar_analyzer.cli.commands.setup._test_jina', return_value=True):

            result = runner.invoke(setup, ['test', '--service', 'all'])
            assert result.exit_code == 0
            assert "All services operational" in result.output

    def test_cli_command_openrouter_only(self, monkeypatch):
        """Test CLI command with OpenRouter only."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")

        runner = CliRunner()

        with patch('edgar_analyzer.cli.commands.setup._test_openrouter', return_value=True):
            result = runner.invoke(setup, ['test', '--service', 'openrouter'])
            assert result.exit_code == 0
            assert "✅ PASS" in result.output

    def test_cli_command_failure(self, monkeypatch):
        """Test CLI command with service failure."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        runner = CliRunner()

        with patch('edgar_analyzer.cli.commands.setup._test_openrouter', return_value=False), \
             patch('edgar_analyzer.cli.commands.setup._test_jina', return_value=True):

            result = runner.invoke(setup, ['test', '--service', 'all'])
            assert result.exit_code == 1  # Abort
            assert "Some services failed" in result.output
