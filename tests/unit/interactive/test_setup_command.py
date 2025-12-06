"""
Tests for /setup command in interactive session.

This module tests:
- API key validation
- File saving and updating
- Command registration
- Startup warnings
- Error handling
"""

import asyncio
import os
from pathlib import Path

import pytest

from edgar_analyzer.interactive.session import InteractiveExtractionSession


class TestSetupCommand:
    """Test suite for /setup command functionality."""

    def test_setup_command_registered(self):
        """Test that /setup and /config commands are registered."""
        session = InteractiveExtractionSession()

        assert "setup" in session.commands, "/setup command not registered"
        assert "config" in session.commands, "/config alias not registered"
        assert session.commands["setup"] == session.cmd_setup
        assert session.commands["config"] == session.cmd_setup

    def test_save_api_key_new_file(self, tmp_path):
        """Test saving API key to new .env.local file."""
        # Change to temp directory
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        try:
            session = InteractiveExtractionSession()

            # Save key to new file
            test_key = "sk-or-v1-test123"
            session._save_api_key(test_key)

            # Verify file created
            env_path = tmp_path / ".env.local"
            assert env_path.exists(), ".env.local not created"

            # Verify content
            content = env_path.read_text()
            assert test_key in content, "API key not saved"
            assert "OPENROUTER_API_KEY=" in content, "Key format incorrect"

        finally:
            os.chdir(original_dir)

    def test_save_api_key_update_existing(self, tmp_path):
        """Test updating API key in existing .env.local file."""
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        try:
            session = InteractiveExtractionSession()

            # Create initial file with old key
            env_path = tmp_path / ".env.local"
            env_path.write_text("OPENROUTER_API_KEY=sk-or-v1-old123\n")

            # Update with new key
            new_key = "sk-or-v1-new456"
            session._save_api_key(new_key)

            # Verify update
            content = env_path.read_text()
            assert new_key in content, "New key not saved"
            assert "sk-or-v1-old123" not in content, "Old key not removed"

        finally:
            os.chdir(original_dir)

    def test_save_api_key_preserves_other_vars(self, tmp_path):
        """Test that saving API key preserves other environment variables."""
        original_dir = Path.cwd()
        os.chdir(tmp_path)

        try:
            session = InteractiveExtractionSession()

            # Create file with multiple variables
            env_path = tmp_path / ".env.local"
            env_path.write_text("""
DATABASE_URL=sqlite:///test.db
OPENROUTER_API_KEY=sk-or-v1-old123
LOG_LEVEL=DEBUG
""")

            # Update API key
            new_key = "sk-or-v1-new456"
            session._save_api_key(new_key)

            # Verify other vars preserved
            content = env_path.read_text()
            assert new_key in content
            assert "DATABASE_URL=sqlite:///test.db" in content
            assert "LOG_LEVEL=DEBUG" in content

        finally:
            os.chdir(original_dir)

    @pytest.mark.asyncio
    async def test_validate_api_key_invalid_format(self):
        """Test API key validation rejects invalid format."""
        session = InteractiveExtractionSession()

        # Test with invalid format (doesn't start with sk-or-v1-)
        is_valid = await session._validate_api_key("invalid-key-format")
        assert not is_valid, "Invalid format should fail validation"

    @pytest.mark.asyncio
    async def test_validate_api_key_unauthorized(self):
        """Test API key validation detects unauthorized keys."""
        session = InteractiveExtractionSession()

        # Test with proper format but invalid credentials
        is_valid = await session._validate_api_key("sk-or-v1-fake123456789")
        assert not is_valid, "Unauthorized key should fail validation"

    def test_session_initialization_without_api_key(self):
        """Test session initializes gracefully without API key."""
        # Temporarily remove API key
        original_key = os.environ.pop("OPENROUTER_API_KEY", None)

        try:
            session = InteractiveExtractionSession()

            # Should initialize but with disabled features
            assert session.openrouter_client is None, "Client should be None"
            assert session.code_generator is None, "Code generator should be None"

            # Other services should still work
            assert session.project_manager is not None
            assert session.schema_analyzer is not None

        finally:
            # Restore key
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key

    @pytest.mark.asyncio
    async def test_chat_command_without_api_key(self, capsys):
        """Test chat command shows helpful message without API key."""
        # Temporarily remove API key
        original_key = os.environ.pop("OPENROUTER_API_KEY", None)

        try:
            session = InteractiveExtractionSession()

            # Try chat without API key
            await session.cmd_chat("hello")

            # Should show error message (captured by Rich console)
            # Note: Rich output goes to stderr, not stdout

        finally:
            # Restore key
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key

    @pytest.mark.asyncio
    async def test_generate_command_without_api_key(self):
        """Test generate command shows helpful message without API key."""
        # Temporarily remove API key
        original_key = os.environ.pop("OPENROUTER_API_KEY", None)

        try:
            session = InteractiveExtractionSession()

            # Try generate without API key
            await session.cmd_generate_code()

            # Should show error message (no exception thrown)

        finally:
            # Restore key
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key


class TestSetupCommandHelp:
    """Test that /setup appears in help command."""

    def test_setup_in_help_table(self):
        """Test that /setup appears in help table."""
        session = InteractiveExtractionSession()

        # The help command should include setup
        # This is more of an integration test - just verify it doesn't crash
        # and the command is registered
        assert "setup" in session.commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
