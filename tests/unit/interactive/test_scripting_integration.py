"""
Tests for scripting engine integration with interactive chat mode.

Verifies that the Dynamic Scripting Engine is properly integrated
with the interactive session for ad-hoc file management tasks.
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from edgar_analyzer.interactive.session import InteractiveExtractionSession
from cli_chatbot.core.scripting_engine import DynamicScriptingEngine
from cli_chatbot.core.interfaces import ScriptResult


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary test directory."""
    return tmp_path


@pytest.fixture
def session(temp_test_dir):
    """Create test session instance."""
    session = InteractiveExtractionSession(
        project_path=temp_test_dir,
        test_mode=True  # Disable interactive prompts
    )
    return session


class TestScriptingEngineInitialization:
    """Test that scripting engine is properly initialized."""

    def test_scripting_engine_exists(self, session):
        """Verify scripting engine is initialized."""
        assert hasattr(session, 'scripting_engine')
        assert session.scripting_engine is not None
        assert isinstance(session.scripting_engine, DynamicScriptingEngine)

    def test_scripting_engine_config(self, session):
        """Verify scripting engine has correct configuration."""
        engine = session.scripting_engine

        # Check allowed imports include file operation modules
        assert 'os' in engine.allowed_imports
        assert 'pathlib' in engine.allowed_imports
        assert 'shutil' in engine.allowed_imports
        assert 'zipfile' in engine.allowed_imports
        assert 'glob' in engine.allowed_imports

        # Check execution settings
        assert engine.max_execution_time == 30.0
        assert engine.prefer_subprocess is True


