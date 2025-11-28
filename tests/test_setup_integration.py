#!/usr/bin/env python3
"""Integration test for setup command - verify CLI integration works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar_analyzer.cli.commands.setup import setup
from click.testing import CliRunner


def test_setup_command_registered():
    """Test that setup command is properly registered and callable."""
    runner = CliRunner()

    # Test help
    result = runner.invoke(setup, ["--help"])
    print("Setup command help:")
    print(result.output)
    assert result.exit_code == 0
    assert "Configure API keys" in result.output

    # Test non-interactive mode
    with runner.isolated_filesystem():
        result = runner.invoke(setup, [
            "--key", "openrouter",
            "--value", "test-key",
            "--no-validate"
        ])
        print("\nNon-interactive setup:")
        print(result.output)
        assert result.exit_code == 0
        assert Path(".env.local").exists()

    print("\n✅ Setup command integration test passed!")


if __name__ == "__main__":
    test_setup_command_registered()
