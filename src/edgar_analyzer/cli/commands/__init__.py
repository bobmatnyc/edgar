"""CLI commands module."""

from edgar_analyzer.cli.commands.project import project
from edgar_analyzer.cli.commands.setup import setup
from edgar_analyzer.cli.commands.extractors import extractors_cli
from edgar_analyzer.cli.commands.fortune100 import fortune100_cli

__all__ = ["project", "setup", "extractors_cli", "fortune100_cli"]
