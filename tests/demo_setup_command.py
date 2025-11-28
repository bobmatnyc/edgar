#!/usr/bin/env python3
"""Demonstration script for setup command functionality.

This script demonstrates all features of the setup command:
- Interactive wizard mode
- Non-interactive mode
- Configuration status display
- API key validation
- Safe .env.local updates

Run with: python tests/demo_setup_command.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar_analyzer.cli.commands.setup import (
    _read_env_file,
    _display_config_status,
    _validate_edgar_user_agent,
    _validate_openrouter,
    _validate_jina,
    setup,
)
from click.testing import CliRunner
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def demo_read_config():
    """Demonstrate reading current configuration."""
    console.print("\n[bold cyan]1. Reading Current Configuration[/bold cyan]\n")

    env_file = Path(".env.local")
    config = _read_env_file(env_file)

    table = Table(title="Configuration Read from .env.local")
    table.add_column("Key", style="cyan")
    table.add_column("Value (Masked)", style="green")

    for key, value in config.items():
        # Mask values for display
        if key != "edgar" and value:
            masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
        else:
            masked = value

        table.add_row(key, masked)

    console.print(table)


def demo_config_status():
    """Demonstrate configuration status display."""
    console.print("\n[bold cyan]2. Configuration Status Display[/bold cyan]\n")

    env_file = Path(".env.local")
    config = _read_env_file(env_file)

    _display_config_status(config)


def demo_validation():
    """Demonstrate validation functions."""
    console.print("\n[bold cyan]3. Validation Functions[/bold cyan]\n")

    # EDGAR user agent validation (local, no network)
    test_cases = [
        ("John Doe john@example.com", True),
        ("InvalidFormat", False),
        ("NoEmail company", False),
        ("", False),
    ]

    table = Table(title="EDGAR User Agent Validation")
    table.add_column("Input", style="cyan")
    table.add_column("Valid", style="green")

    for user_agent, expected in test_cases:
        result = _validate_edgar_user_agent(user_agent)
        status = "✅" if result == expected else "❌"
        table.add_row(user_agent or "(empty)", status)

    console.print(table)

    # Note about API validation
    console.print(
        "\n[yellow]Note:[/yellow] OpenRouter and Jina validation require network access"
    )
    console.print("and will be skipped in this demo to avoid API calls.\n")


def demo_non_interactive_mode():
    """Demonstrate non-interactive mode."""
    console.print("\n[bold cyan]4. Non-Interactive Mode[/bold cyan]\n")

    runner = CliRunner()

    # Simulate non-interactive setup (without validation to avoid API calls)
    console.print("[yellow]Simulating command:[/yellow]")
    console.print(
        "  python -m edgar_analyzer setup --key openrouter --value <key> --no-validate\n"
    )

    # Note: Not actually running to avoid modifying .env.local
    console.print(
        "[green]✅ In production, this would:[/green]\n"
        "  1. Parse command-line arguments\n"
        "  2. Validate key name (openrouter, jina, edgar)\n"
        "  3. Optionally validate API key (if --validate)\n"
        "  4. Update .env.local preserving other variables\n"
        "  5. Print success message\n"
    )


def demo_interactive_mode():
    """Demonstrate interactive wizard mode."""
    console.print("\n[bold cyan]5. Interactive Wizard Mode[/bold cyan]\n")

    console.print(
        "[yellow]Interactive wizard provides:[/yellow]\n"
        "  • Current configuration status display\n"
        "  • Prompts for each API key\n"
        "  • Option to reconfigure existing keys\n"
        "  • Password-style input (hidden)\n"
        "  • Optional validation\n"
        "  • Rich UI with tables and colors\n"
    )

    console.print(
        "\n[green]To launch wizard:[/green] python -m edgar_analyzer setup\n"
    )


def demo_help():
    """Demonstrate help output."""
    console.print("\n[bold cyan]6. Help Output[/bold cyan]\n")

    runner = CliRunner()
    result = runner.invoke(setup, ["--help"])

    console.print(Panel(result.output, title="Setup Command Help", border_style="cyan"))


def main():
    """Run all demonstrations."""
    console.print(
        Panel.fit(
            "[bold green]EDGAR Platform Setup Command Demo[/bold green]\n"
            "[cyan]Demonstrating all features and capabilities[/cyan]",
            title="Setup Command Demo",
            border_style="green",
        )
    )

    try:
        demo_read_config()
        demo_config_status()
        demo_validation()
        demo_non_interactive_mode()
        demo_interactive_mode()
        demo_help()

        console.print("\n")
        console.print(
            Panel.fit(
                "[bold green]✅ Demo Complete[/bold green]\n\n"
                "[cyan]Key Features:[/cyan]\n"
                "  • Interactive wizard with Rich UI\n"
                "  • Non-interactive mode for automation\n"
                "  • API key validation (OpenRouter, Jina, EDGAR)\n"
                "  • Safe .env.local management\n"
                "  • Masked key display for security\n"
                "  • Preserves existing configuration\n\n"
                "[yellow]Try it yourself:[/yellow]\n"
                "  python -m edgar_analyzer setup\n",
                title="Summary",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
