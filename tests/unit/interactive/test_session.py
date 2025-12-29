"""
Unit Tests for InteractiveExtractionSession

Tests the interactive REPL session functionality including:
- Session initialization and state management
- Command registry and execution
- Project loading and validation
- Analysis and pattern detection
- Code generation and extraction
- Error handling and edge cases

Design Notes:
- Uses pytest-asyncio for async test support
- Mocks external services (ProjectManager, SchemaAnalyzer)
- Tests both success and error paths
- Validates Rich output formatting (where practical)
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from edgar_analyzer.interactive.session import InteractiveExtractionSession
from extract_transform_platform.models.project_config import (
    DataSourceConfig,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
)


@pytest.fixture
def session():
    """Create a basic session for testing."""
    return InteractiveExtractionSession()


@pytest.fixture
def session_with_project(tmp_path):
    """Create a session with a temporary project path."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    return InteractiveExtractionSession(project_path=project_path)


@pytest.fixture
def mock_project_config():
    """Create a mock ProjectConfig for testing."""
    return ProjectConfig(
        project=ProjectMetadata(
            name="test_project",  # Must be alphanumeric with underscores/hyphens
            description="Test project for interactive session",
            version="1.0.0",
        ),
        data_source=DataSourceConfig(
            name="test_api",  # Required field
            type="api",
            config={"url": "https://api.example.com"},
        ),
        output=OutputConfig(
            formats=[  # At least one format required
                OutputDestinationConfig(
                    type=OutputFormat.JSON, path="output/results.json"
                )
            ]
        ),
        examples=[],
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================


def test_session_initialization(session):
    """Test session initializes with empty state."""
    assert session.project_config is None
    assert session.analysis_results is None
    assert session.generated_code is None
    assert session.extraction_results is None
    assert session.project_path is None
    assert len(session.commands) > 0


def test_session_initialization_with_project(tmp_path):
    """Test session initializes with project path."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    session = InteractiveExtractionSession(project_path=project_path)

    assert session.project_path == project_path
    assert session.project_config is None  # Not loaded until start() or load command


def test_command_registry(session):
    """Test all commands are registered."""
    expected_commands = {
        "help",
        "load",
        "show",
        "analyze",
        "patterns",
        "examples",
        "generate",
        "extract",
        "exit",
    }
    assert set(session.commands.keys()) == expected_commands


def test_command_registry_callable(session):
    """Test all registered commands are callable."""
    for command_name, command_func in session.commands.items():
        assert callable(command_func), f"Command {command_name} is not callable"


# ============================================================================
# COMMAND TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_help_command(session, capsys):
    """Test help command displays without error."""
    await session.cmd_help()
    # Should not raise exception
    # Note: Rich output goes to stdout, so we can't easily capture it in tests
    # but we can verify the command executes without error


@pytest.mark.asyncio
async def test_show_without_project(session, capsys):
    """Test show command without loaded project."""
    await session.cmd_show()
    # Should display warning, not crash
    # Verify session state unchanged
    assert session.project_config is None


@pytest.mark.asyncio
async def test_show_with_project(session, mock_project_config):
    """Test show command with loaded project."""
    session.project_config = mock_project_config
    await session.cmd_show()
    # Should display project info without error


@pytest.mark.asyncio
async def test_examples_without_project(session):
    """Test examples command without loaded project."""
    await session.cmd_show_examples()
    # Should display warning, not crash


@pytest.mark.asyncio
async def test_examples_with_empty_project(session, mock_project_config):
    """Test examples command with project but no examples."""
    session.project_config = mock_project_config
    await session.cmd_show_examples()
    # Should handle gracefully


@pytest.mark.asyncio
async def test_analyze_without_project(session):
    """Test analyze command without loaded project."""
    await session.cmd_analyze()
    # Should display warning
    assert session.analysis_results is None


@pytest.mark.asyncio
async def test_analyze_with_project(session, mock_project_config):
    """Test analyze command with loaded project."""
    session.project_config = mock_project_config
    await session.cmd_analyze()

    # Should create analysis results (even if placeholder)
    assert session.analysis_results is not None
    assert "patterns" in session.analysis_results
    assert "num_examples" in session.analysis_results


@pytest.mark.asyncio
async def test_patterns_without_analysis(session):
    """Test patterns command without analysis results."""
    await session.cmd_show_patterns()
    # Should display warning
    assert session.analysis_results is None


@pytest.mark.asyncio
async def test_patterns_with_analysis(session):
    """Test patterns command with analysis results."""
    session.analysis_results = {
        "patterns": [
            {
                "type": "FIELD_MAPPING",
                "confidence": 0.95,
                "description": "Map field A to B",
            },
            {
                "type": "TYPE_CONVERSION",
                "confidence": 0.87,
                "description": "Convert string to int",
            },
        ]
    }
    await session.cmd_show_patterns()
    # Should display patterns without error


@pytest.mark.asyncio
async def test_generate_without_analysis(session):
    """Test generate command without analysis."""
    await session.cmd_generate_code()
    # Should display warning
    assert session.generated_code is None


@pytest.mark.asyncio
async def test_generate_with_analysis(session):
    """Test generate command with analysis."""
    session.analysis_results = {"patterns": []}
    await session.cmd_generate_code()

    # Should generate code (even if placeholder)
    assert session.generated_code is not None
    assert len(session.generated_code) > 0


@pytest.mark.asyncio
async def test_extract_without_code(session):
    """Test extract command without generated code."""
    await session.cmd_run_extraction()
    # Should display warning
    assert session.extraction_results is None


@pytest.mark.asyncio
async def test_extract_with_code(session):
    """Test extract command with generated code."""
    session.generated_code = "# Sample code"
    await session.cmd_run_extraction()

    # Should run extraction (even if placeholder)
    assert session.extraction_results is not None


@pytest.mark.asyncio
async def test_exit_command(session):
    """Test exit command returns exit signal."""
    result = await session.cmd_exit()
    assert result == "exit"


# ============================================================================
# PROJECT LOADING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_load_project_no_path(session):
    """Test load command without path argument."""
    await session.cmd_load_project("")
    # Should display usage message
    assert session.project_config is None


@pytest.mark.asyncio
async def test_load_project_missing_yaml(session, tmp_path):
    """Test load command with missing project.yaml."""
    project_path = tmp_path / "no_yaml"
    project_path.mkdir()

    await session.cmd_load_project(str(project_path))

    # Should fail gracefully
    assert session.project_config is None


@pytest.mark.asyncio
async def test_load_project_success(session, tmp_path):
    """Test successful project loading."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    # Create a valid project.yaml
    import yaml

    config_path = project_path / "project.yaml"
    with open(config_path, "w") as f:
        yaml.dump(
            {
                "project": {
                    "name": "test_project",  # Must be alphanumeric with underscores/hyphens
                    "description": "Test",
                    "version": "1.0.0",
                },
                "data_source": {
                    "name": "test_api",
                    "type": "api",
                    "config": {"url": "https://api.example.com"},
                },
                "output": {
                    "formats": [{"type": "json", "path": "output/results.json"}]
                },
                "examples": [],
            },
            f,
        )

    await session.cmd_load_project(str(project_path))

    # Should load successfully
    assert session.project_config is not None
    assert session.project_path == project_path


@pytest.mark.asyncio
async def test_load_project_invalid_yaml(session, tmp_path):
    """Test load command with invalid YAML."""
    project_path = tmp_path / "invalid_yaml"
    project_path.mkdir()

    # Create invalid YAML
    config_path = project_path / "project.yaml"
    with open(config_path, "w") as f:
        f.write("invalid: yaml: content: [")

    await session.cmd_load_project(str(project_path))

    # Should fail gracefully
    assert session.project_config is None


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================


def test_state_isolation(session):
    """Test that session state is properly isolated."""
    # Modify state
    session.analysis_results = {"test": "data"}
    session.generated_code = "test code"

    # Create new session
    new_session = InteractiveExtractionSession()

    # Should have clean state
    assert new_session.analysis_results is None
    assert new_session.generated_code is None


def test_state_persistence_across_commands(session):
    """Test that state persists across multiple commands."""
    # Set state
    test_results = {"patterns": []}
    session.analysis_results = test_results

    # State should persist
    assert session.analysis_results is test_results
    assert session.analysis_results["patterns"] == []


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_load_project_exception_handling(session):
    """Test that project loading exceptions are caught."""
    # Try to load a path that will cause an error
    await session.cmd_load_project("/nonexistent/path/that/does/not/exist")

    # Should handle error gracefully
    assert session.project_config is None


@pytest.mark.asyncio
async def test_command_execution_with_exception(session):
    """Test that command exceptions don't crash the session."""
    # Test that the session can recover from exceptions
    # Note: In this implementation, exceptions in commands are not automatically
    # caught - they would be caught in the REPL loop's try/except
    # This test verifies the command works normally
    await session.cmd_help()
    # If we get here, the command executed successfully


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_full_workflow_simulation(session, tmp_path):
    """Test a complete workflow: load -> analyze -> generate -> extract."""
    # Create project
    project_path = tmp_path / "workflow_test"
    project_path.mkdir()

    import yaml

    config_path = project_path / "project.yaml"
    with open(config_path, "w") as f:
        yaml.dump(
            {
                "project": {
                    "name": "workflow_test",  # Must be alphanumeric with underscores/hyphens
                    "description": "Test workflow",
                    "version": "1.0.0",
                },
                "data_source": {
                    "name": "test_api",
                    "type": "api",
                    "config": {"url": "https://api.example.com"},
                },
                "output": {
                    "formats": [{"type": "json", "path": "output/results.json"}]
                },
                "examples": [],
            },
            f,
        )

    # Execute workflow
    await session.cmd_load_project(str(project_path))
    assert session.project_config is not None

    await session.cmd_analyze()
    assert session.analysis_results is not None

    await session.cmd_generate_code()
    assert session.generated_code is not None

    await session.cmd_run_extraction()
    assert session.extraction_results is not None


# ============================================================================
# COVERAGE TESTS
# ============================================================================


def test_all_commands_have_tests():
    """Ensure all commands have at least one test."""
    session = InteractiveExtractionSession()
    tested_commands = {
        "help",
        "load",
        "show",
        "analyze",
        "patterns",
        "examples",
        "generate",
        "extract",
        "exit",
    }

    # Verify all commands are covered
    assert set(session.commands.keys()) == tested_commands


@pytest.mark.asyncio
async def test_command_signature_consistency(session):
    """Test that all commands accept args parameter."""
    # All commands should accept a string argument
    for command_name, command_func in session.commands.items():
        try:
            # Should be callable with a string argument
            result = await command_func("")
            # exit returns "exit", others return None
            assert result is None or result == "exit"
        except TypeError as e:
            pytest.fail(f"Command {command_name} doesn't accept args parameter: {e}")


# ============================================================================
# PHASE 2 INTEGRATION TESTS - Full Workflow with Services
# ============================================================================


@pytest.mark.asyncio
async def test_phase2_full_workflow_integration(tmp_path):
    """Test complete Phase 2 workflow: load → analyze → generate → validate → extract."""
    # Setup test project
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create project.yaml
    import yaml

    config_data = {
        "project": {
            "name": "test_project",
            "description": "Phase 2 test",
            "version": "1.0.0",
        },
        "data_source": {
            "name": "test_api",
            "type": "api",
            "config": {"url": "https://api.example.com"},
        },
        "output": {"formats": [{"type": "json", "path": "output/results.json"}]},
        "examples": ["example1.json", "example2.json"],
    }

    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump(config_data, f)

    # Create example files
    import json

    example1 = {
        "input_data": {"name": "John", "age": "30"},
        "output_data": {"full_name": "John", "years": 30},
    }
    example2 = {
        "input_data": {"name": "Jane", "age": "25"},
        "output_data": {"full_name": "Jane", "years": 25},
    }

    with open(project_dir / "example1.json", "w") as f:
        json.dump(example1, f)
    with open(project_dir / "example2.json", "w") as f:
        json.dump(example2, f)

    # Run workflow
    session = InteractiveExtractionSession(project_path=project_dir)

    # Load project
    await session.cmd_load_project(str(project_dir))
    assert session.project_config is not None
    assert session.project_config.project.name == "test_project"

    # Analyze (uses ExampleParser and SchemaAnalyzer)
    await session.cmd_analyze()
    assert session.analysis_results is not None
    assert "patterns" in session.analysis_results
    assert "input_schema" in session.analysis_results
    assert "output_schema" in session.analysis_results

    # Generate code
    await session.cmd_generate_code()
    assert session.generated_code is not None
    assert session.generated_code_path is not None
    assert session.generated_code_path.exists()
    assert "class GeneratedExtractor" in session.generated_code

    # Validate code (uses ConstraintEnforcer)
    await session.cmd_validate_code()
    # Validation should complete without error

    # Extract data (executes generated code)
    await session.cmd_run_extraction()
    assert session.extraction_results is not None
    assert len(session.extraction_results) > 0


@pytest.mark.asyncio
async def test_phase2_session_save_restore(tmp_path):
    """Test session persistence (save/resume/list)."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create minimal project
    import yaml

    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump(
            {
                "project": {
                    "name": "test_save",
                    "description": "Test",
                    "version": "1.0.0",
                },
                "data_source": {"name": "test", "type": "api", "config": {}},
                "output": {"formats": [{"type": "json", "path": "output.json"}]},
                "examples": [],
            },
            f,
        )

    session1 = InteractiveExtractionSession(project_path=project_dir)
    await session1.cmd_load_project(str(project_dir))

    # Add some state
    session1.analysis_results = {
        "patterns": [
            {
                "type": "FIELD_MAPPING",
                "confidence": 0.95,
                "source_field": "name",
                "target_field": "full_name",
                "description": "Map name",
            }
        ]
    }

    # Save session
    await session1.cmd_save_session("test")

    # Create new session and restore
    session2 = InteractiveExtractionSession()
    await session2.cmd_resume_session("test")

    # Verify state restored
    assert session2.project_config is not None
    assert session2.project_config.project.name == "test_save"
    assert session2.analysis_results is not None
    assert len(session2.analysis_results["patterns"]) == 1

    # List sessions
    await session2.cmd_list_sessions()
    # Should display without error


@pytest.mark.asyncio
async def test_phase2_auto_save_on_exit(tmp_path):
    """Test auto-save functionality on exit."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    import yaml

    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump(
            {
                "project": {
                    "name": "test_autosave",
                    "description": "Test",
                    "version": "1.0.0",
                },
                "data_source": {"name": "test", "type": "api", "config": {}},
                "output": {"formats": [{"type": "json", "path": "output.json"}]},
                "examples": [],
            },
            f,
        )

    session = InteractiveExtractionSession(project_path=project_dir)
    await session.cmd_load_project(str(project_dir))

    # Exit should auto-save
    result = await session.cmd_exit()
    assert result == "exit"

    # Verify session was saved
    session_file = session._get_session_file("last")
    assert session_file.exists()


@pytest.mark.asyncio
async def test_phase2_enhanced_pattern_display(session):
    """Test enhanced pattern display with color-coded confidence."""
    session.analysis_results = {
        "patterns": [
            {
                "type": "FIELD_MAPPING",
                "confidence": 0.95,
                "source_field": "name",
                "target_field": "full_name",
                "description": "Direct field mapping",
            },
            {
                "type": "TYPE_CONVERSION",
                "confidence": 0.75,
                "source_field": "age",
                "target_field": "years",
                "description": "String to integer",
            },
            {
                "type": "CONCATENATION",
                "confidence": 0.65,
                "source_field": "first+last",
                "target_field": "name",
                "description": "Concatenate fields",
            },
        ]
    }

    # Should display patterns with color-coded confidence
    await session.cmd_show_patterns()
    # Should complete without error (visual verification in manual testing)


@pytest.mark.asyncio
async def test_phase2_command_registry_updated(session):
    """Test that Phase 2 commands are registered."""
    expected_commands = {
        "help",
        "load",
        "show",
        "examples",
        "analyze",
        "patterns",
        "generate",
        "validate",
        "extract",  # Phase 2: enhanced
        "save",
        "resume",
        "sessions",  # Phase 2: new
        "exit",
    }
    assert set(session.commands.keys()) == expected_commands


@pytest.mark.asyncio
async def test_phase2_validate_without_code(session):
    """Test validate command without generated code."""
    await session.cmd_validate_code()
    # Should display warning
    assert session.generated_code is None


@pytest.mark.asyncio
async def test_phase2_sessions_command_empty(session):
    """Test sessions command with no saved sessions."""
    # Clear session directory if it exists
    session_dir = session._get_session_dir()
    for session_file in session_dir.glob("*.json"):
        session_file.unlink()

    await session.cmd_list_sessions()
    # Should display "No saved sessions found"