class TestScriptExtraction:
    """Test script extraction from AI responses."""

    @pytest.mark.asyncio
    async def test_extract_single_script(self, session):
        """Test extracting single python:execute block."""
        response = """Here's a script to create directories:

```python:execute
from pathlib import Path

project_dir = Path("test_project")
project_dir.mkdir(exist_ok=True)

result = f"Created {project_dir}"
```

The script creates a project directory.
"""

        # Mock the scripting engine to avoid actual execution
        mock_result = ScriptResult(
            success=True,
            result="Created test_project",
            output="",
            error=None,
            execution_time=0.1,
            side_effects=[]
        )

        with patch.object(session.scripting_engine, 'execute_script', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result

            await session._execute_scripts_from_response(response)

            # Verify script was executed
            assert mock_exec.called
            call_args = mock_exec.call_args
            assert 'project_dir = Path("test_project")' in call_args[1]['script_code']

    @pytest.mark.asyncio
    async def test_extract_multiple_scripts(self, session):
        """Test extracting multiple python:execute blocks."""
        response = """First, create directory:

```python:execute
from pathlib import Path
Path("dir1").mkdir(exist_ok=True)
result = "Created dir1"
```

Then create another:

```python:execute
from pathlib import Path
Path("dir2").mkdir(exist_ok=True)
result = "Created dir2"
```

Done!
"""

        mock_result = ScriptResult(
            success=True,
            result="Created directory",
            output="",
            error=None,
            execution_time=0.1,
            side_effects=[]
        )

        with patch.object(session.scripting_engine, 'execute_script', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result

            await session._execute_scripts_from_response(response)

            # Verify both scripts were executed
            assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_no_scripts_in_response(self, session):
        """Test handling response with no scripts."""
        response = "This is a normal response with no scripts."

        with patch.object(session.scripting_engine, 'execute_script', new_callable=AsyncMock) as mock_exec:
            await session._execute_scripts_from_response(response)

            # Verify no execution attempted
            assert not mock_exec.called


class TestScriptExecution:
    """Test actual script execution."""

    @pytest.mark.asyncio
    async def test_successful_script_execution(self, session, temp_test_dir):
        """Test successful script execution with file operations."""
        script_code = f"""
from pathlib import Path

test_dir = Path("{temp_test_dir}") / "test_output"
test_dir.mkdir(exist_ok=True)

result = f"Created directory at {{test_dir}}"
"""

        result = await session.scripting_engine.execute_script(
            script_code=script_code,
            context={},
            safety_checks=True
        )

        # Verify execution succeeded
        assert result.success is True
        assert result.error is None
        assert "Created directory at" in result.result

        # Verify directory was actually created
        assert (temp_test_dir / "test_output").exists()

    @pytest.mark.asyncio
    async def test_script_with_context(self, session, temp_test_dir):
        """Test script execution with injected context."""
        script_code = """
from pathlib import Path

# Use injected context
base_path = Path(project_path) if project_path else Path(".")
output_dir = base_path / "output"
output_dir.mkdir(exist_ok=True)

result = f"Created output at {output_dir}"
"""

        context = {
            "project_path": str(temp_test_dir),
            "session_id": "test-session-123"
        }

        result = await session.scripting_engine.execute_script(
            script_code=script_code,
            context=context,
            safety_checks=True
        )

        # Verify execution succeeded with context
        assert result.success is True
        assert "Created output at" in result.result

        # Verify directory was created at correct location
        assert (temp_test_dir / "output").exists()

    @pytest.mark.asyncio
    async def test_failed_script_execution(self, session):
        """Test handling of script execution failures."""
        script_code = """
# This will fail - division by zero
x = 1 / 0
result = "Should not reach here"
"""

        result = await session.scripting_engine.execute_script(
            script_code=script_code,
            context={},
            safety_checks=True
        )

        # Verify execution failed
        assert result.success is False
        assert result.error is not None
        assert "ZeroDivisionError" in result.error or "division" in result.error.lower()

    @pytest.mark.asyncio
    async def test_unsafe_script_rejected(self, session):
        """Test that unsafe scripts are rejected by safety checks."""
        # Try to use eval (blocked operation)
        script_code = """
# This should be blocked by safety checks
result = eval("1 + 1")
"""

        result = await session.scripting_engine.execute_script(
            script_code=script_code,
            context={},
            safety_checks=True
        )

        # Verify execution was blocked
        assert result.success is False
        assert result.error is not None
        assert "safety validation" in result.error.lower()


class TestChatIntegration:
    """Test integration with chat command."""

    @pytest.mark.asyncio
    async def test_chat_with_file_operation_request(self, session, temp_test_dir):
        """Test chat command triggers script execution for file operations."""
        # Mock OpenRouter client to return script-containing response
        mock_response = f"""I'll create a project directory for you:

```python:execute
from pathlib import Path

project_dir = Path("{temp_test_dir}") / "my_project"
project_dir.mkdir(exist_ok=True)

# Create subdirectories
(project_dir / "input").mkdir(exist_ok=True)
(project_dir / "output").mkdir(exist_ok=True)

result = f"Created project at {{project_dir}}"
```

Your project is ready!
"""

        with patch.object(session.openrouter_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            # Execute chat command
            await session.cmd_chat("create a project called my_project")

            # Verify OpenRouter was called
            assert mock_chat.called

            # Verify directories were created
            project_dir = temp_test_dir / "my_project"
            assert project_dir.exists()
            assert (project_dir / "input").exists()
            assert (project_dir / "output").exists()


class TestSystemPrompt:
    """Test that system prompt includes file operation instructions."""

    @pytest.mark.asyncio
    async def test_system_prompt_has_file_operations(self, session):
        """Verify system prompt includes file operation capabilities."""
        # Trigger chat to access system prompt construction
        with patch.object(session.openrouter_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "Test response"

            await session.cmd_chat("test message")

            # Get the system prompt from the call
            call_args = mock_chat.call_args
            messages = call_args[1]['messages']
            system_message = next((m for m in messages if m['role'] == 'system'), None)

            assert system_message is not None
            system_prompt = system_message['content']

            # Verify file operation capabilities are mentioned
            assert "File Operations" in system_prompt
            assert "python:execute" in system_prompt
            assert "Create directories" in system_prompt
            assert "Copy/move files" in system_prompt
            assert "Unzip archives" in system_prompt


@pytest.mark.asyncio
async def test_end_to_end_file_operation(tmp_path):
    """End-to-end test of file operation via chat."""
    # Create session
    session = InteractiveExtractionSession(
        project_path=tmp_path,
        test_mode=True
    )

    # Create a test file to copy
    source_file = tmp_path / "test.txt"
    source_file.write_text("Test content")

    # Simulate AI response with copy operation
    mock_response = f"""I'll copy the file for you:

```python:execute
import shutil
from pathlib import Path

source = Path("{source_file}")
dest = Path("{tmp_path}") / "copied.txt"

shutil.copy2(source, dest)

result = f"Copied {{source.name}} to {{dest}}"
```

File copied successfully!
"""

    with patch.object(session.openrouter_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response

        # Execute chat command
        await session.cmd_chat("copy test.txt to copied.txt")

        # Verify file was copied
        copied_file = tmp_path / "copied.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "Test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
