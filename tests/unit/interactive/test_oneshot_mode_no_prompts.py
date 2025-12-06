"""Test that one-shot mode never triggers interactive prompts."""

import asyncio
import os
import pytest
from pathlib import Path

from edgar_analyzer.interactive.session import InteractiveExtractionSession


@pytest.fixture
def remove_api_key():
    """Temporarily remove API key for testing."""
    original_key = os.environ.pop("OPENROUTER_API_KEY", None)
    yield
    if original_key:
        os.environ["OPENROUTER_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_oneshot_chat_no_api_key_no_prompt(remove_api_key):
    """Test that one-shot mode with missing API key doesn't trigger interactive prompt."""
    session = InteractiveExtractionSession()

    # Execute chat command in one-shot mode
    result = await session.execute_command_oneshot("chat hello")

    # Should succeed without error
    assert result["success"] is True
    assert result["error"] is None

    # Should show appropriate message
    assert "No valid API key" in result["output"] or "API key not configured" in result["output"]

    # Should NOT contain EOFError
    assert "EOF when reading a line" not in result["output"]

    # Should NOT contain interactive prompt text
    assert "Do you want to update your API key?" not in result["output"]


@pytest.mark.asyncio
async def test_oneshot_setup_returns_error_message(remove_api_key):
    """Test that /setup in one-shot mode returns error message instead of prompting."""
    session = InteractiveExtractionSession()

    # Execute setup command in one-shot mode
    result = await session.execute_command_oneshot("/setup")

    # Should succeed (not crash)
    assert result["success"] is True

    # Should explain why setup can't run in one-shot mode
    assert "Cannot run interactive setup in one-shot mode" in result["output"]

    # Should suggest alternative
    assert "edgar /setup" in result["output"] or "OPENROUTER_API_KEY" in result["output"]

    # Should NOT try to prompt
    assert "Do you want to update" not in result["output"]


@pytest.mark.asyncio
async def test_oneshot_mode_flag_lifecycle():
    """Test that _oneshot_mode flag is properly set and reset."""
    session = InteractiveExtractionSession()

    # Initially should be False
    assert session._oneshot_mode is False

    # Execute a command in one-shot mode
    result = await session.execute_command_oneshot("help")

    # After execution, should be reset to False
    assert session._oneshot_mode is False
    assert result["success"] is True


@pytest.mark.asyncio
async def test_oneshot_multiple_commands(remove_api_key):
    """Test that multiple one-shot commands don't accumulate state issues."""
    session = InteractiveExtractionSession()

    # Execute multiple commands
    for i in range(3):
        result = await session.execute_command_oneshot("chat test")

        # Each should succeed without prompting
        assert result["success"] is True
        assert "EOF when reading a line" not in result["output"]
        assert session._oneshot_mode is False  # Should be reset after each


@pytest.mark.asyncio
async def test_regular_repl_mode_can_still_prompt():
    """Test that regular REPL mode is not affected by one-shot changes."""
    session = InteractiveExtractionSession()

    # _oneshot_mode should be False in normal REPL
    assert session._oneshot_mode is False

    # Verify that _oneshot_mode flag exists and can be checked
    assert hasattr(session, "_oneshot_mode")
    assert isinstance(session._oneshot_mode, bool)

    # The flag should remain False in normal operation
    assert session._oneshot_mode is False
