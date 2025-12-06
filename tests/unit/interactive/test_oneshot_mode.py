"""
Tests for one-shot command execution mode.

Tests the execute_command_oneshot() method and session GUID functionality.
"""

import json
import pytest
from pathlib import Path

from edgar_analyzer.interactive.session import InteractiveExtractionSession


@pytest.mark.asyncio
async def test_oneshot_help_command():
    """Test one-shot execution of help command."""
    session = InteractiveExtractionSession(test_mode=True)

    result = await session.execute_command_oneshot("help")

    assert result["success"] is True
    assert result["session_id"].startswith("edgar-")
    assert "Available Commands" in result["output"]
    assert result["error"] is None


@pytest.mark.asyncio
async def test_oneshot_threshold_command():
    """Test one-shot execution of threshold command."""
    session = InteractiveExtractionSession(test_mode=True)

    result = await session.execute_command_oneshot("threshold")

    assert result["success"] is True
    assert result["session_id"].startswith("edgar-")
    assert "No project loaded" in result["output"]
    assert result["error"] is None


@pytest.mark.asyncio
async def test_oneshot_unknown_command():
    """Test one-shot execution with unknown command."""
    session = InteractiveExtractionSession(test_mode=True)

    result = await session.execute_command_oneshot("foobar")

    assert result["success"] is False
    assert result["error"] == "Unknown command: foobar"
    assert "Unknown command: foobar" in result["output"]


@pytest.mark.asyncio
async def test_oneshot_slash_command():
    """Test one-shot execution with slash-prefixed command."""
    session = InteractiveExtractionSession(test_mode=True)

    result = await session.execute_command_oneshot("/help")

    assert result["success"] is True
    assert "Available Commands" in result["output"]


@pytest.mark.asyncio
async def test_oneshot_sessions_command():
    """Test one-shot execution of sessions command."""
    session = InteractiveExtractionSession(test_mode=True)

    result = await session.execute_command_oneshot("sessions")

    assert result["success"] is True
    assert result["session_id"].startswith("edgar-")
    # Output may be "No saved sessions" or a table


@pytest.mark.asyncio
async def test_session_id_generation():
    """Test that session IDs are generated correctly."""
    session1 = InteractiveExtractionSession(test_mode=True)
    session2 = InteractiveExtractionSession(test_mode=True)

    # Session IDs should be unique
    assert session1.session_id != session2.session_id

    # Session IDs should follow format: edgar-YYYYMMDD-HHMMSS-UUID
    assert session1.session_id.startswith("edgar-")
    assert len(session1.session_id.split("-")) == 4

    # Last part should be 8-character UUID
    uuid_part = session1.session_id.split("-")[-1]
    assert len(uuid_part) == 8


@pytest.mark.asyncio
async def test_session_id_persistence():
    """Test that session ID is persisted in session save."""
    session = InteractiveExtractionSession(test_mode=True)

    # Execute command to trigger auto-save
    result = await session.execute_command_oneshot("help")

    # Check that session file was created
    session_file = Path.home() / ".edgar" / "sessions" / f"{result['session_id']}_session.json"
    assert session_file.exists()

    # Check that session file contains session_id
    with open(session_file, 'r') as f:
        session_data = json.load(f)

    assert session_data["session_id"] == result["session_id"]
    assert session_data["session_id"].startswith("edgar-")

    # Cleanup
    session_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_session_id_resume():
    """Test that session ID can be used to resume sessions."""
    # Create initial session
    session1 = InteractiveExtractionSession(test_mode=True)
    original_id = session1.session_id

    # Execute command and save
    await session1.execute_command_oneshot("help")

    # Create new session with same ID
    session2 = InteractiveExtractionSession(test_mode=True, session_id=original_id)

    # Session ID should be preserved
    assert session2.session_id == original_id

    # Cleanup
    session_file = Path.home() / ".edgar" / "sessions" / f"{original_id}_session.json"
    session_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_oneshot_command_result_structure():
    """Test that one-shot command result has correct structure."""
    session = InteractiveExtractionSession(test_mode=True)

    result = await session.execute_command_oneshot("help")

    # Check all required keys are present
    assert "session_id" in result
    assert "command" in result
    assert "success" in result
    assert "output" in result
    assert "error" in result

    # Check types
    assert isinstance(result["session_id"], str)
    assert isinstance(result["command"], str)
    assert isinstance(result["success"], bool)
    assert isinstance(result["output"], str)
    assert result["error"] is None or isinstance(result["error"], str)
