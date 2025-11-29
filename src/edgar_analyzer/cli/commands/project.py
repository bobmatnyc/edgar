"""Project management commands for the EDGAR analyzer platform.

This module provides commands for creating, listing, deleting, and validating projects.
Each project represents an independent data extraction workflow with its own configuration,
examples, and generated code.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def get_templates_dir() -> Path:
    """Get the templates directory, allowing override via environment variable.

    Returns:
        Path to templates directory
    """
    # Allow override for testing
    if env_path := os.getenv("EDGAR_TEMPLATES_DIR"):
        return Path(env_path)

    # Default to project root templates directory
    return Path(__file__).parent.parent.parent.parent.parent / "templates"


def get_projects_dir() -> Path:
    """Get the projects directory, allowing override via environment variable.

    Returns:
        Path to projects directory (external or in-repo)
    """
    # Check for external artifacts directory
    artifacts_base = os.getenv("EDGAR_ARTIFACTS_DIR")
    if artifacts_base and artifacts_base.strip():
        artifacts_path = Path(artifacts_base).expanduser().resolve()
        return artifacts_path / "projects"

    # Default to in-repo projects directory
    return Path("projects")


@click.group()
def project():
    """Manage projects (create, list, delete, validate)."""
    pass


@project.command()
@click.argument("name")
@click.option(
    "--template",
    type=click.Choice(["weather", "minimal"], case_sensitive=False),
    default="minimal",
    help="Project template to use",
)
@click.option(
    "--description",
    type=str,
    default="",
    help="Project description",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=str),
    default=None,
    help="Directory to create project in (default: $EDGAR_ARTIFACTS_DIR/projects or ./projects)",
)
def create(
    name: str,
    template: str,
    description: str,
    output_dir: Optional[str],
):
    """Create a new project from a template.

    Args:
        name: Project name (will be used as directory name)
        template: Template to use (weather, minimal)
        description: Optional project description
        output_dir: Directory to create project in (default: from environment or ./projects)

    Examples:
        edgar-analyzer project create my-api --template weather
        edgar-analyzer project create custom-scraper --template minimal
    """
    try:
        # Resolve paths - use get_projects_dir() if output_dir not specified
        output_path = Path(output_dir) if output_dir else get_projects_dir()
        project_path = output_path / name
        templates_dir = get_templates_dir()

        # Check if project already exists
        if project_path.exists():
            console.print(f"[red]Error:[/red] Project '{name}' already exists at {project_path}")
            raise click.Abort()

        # Determine template file
        if template == "weather":
            template_file = templates_dir / "weather_api_project.yaml"
        else:
            template_file = templates_dir / "project.yaml.template"

        if not template_file.exists():
            console.print(f"[red]Error:[/red] Template file not found: {template_file}")
            raise click.Abort()

        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)

        # Load and customize template
        with open(template_file) as f:
            config = yaml.safe_load(f)

        # Update project metadata
        config["project"]["name"] = name
        if description:
            config["project"]["description"] = description

        # Write project.yaml
        config_path = project_path / "project.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Create standard directories
        (project_path / "examples").mkdir(exist_ok=True)
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        (project_path / "output").mkdir(exist_ok=True)

        # Create README
        readme_content = f"""# {name}

{description or "Project description goes here"}

## Quick Start

1. Add example data files to `examples/`
2. Run code generation: `edgar-analyzer generate {name}`
3. Test the generated code: `python -m pytest tests/`
4. Extract data: `python src/{name}/main.py`

## Project Structure

- `project.yaml` - Project configuration
- `examples/` - Example data files for code generation
- `src/` - Generated source code
- `tests/` - Generated tests
- `output/` - Extracted data output

## Configuration

Edit `project.yaml` to customize:
- Data sources
- Output format
- Code generation constraints
- Validation rules

## Documentation

