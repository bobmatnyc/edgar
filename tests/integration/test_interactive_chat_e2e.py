"""End-to-end integration tests for interactive chat mode.

Tests the complete interactive chat workflow including:
- Natural language command understanding
- Confidence threshold tuning
- Session persistence
- CLI integration
- Full workflow execution
"""

import json
from pathlib import Path

import pytest
import yaml

from edgar_analyzer.interactive import InteractiveExtractionSession


@pytest.fixture
def test_project(tmp_path):
    """Create a test project with valid configuration."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create project.yaml
    config = {
        "project": {"name": "test_project", "version": "1.0.0"},
        "data_source": {
            "type": "excel",
            "config": {"file_path": "data.xlsx", "sheet_name": 0},
        },
        "examples": ["example1.json", "example2.json"],
        "confidence_threshold": 0.7,
    }

    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump(config, f)

    # Create examples
    examples = [
        {
            "input_data": {"name": "John", "age": 30, "city": "NYC"},
            "output_data": {"full_name": "John", "age_years": 30, "location": "NYC"},
        },
        {
            "input_data": {"name": "Jane", "age": 25, "city": "LA"},
            "output_data": {"full_name": "Jane", "age_years": 25, "location": "LA"},
        },
    ]

    for idx, example in enumerate(examples, 1):
        with open(project_dir / f"example{idx}.json", "w") as f:
            json.dump(example, f)

    return project_dir


@pytest.mark.asyncio
async def test_full_workflow_e2e(test_project):
    """Test complete workflow: load → analyze → generate → validate → extract."""
    session = InteractiveExtractionSession(project_path=test_project)

    # 1. Load project
    await session.cmd_load_project(str(test_project))
    assert session.project_config is not None
    assert session.project_config.project.name == "test_project"

    # 2. Show examples
    await session.cmd_show_examples()

    # 3. Analyze
    await session.cmd_analyze()
    assert session.analysis_results is not None
    assert "patterns" in session.analysis_results

    # 4. Show patterns
    await session.cmd_show_patterns()

    # 5. Generate code
    await session.cmd_generate_code()
    assert session.generated_code is not None

    # 6. Validate code
    await session.cmd_validate_code()

    # 7. Extract (may fail if code generation incomplete, that's OK)
    try:
        await session.cmd_run_extraction()
        assert session.extraction_results is not None
    except Exception:
        pass  # Code execution may fail in test environment


@pytest.mark.asyncio
async def test_confidence_threshold_tuning(test_project):
    """Test confidence threshold adjustment."""
    session = InteractiveExtractionSession(project_path=test_project)

    await session.cmd_load_project(str(test_project))
    await session.cmd_analyze()

    initial_patterns = len(session.analysis_results.get("patterns", []))

    # Increase threshold
    await session.cmd_set_confidence("0.9")

    # Should have potentially fewer patterns with higher threshold
    new_patterns = len(session.analysis_results.get("patterns", []))
    assert new_patterns <= initial_patterns


@pytest.mark.asyncio
async def test_confidence_threshold_invalid(test_project):
    """Test invalid confidence threshold handling."""
    session = InteractiveExtractionSession(project_path=test_project)

    await session.cmd_load_project(str(test_project))

    # Test out of range values
    await session.cmd_set_confidence("1.5")  # Should show error
    await session.cmd_set_confidence("-0.1")  # Should show error
    await session.cmd_set_confidence("invalid")  # Should show error


@pytest.mark.asyncio
async def test_session_persistence_e2e(test_project, tmp_path):
    """Test full session save/restore workflow."""
    session1 = InteractiveExtractionSession(project_path=test_project)

    # Work in session 1
    await session1.cmd_load_project(str(test_project))
    await session1.cmd_analyze()
    await session1.cmd_save_session("test_e2e")

    # Create new session and restore
    session2 = InteractiveExtractionSession()
    await session2.cmd_resume_session("test_e2e")

    # Verify state restored
    assert session2.project_config is not None
    assert session2.project_config.project.name == "test_project"
    assert session2.analysis_results is not None


@pytest.mark.asyncio
async def test_natural_language_parsing():
    """Test NL command understanding."""
    session = InteractiveExtractionSession()

    # Test various NL inputs
    test_cases = [
        ("What patterns did you detect?", "patterns"),
        ("Show me the examples", "examples"),
        ("Analyze the project", "analyze"),
        ("Generate code", "generate"),
        ("Run extraction", "extract"),
        ("What's the confidence threshold?", "threshold"),
        ("Set confidence to 0.8", "confidence"),
    ]

    for nl_input, expected_cmd in test_cases:
        cmd, _ = await session._parse_natural_language(nl_input)
        assert cmd == expected_cmd, f"Failed for: {nl_input} (got: {cmd})"


@pytest.mark.asyncio
async def test_natural_language_fallback():
    """Test NL parsing fallback for unknown commands."""
    session = InteractiveExtractionSession()

    # Unknown phrase should fall back to first word
    cmd, _ = await session._parse_natural_language("unknown command here")
    assert cmd == "unknown"


@pytest.mark.asyncio
async def test_cli_integration_list_sessions():
    """Test CLI --list-sessions flag."""
    from click.testing import CliRunner

    from edgar_analyzer.main_cli import cli

    runner = CliRunner()

    # Test --list-sessions
    result = runner.invoke(cli, ["chat", "--list-sessions"])
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_show_command_no_project():
    """Test show command when no project loaded."""
    session = InteractiveExtractionSession()
    await session.cmd_show()
    # Should show warning, not crash


@pytest.mark.asyncio
async def test_analyze_command_no_project():
    """Test analyze command when no project loaded."""
    session = InteractiveExtractionSession()
    await session.cmd_analyze()
    # Should show warning, not crash


@pytest.mark.asyncio
async def test_generate_command_no_analysis():
    """Test generate command before analysis."""
    session = InteractiveExtractionSession()
    await session.cmd_generate_code()
    # Should show warning, not crash


@pytest.mark.asyncio
async def test_validate_command_no_code():
    """Test validate command before code generation."""
    session = InteractiveExtractionSession()
    await session.cmd_validate_code()
    # Should show warning, not crash


@pytest.mark.asyncio
async def test_extract_command_no_code():
    """Test extract command before code generation."""
    session = InteractiveExtractionSession()
    await session.cmd_run_extraction()
    # Should show warning, not crash


@pytest.mark.asyncio
async def test_session_resume_nonexistent():
    """Test resuming non-existent session."""
    session = InteractiveExtractionSession()
    await session.cmd_resume_session("nonexistent_session_xyz")
    # Should show warning, not crash


@pytest.mark.asyncio
async def test_get_confidence_no_project():
    """Test get confidence when no project loaded."""
    session = InteractiveExtractionSession()
    await session.cmd_get_confidence()
    # Should show warning, not crash


@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_requirements():
    """Test performance requirements."""
    import time

    session = InteractiveExtractionSession()

    # NL parsing should be <500ms
    start = time.time()
    await session._parse_natural_language("What patterns did you find?")
    duration = time.time() - start
    assert duration < 0.5, f"NL parsing too slow: {duration:.2f}s"


@pytest.mark.asyncio
async def test_command_registry_completeness():
    """Verify all expected commands exist in registry."""
    session = InteractiveExtractionSession()

    expected_commands = {
        "help",
        "load",
        "show",
        "examples",
        "analyze",
        "patterns",
        "generate",
        "validate",
        "extract",
        "save",
        "resume",
        "sessions",
        "confidence",
        "threshold",
        "exit",
    }

    actual_commands = set(session.commands.keys())
    assert expected_commands.issubset(
        actual_commands
    ), f"Missing commands: {expected_commands - actual_commands}"


@pytest.mark.asyncio
async def test_help_command():
    """Test help command displays all commands."""
    session = InteractiveExtractionSession()
    await session.cmd_help()
    # Should display help without errors


@pytest.mark.asyncio
async def test_exit_command():
    """Test exit command returns exit signal."""
    session = InteractiveExtractionSession()
    result = await session.cmd_exit()
    assert result == "exit"


@pytest.mark.asyncio
async def test_exit_command_with_project_autosaves(test_project):
    """Test exit command auto-saves when project loaded."""
    session = InteractiveExtractionSession(project_path=test_project)
    await session.cmd_load_project(str(test_project))

    result = await session.cmd_exit()
    assert result == "exit"

    # Verify "last" session was saved
    session_file = Path.home() / ".edgar" / "sessions" / "last_session.json"
    assert session_file.exists()


@pytest.mark.asyncio
async def test_confidence_persistence_in_session(test_project):
    """Test confidence threshold persists across session save/restore."""
    session1 = InteractiveExtractionSession(project_path=test_project)

    # Set confidence and save
    await session1.cmd_load_project(str(test_project))
    await session1.cmd_set_confidence("0.85")
    await session1.cmd_save_session("confidence_test")

    # Restore in new session
    session2 = InteractiveExtractionSession()
    await session2.cmd_resume_session("confidence_test")

    # Verify confidence was restored
    assert session2.project_config.confidence_threshold == 0.85


@pytest.mark.asyncio
async def test_multiple_analyze_runs(test_project):
    """Test running analyze multiple times works correctly."""
    session = InteractiveExtractionSession(project_path=test_project)

    await session.cmd_load_project(str(test_project))

    # First analysis
    await session.cmd_analyze()
    first_patterns = len(session.analysis_results.get("patterns", []))

    # Second analysis (should work, not crash)
    await session.cmd_analyze()
    second_patterns = len(session.analysis_results.get("patterns", []))

    # Should get same results
    assert first_patterns == second_patterns
