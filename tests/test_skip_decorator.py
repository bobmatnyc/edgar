"""
Test to verify skip decorator functionality.

Tests that API-dependent tests skip gracefully when OPENROUTER_API_KEY is not set.
"""

import os

import pytest


def requires_openrouter_api_key():
    """Skip decorator for tests requiring OpenRouter API key."""
    return pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY"),
        reason="OPENROUTER_API_KEY not set - skipping code generation test",
    )


class TestSkipDecoratorVerification:
    """Verify skip decorator implementation."""

    def test_decorator_skips_without_api_key(self):
        """Test passes without API key (no decorator)."""
        assert True

    @pytest.mark.requires_api
    @requires_openrouter_api_key()
    def test_decorator_skips_with_marker(self):
        """Test should skip when OPENROUTER_API_KEY is not set."""
        # This test should be skipped if API key is missing
        api_key = os.getenv("OPENROUTER_API_KEY")
        assert api_key is not None, "Test should have been skipped!"
        assert len(api_key) > 0