See the main EDGAR Analyzer documentation for details on:
- Adding examples
- Customizing templates
- Running code generation
- Troubleshooting
"""
        with open(project_path / "README.md", "w") as f:
            f.write(readme_content)

        # Copy template examples if using weather template
        if template == "weather":
            weather_examples = Path(__file__).parent.parent.parent.parent.parent / "projects" / "weather_api" / "examples"
            if weather_examples.exists():
                for example_file in weather_examples.glob("*.json"):
                    shutil.copy(example_file, project_path / "examples")

        # Success message
        console.print()
        console.print(Panel.fit(
            f"[green]✓[/green] Project '{name}' created successfully!\n\n"
            f"Location: {project_path}\n"
            f"Template: {template}\n\n"
            f"Next steps:\n"
            f"1. cd {project_path}\n"
            f"2. Add example data to examples/\n"
            f"3. Run: edgar-analyzer generate {name}",
            title="Project Created",
            border_style="green",
        ))

    except Exception as e:
        console.print(f"[red]Error creating project:[/red] {e}")
        raise click.Abort()


@project.command()
@click.option(
    "--output-dir",
    type=click.Path(path_type=str),
    default=None,
    help="Projects directory to list (default: $EDGAR_ARTIFACTS_DIR/projects or ./projects)",
)
@click.option(
    "--format",
    type=click.Choice(["table", "tree", "json"], case_sensitive=False),
    default="table",
    help="Output format",
)
def list(output_dir: Optional[str], format: str):
    """List all projects.

    Args:
        output_dir: Directory containing projects (default: from environment or ./projects)
        format: Output format (table, tree, json)

    Examples:
        edgar-analyzer project list
        edgar-analyzer project list --format tree
        edgar-analyzer project list --format json
    """
    try:
        output_path = Path(output_dir) if output_dir else get_projects_dir()

        if not output_path.exists():
            console.print(f"[yellow]No projects directory found at {output_path}[/yellow]")
            return

        # Find all projects (directories with project.yaml)
        projects = []
        for item in output_path.iterdir():
            if item.is_dir() and (item / "project.yaml").exists():
                with open(item / "project.yaml") as f:
                    config = yaml.safe_load(f)

                projects.append({
                    "name": config.get("project", {}).get("name", item.name),
                    "path": str(item),
                    "description": config.get("project", {}).get("description", ""),
                    "version": config.get("project", {}).get("version", "0.1.0"),
                    "template": config.get("project", {}).get("template", "custom"),
                })

        if not projects:
            console.print(f"[yellow]No projects found in {output_path}[/yellow]")
            return

        # Output based on format
        if format == "json":
            print(json.dumps(projects, indent=2))

        elif format == "tree":
            tree = Tree(f"[bold]Projects ({len(projects)})[/bold]")
            for p in projects:
                project_node = tree.add(f"[cyan]{p['name']}[/cyan] ({p['version']})")
                project_node.add(f"[dim]Path:[/dim] {p['path']}")
                if p['description']:
                    project_node.add(f"[dim]Description:[/dim] {p['description']}")
                project_node.add(f"[dim]Template:[/dim] {p['template']}")
            console.print(tree)

        else:  # table
            table = Table(title=f"Projects ({len(projects)})")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Version", style="magenta")
            table.add_column("Template", style="yellow")
            table.add_column("Description", style="white")

            for p in projects:
                table.add_row(
                    p['name'],
                    p['version'],
                    p['template'],
                    p['description'][:50] + "..." if len(p['description']) > 50 else p['description'],
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing projects:[/red] {e}")
        raise click.Abort()


@project.command()
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=str),
    default=None,
    help="Projects directory (default: $EDGAR_ARTIFACTS_DIR/projects or ./projects)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Delete without confirmation",
)
def delete(name: str, output_dir: Optional[str], force: bool):
    """Delete a project.

    Args:
        name: Project name to delete
        output_dir: Directory containing projects (default: from environment or ./projects)
        force: Skip confirmation prompt

    Examples:
        edgar-analyzer project delete my-api
        edgar-analyzer project delete my-api --force
    """
    try:
        output_path = Path(output_dir) if output_dir else get_projects_dir()
        project_path = output_path / name

        if not project_path.exists():
            console.print(f"[red]Error:[/red] Project '{name}' not found at {project_path}")
            raise click.Abort()

        if not (project_path / "project.yaml").exists():
            console.print(f"[red]Error:[/red] '{name}' is not a valid project (no project.yaml)")
            raise click.Abort()

        # Confirm deletion
        if not force:
            console.print(f"\n[yellow]Warning:[/yellow] You are about to delete project '{name}'")
            console.print(f"Location: {project_path}")

            if not click.confirm("\nAre you sure you want to delete this project?", default=False):
                console.print("[cyan]Deletion cancelled[/cyan]")
                return

        # Delete project
        shutil.rmtree(project_path)

        console.print(f"[green]✓[/green] Project '{name}' deleted successfully")

    except Exception as e:
        console.print(f"[red]Error deleting project:[/red] {e}")
        raise click.Abort()


@project.command()
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=str),
    default=None,
    help="Projects directory (default: $EDGAR_ARTIFACTS_DIR/projects or ./projects)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed validation output",
)
def validate(name: str, output_dir: Optional[str], verbose: bool):
    """Validate a project configuration.

    Args:
        name: Project name to validate
        output_dir: Directory containing projects (default: from environment or ./projects)
        verbose: Show detailed validation output

    Examples:
        edgar-analyzer project validate my-api
        edgar-analyzer project validate my-api --verbose
    """
    try:
        output_path = Path(output_dir) if output_dir else get_projects_dir()
        project_path = output_path / name

        if not project_path.exists():
            console.print(f"[red]Error:[/red] Project '{name}' not found at {project_path}")
            raise click.Abort()

        config_path = project_path / "project.yaml"
        if not config_path.exists():
            console.print(f"[red]Error:[/red] No project.yaml found in '{name}'")
            raise click.Abort()

        # Load and validate config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        errors = []
        warnings = []

        # Validate required fields
        if "project" not in config:
            errors.append("Missing 'project' section")
        else:
            if "name" not in config["project"]:
                errors.append("Missing project.name")
            if "version" not in config["project"]:
                warnings.append("Missing project.version (using default 0.1.0)")

        # Validate directories
        required_dirs = ["examples", "src", "tests", "output"]
        for dir_name in required_dirs:
            dir_path = project_path / dir_name
            if not dir_path.exists():
                warnings.append(f"Missing directory: {dir_name}/")

        # Check for example files
        examples_dir = project_path / "examples"
        if examples_dir.exists():
            # Use os.listdir instead of Path.glob to avoid Click parser conflict
            example_files = [f for f in os.listdir(str(examples_dir)) if (examples_dir / f).is_file()]
            if not example_files:
                warnings.append("No example files found in examples/")

        # Output validation results
        if verbose:
            console.print("\n[bold]Validation Report[/bold]")
            console.print(f"Project: {name}")
            console.print(f"Path: {project_path}")
            console.print()

        if errors:
            console.print("[red]Errors:[/red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error}")

        if warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  [yellow]![/yellow] {warning}")

        if not errors and not warnings:
            console.print(f"[green]✓[/green] Project '{name}' is valid")
        elif not errors:
            console.print(f"\n[yellow]Project '{name}' is valid with warnings[/yellow]")
        else:
            console.print(f"\n[red]Project '{name}' has validation errors[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error validating project:[/red] {e}")
        raise click.Abort()


if __name__ == "__main__":
    project()
