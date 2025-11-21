#!/usr/bin/env python3
"""
EDGAR Analyzer CLI Entry Point

Main entry point for the EDGAR Analyzer CLI when run as a module.
"""

from .main_cli import create_integrated_cli

if __name__ == "__main__":
    cli = create_integrated_cli()
    cli()
