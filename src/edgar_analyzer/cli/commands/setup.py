"""Setup command for API key configuration."""

import click
from pathlib import Path
from typing import Optional
import httpx
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


@click.command()
@click.option('--key', type=str, help='API key to configure (openrouter, jina, edgar)')
@click.option('--value', type=str, help='API key value (non-interactive mode)')
@click.option('--validate/--no-validate', default=True, help='Validate API key')
def setup(key: Optional[str], value: Optional[str], validate: bool) -> None:
    """Configure API keys and settings for the platform."""

    if key and value:
        # Non-interactive mode
        _setup_single_key(key, value, validate)
    else:
        # Interactive wizard mode
        _interactive_setup()


def _interactive_setup() -> None:
    """Interactive wizard for setting up all API keys."""
    console.print("\n[bold cyan]🔧 EDGAR Platform Setup Wizard[/bold cyan]\n")

    # Check current configuration
    env_file = Path(".env.local")
    current_config = _read_env_file(env_file)

    # Display current status
    _display_config_status(current_config)

    # Prompt for each key
    keys_to_configure = [
        ("openrouter", "OpenRouter API Key", "Get your key from https://openrouter.ai/keys"),
        ("jina", "Jina.ai API Key (optional)", "Get your key from https://jina.ai"),
        ("edgar", "SEC EDGAR User Agent", "Format: YourName email@example.com"),
    ]

    updates = {}
    for key_name, display_name, help_text in keys_to_configure:
        if _should_configure_key(key_name, current_config):
            console.print(f"\n[yellow]{display_name}[/yellow]")
            console.print(f"[dim]{help_text}[/dim]")

            value = Prompt.ask(
                f"Enter {display_name}",
                password=(key_name != "edgar"),
                default=current_config.get(key_name, "")
            )

            if value:
                updates[key_name] = value

    # Validate keys if requested
    if updates and Confirm.ask("\nValidate API keys?", default=True):
        _validate_keys(updates)

    # Save to .env.local
    if updates:
        _save_to_env_file(env_file, updates)
        console.print("\n[green]✅ Configuration saved to .env.local[/green]")
    else:
        console.print("\n[yellow]No changes made[/yellow]")


def _setup_single_key(key: str, value: str, validate: bool) -> None:
    """Configure a single API key (non-interactive mode)."""
    key_mapping = {
        "openrouter": "OPENROUTER_API_KEY",
        "jina": "JINA_API_KEY",
        "edgar": "EDGAR_USER_AGENT"
    }

    if key not in key_mapping:
        console.print(f"[red]❌ Unknown key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(key_mapping.keys())}")
        return

    # Validate if requested
    if validate:
        if not _validate_single_key(key, value):
            console.print(f"[red]❌ Validation failed for {key}[/red]")
            return

    # Save to .env.local
    env_file = Path(".env.local")
    _save_to_env_file(env_file, {key: value})
    console.print(f"[green]✅ {key_mapping[key]} configured[/green]")


def _read_env_file(env_file: Path) -> dict:
    """Read current .env.local configuration."""
    config = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Map env var names to short names
                    if key == "OPENROUTER_API_KEY":
                        config["openrouter"] = value
                    elif key == "JINA_API_KEY":
                        config["jina"] = value
                    elif key == "EDGAR_USER_AGENT":
                        config["edgar"] = value
    return config


def _display_config_status(config: dict) -> None:
    """Display current configuration status."""
    table = Table(title="Current Configuration")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value", style="dim")

    services = [
        ("OpenRouter", "openrouter", "Required"),
        ("Jina.ai", "jina", "Optional"),
        ("SEC EDGAR", "edgar", "Required for EDGAR sources"),
    ]

    for name, key, note in services:
        if key in config and config[key]:
            value = config[key]
            # Mask API keys
            if key != "edgar":
                value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            table.add_row(name, "✅ Configured", value)
        else:
            table.add_row(name, "❌ Not configured", note)

    console.print(table)


def _should_configure_key(key_name: str, current_config: dict) -> bool:
    """Ask if user wants to configure this key."""
    if key_name in current_config and current_config[key_name]:
        return Confirm.ask(f"Reconfigure {key_name}?", default=False)
    return True


def _validate_keys(updates: dict) -> None:
    """Validate API keys by testing connections."""
    console.print("\n[yellow]Validating API keys...[/yellow]")

    for key, value in updates.items():
        console.print(f"Testing {key}...", end=" ")

        if _validate_single_key(key, value):
            console.print("[green]✅[/green]")
        else:
            console.print("[red]❌ Failed[/red]")


def _validate_single_key(key: str, value: str) -> bool:
    """Validate a single API key."""
    try:
        if key == "openrouter":
            return _validate_openrouter(value)
        elif key == "jina":
            return _validate_jina(value)
        elif key == "edgar":
            return _validate_edgar_user_agent(value)
    except Exception:
        return False
    return True


def _validate_openrouter(api_key: str) -> bool:
    """Test OpenRouter API key."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.status_code == 200
    except Exception:
        return False


def _validate_jina(api_key: str) -> bool:
    """Test Jina.ai API key."""
    try:
        with httpx.Client(timeout=10.0) as client:
            # Simple test with Jina reader
            response = client.get(
                "https://r.jina.ai/https://example.com",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.status_code == 200
    except Exception:
        return False


def _validate_edgar_user_agent(user_agent: str) -> bool:
    """Validate SEC EDGAR user agent format."""
    # Should be: "Name email@example.com"
    return " " in user_agent and "@" in user_agent


def _save_to_env_file(env_file: Path, updates: dict) -> None:
    """Save configuration updates to .env.local."""
    key_mapping = {
        "openrouter": "OPENROUTER_API_KEY",
        "jina": "JINA_API_KEY",
        "edgar": "EDGAR_USER_AGENT"
    }

    # Read existing file
    lines = []
    existing_keys = set()
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    env_key = stripped.split("=", 1)[0]
                    existing_keys.add(env_key)

                    # Update if this key is being modified
                    updated = False
                    for short_key, long_key in key_mapping.items():
                        if env_key == long_key and short_key in updates:
                            lines.append(f"{long_key}={updates[short_key]}\n")
                            updated = True
                            break

                    if not updated:
                        lines.append(line)
                else:
                    lines.append(line)

    # Add new keys
    for short_key, value in updates.items():
        long_key = key_mapping[short_key]
        if long_key not in existing_keys:
            lines.append(f"{long_key}={value}\n")

    # Write back
    with open(env_file, "w") as f:
        f.writelines(lines)
