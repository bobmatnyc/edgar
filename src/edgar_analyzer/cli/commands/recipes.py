"""CLI commands for recipe management.

Commands:
- edgar recipes list - List available recipes
- edgar recipes validate <recipe> - Validate a recipe file
- edgar recipes info <recipe> - Show recipe information
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pydantic import ValidationError
import yaml

from edgar_analyzer.recipes import load_recipe, discover_recipes, validate_recipe
from edgar_analyzer.recipes.loader import get_recipe_info

console = Console()


@click.group(name="recipes")
def recipes_cli():
    """Recipe management commands."""
    pass


@recipes_cli.command(name="list")
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    default=Path("recipes"),
    help="Directory to search for recipes (default: recipes/)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information",
)
def list_recipes(directory: Path, verbose: bool):
    """List available recipes.

    Discovers all recipe YAML files in the specified directory and displays
    their metadata.

    Example:
        edgar recipes list
        edgar recipes list --directory custom_recipes/ --verbose
    """
    console.print(f"[cyan]Discovering recipes in {directory}...[/cyan]\n")

    try:
        recipes = discover_recipes(directory)

        if not recipes:
            console.print(f"[yellow]No recipes found in {directory}[/yellow]")
            return

        # Create table
        table = Table(title=f"Available Recipes ({len(recipes)} found)")
        table.add_column("Name", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Steps", style="green", justify="right")
        table.add_column("Parameters", style="blue", justify="right")

        if verbose:
            table.add_column("Description", style="yellow")

        for recipe in recipes:
            info = get_recipe_info(recipe)
            row = [
                info["name"],
                info["title"],
                str(info["step_count"]),
                str(info["parameter_count"]),
            ]

            if verbose:
                description = info["description"]
                # Truncate long descriptions
                if len(description) > 50:
                    description = description[:47] + "..."
                row.append(description)

            table.add_row(*row)

        console.print(table)

        # Summary
        console.print(f"\n[green]Total recipes: {len(recipes)}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@recipes_cli.command(name="validate")
@click.argument("recipe_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation results",
)
def validate_recipe_cmd(recipe_path: Path, verbose: bool):
    """Validate a recipe file.

    Checks recipe syntax, schema validity, and semantic correctness.

    Example:
        edgar recipes validate recipes/fortune100.yaml
        edgar recipes validate my_recipe.yaml --verbose
    """
    console.print(f"[cyan]Validating recipe: {recipe_path}[/cyan]\n")

    try:
        # Load recipe (includes Pydantic validation)
        recipe = load_recipe(recipe_path)

        console.print(f"[green]✓ YAML syntax valid[/green]")
        console.print(f"[green]✓ Schema validation passed[/green]")

        # Semantic validation
        errors = validate_recipe(recipe)

        if errors:
            console.print(f"\n[red]✗ Semantic validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
            return

        console.print(f"[green]✓ Semantic validation passed[/green]")

        # Show recipe info if verbose
        if verbose:
            info = get_recipe_info(recipe)

            info_panel = Panel.fit(
                f"[bold]Recipe Information[/bold]\n"
                f"[cyan]Name:[/cyan] {info['name']}\n"
                f"[cyan]Title:[/cyan] {info['title']}\n"
                f"[cyan]Version:[/cyan] {info['version']}\n"
                f"[cyan]Steps:[/cyan] {info['step_count']}\n"
                f"[cyan]Parameters:[/cyan] {info['parameter_count']}\n"
                f"[cyan]Required Params:[/cyan] {', '.join(info['required_parameters']) or 'None'}\n"
                f"[cyan]Optional Params:[/cyan] {', '.join(info['optional_parameters']) or 'None'}\n"
                f"[cyan]Step Types:[/cyan] {', '.join(set(info['step_types']))}",
                title="Recipe Details",
            )
            console.print(info_panel)

        console.print(f"\n[bold green]Recipe is valid! ✓[/bold green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
    except ValidationError as e:
        console.print(f"[red]Schema validation failed:[/red]")
        console.print(f"[red]{e}[/red]")
    except yaml.YAMLError as e:
        console.print(f"[red]YAML syntax error:[/red]")
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@recipes_cli.command(name="info")
@click.argument("recipe_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--show-steps",
    "-s",
    is_flag=True,
    help="Show detailed step information",
)
def show_recipe_info(recipe_path: Path, show_steps: bool):
    """Show detailed recipe information.

    Displays recipe metadata, parameters, and steps.

    Example:
        edgar recipes info recipes/fortune100.yaml
        edgar recipes info my_recipe.yaml --show-steps
    """
    console.print(f"[cyan]Loading recipe: {recipe_path}[/cyan]\n")

    try:
        recipe = load_recipe(recipe_path)
        info = get_recipe_info(recipe)

        # Main info panel
        info_text = (
            f"[bold]{info['title']}[/bold]\n"
            f"{info['description']}\n\n"
            f"[cyan]Version:[/cyan] {info['version']}\n"
            f"[cyan]Name:[/cyan] {info['name']}\n"
            f"[cyan]Steps:[/cyan] {info['step_count']}\n"
            f"[cyan]Parameters:[/cyan] {info['parameter_count']}"
        )

        console.print(Panel(info_text, title="Recipe Information"))

        # Parameters table
        if recipe.parameters:
            param_table = Table(title="Parameters")
            param_table.add_column("Name", style="cyan")
            param_table.add_column("Type", style="blue")
            param_table.add_column("Required", style="yellow")
            param_table.add_column("Default", style="green")
            param_table.add_column("Description", style="white")

            for param in recipe.parameters:
                param_table.add_row(
                    param.name,
                    param.type.value,
                    "Yes" if param.required else "No",
                    str(param.default) if param.default is not None else "-",
                    param.description or "-",
                )

            console.print(param_table)

        # Steps table
        if show_steps and recipe.steps:
            steps_table = Table(title="Steps")
            steps_table.add_column("Order", style="blue", justify="right")
            steps_table.add_column("Name", style="cyan")
            steps_table.add_column("Type", style="magenta")
            steps_table.add_column("Outputs", style="green")
            steps_table.add_column("Condition", style="yellow")

            for i, step in enumerate(recipe.steps, 1):
                outputs = ", ".join(step.outputs) if step.outputs else "-"
                condition = step.condition if step.condition else "-"

                steps_table.add_row(
                    str(i),
                    step.name,
                    step.type.value,
                    outputs,
                    condition,
                )

            console.print(steps_table)

        # Validation status
        errors = validate_recipe(recipe)
        if errors:
            console.print(f"\n[yellow]⚠ Recipe has validation warnings:[/yellow]")
            for error in errors:
                console.print(f"  [yellow]• {error}[/yellow]")
        else:
            console.print(f"\n[green]✓ Recipe is valid[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
    except ValidationError as e:
        console.print(f"[red]Schema validation failed:[/red]")
        console.print(f"[red]{e}[/red]")
    except yaml.YAMLError as e:
        console.print(f"[red]YAML syntax error:[/red]")
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
