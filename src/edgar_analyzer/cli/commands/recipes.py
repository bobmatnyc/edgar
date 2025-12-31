"""CLI commands for recipe management.

Commands:
- edgar recipes list - List available recipes
- edgar recipes validate <recipe> - Validate a recipe directory
- edgar recipes info <recipe> - Show recipe information
- edgar recipes init <name> - Create new recipe directory structure
- edgar recipes run <recipe> - Execute a recipe
"""

from pathlib import Path
import asyncio

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from pydantic import ValidationError
import yaml

from edgar_analyzer.recipes import (
    load_recipe,
    discover_recipes,
    validate_recipe,
    RecipeRunner,
)
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
    help="Directory to search for recipe directories (default: recipes/)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information including directory paths",
)
def list_recipes(directory: Path, verbose: bool):
    """List available recipes.

    Discovers all recipe directories containing config.yaml and displays
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
            console.print(
                "[dim]Tip: Recipe directories must contain a config.yaml file[/dim]"
            )
            return

        # Create table
        table = Table(title=f"Available Recipes ({len(recipes)} found)")
        table.add_column("Name", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Steps", style="green", justify="right")
        table.add_column("Parameters", style="blue", justify="right")

        if verbose:
            table.add_column("Location", style="magenta")
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
                # Show relative path from current directory
                recipe_location = recipe.recipe_dir.name if recipe.recipe_dir else "N/A"
                row.append(recipe_location)

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
@click.argument("recipe_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation results",
)
def validate_recipe_cmd(recipe_dir: Path, verbose: bool):
    """Validate a recipe directory.

    Checks recipe syntax, schema validity, and semantic correctness.
    The recipe directory must contain a config.yaml file.

    Example:
        edgar recipes validate recipes/fortune100
        edgar recipes validate my_recipe/ --verbose
    """
    console.print(f"[cyan]Validating recipe: {recipe_dir}[/cyan]\n")

    try:
        # Load recipe (includes Pydantic validation)
        recipe = load_recipe(recipe_dir)

        console.print("[green]✓ YAML syntax valid[/green]")
        console.print("[green]✓ Schema validation passed[/green]")

        # Semantic validation
        errors = validate_recipe(recipe)

        if errors:
            console.print("\n[red]✗ Semantic validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
            return

        console.print("[green]✓ Semantic validation passed[/green]")

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

        console.print("\n[bold green]Recipe is valid! ✓[/bold green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
    except ValidationError as e:
        console.print("[red]Schema validation failed:[/red]")
        console.print(f"[red]{e}[/red]")
    except yaml.YAMLError as e:
        console.print("[red]YAML syntax error:[/red]")
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@recipes_cli.command(name="info")
@click.argument("recipe_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--show-steps",
    "-s",
    is_flag=True,
    help="Show detailed step information",
)
def show_recipe_info(recipe_dir: Path, show_steps: bool):
    """Show detailed recipe information.

    Displays recipe metadata, parameters, and steps from a recipe directory.

    Example:
        edgar recipes info recipes/fortune100
        edgar recipes info my_recipe/ --show-steps
    """
    console.print(f"[cyan]Loading recipe: {recipe_dir}[/cyan]\n")

    try:
        recipe = load_recipe(recipe_dir)
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
            console.print("\n[yellow]⚠ Recipe has validation warnings:[/yellow]")
            for error in errors:
                console.print(f"  [yellow]• {error}[/yellow]")
        else:
            console.print("\n[green]✓ Recipe is valid[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
    except ValidationError as e:
        console.print("[red]Schema validation failed:[/red]")
        console.print(f"[red]{e}[/red]")
    except yaml.YAMLError as e:
        console.print("[red]YAML syntax error:[/red]")
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@recipes_cli.command(name="init")
@click.argument("name")
@click.option(
    "--directory",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("recipes"),
    help="Parent directory for recipe (default: recipes/)",
)
@click.option(
    "--title",
    "-t",
    help="Recipe title (defaults to capitalized name)",
)
@click.option(
    "--description",
    help="Recipe description",
)
def init_recipe(name: str, directory: Path, title: str | None, description: str | None):
    """Create a new recipe directory structure.

    Scaffolds a new recipe with:
    - config.yaml template
    - input/ directory for input files
    - output/ directory for generated files
    - README.md with basic documentation

    Example:
        edgar recipes init my_recipe
        edgar recipes init fraud_detection --title "Fraud Detection Pipeline"
        edgar recipes init custom --directory my_recipes/
    """
    # Validate recipe name
    if not name.isidentifier():
        console.print(
            f"[red]Error: Recipe name must be a valid identifier: {name}[/red]"
        )
        console.print(
            "[dim]Use only letters, numbers, and underscores (no spaces)[/dim]"
        )
        return

    recipe_dir = directory / name

    # Check if recipe directory already exists
    if recipe_dir.exists():
        console.print(
            f"[red]Error: Recipe directory already exists: {recipe_dir}[/red]"
        )
        return

    try:
        # Create directory structure
        recipe_dir.mkdir(parents=True, exist_ok=False)
        (recipe_dir / "input").mkdir()
        (recipe_dir / "output").mkdir()

        console.print(f"[green]✓ Created recipe directory: {recipe_dir}[/green]")

        # Generate config.yaml template
        recipe_title = title or name.replace("_", " ").title()
        recipe_description = description or f"Recipe for {recipe_title.lower()}"

        config_template = f"""version: "1.0"
name: {name}
title: {recipe_title}
description: |
  {recipe_description}

parameters:
  - name: output_dir
    type: string
    required: false
    default: "output/{name}"
    description: Output directory for results

  # Add your custom parameters here
  # - name: my_param
  #   type: string
  #   required: true
  #   description: Description of my parameter

steps:
  # Add your recipe steps here
  # Example Python step:
  # - name: my_step
  #   type: python
  #   python:
  #     function: my_module.my_function
  #   inputs:
  #     param: $params.my_param
  #   outputs:
  #     - result

  # Example extractor step:
  # - name: extract_data
  #   type: extractor
  #   extractor:
  #     extractor: MyAdapter
  #     filing_type: "10-K"
  #   inputs:
  #     cik: $params.cik
  #   outputs:
  #     - extracted_data

  # Example sub-recipe step:
  # - name: run_sub_recipe
  #   type: sub_recipe
  #   sub_recipe:
  #     recipe: other_recipe_name
  #   inputs:
  #     data: $steps.my_step.result
  #   outputs:
  #     - final_result

error_handling:
  on_step_failure: stop  # or 'continue'
  collect_errors: true
  max_retries: 2
"""

        config_path = recipe_dir / "config.yaml"
        with open(config_path, "w") as f:
            f.write(config_template)

        console.print("[green]✓ Created config.yaml[/green]")

        # Generate README.md
        readme_content = f"""# {recipe_title}

{recipe_description}

## Directory Structure

```
{name}/
├── config.yaml      # Recipe definition
├── input/           # Input files (optional)
├── output/          # Output files (generated)
└── README.md        # This file
```

## Usage

Validate the recipe:
```bash
edgar recipes validate recipes/{name}
```

Show recipe info:
```bash
edgar recipes info recipes/{name}
```

Execute the recipe (once implemented):
```bash
edgar recipes run recipes/{name} --param value
```

## Parameters

- `output_dir`: Output directory for results (default: output/{name})

Add more parameters in `config.yaml` as needed.

## Steps

Add your recipe steps in `config.yaml`. See the template for examples.

## Development Notes

Add any development notes, requirements, or special instructions here.
"""

        readme_path = recipe_dir / "README.md"
        with open(readme_path, "w") as f:
            f.write(readme_content)

        console.print("[green]✓ Created README.md[/green]")

        # Summary
        console.print(
            f"\n[bold green]Recipe '{name}' created successfully![/bold green]"
        )
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print(f"  1. Edit {config_path} to define your recipe")
        console.print(f"  2. Add input files to {recipe_dir / 'input'}/")
        console.print(
            f"  3. Validate with: [bold]edgar recipes validate {recipe_dir}[/bold]"
        )
        console.print(
            f"  4. View info with: [bold]edgar recipes info {recipe_dir}[/bold]"
        )

    except Exception as e:
        console.print(f"[red]Error creating recipe: {e}[/red]")
        # Clean up on error
        if recipe_dir.exists():
            import shutil

            shutil.rmtree(recipe_dir)
            console.print("[yellow]Cleaned up partial recipe directory[/yellow]")


@recipes_cli.command(name="run")
@click.argument("recipe_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--param", "-p", multiple=True, help="Parameter in key=value format")
@click.option("--dry-run", is_flag=True, help="Show execution plan without running")
def run_recipe(recipe_dir: Path, param: tuple, dry_run: bool):
    """Execute a recipe.

    Runs all steps in sequence with variable substitution.

    Examples:
        edgar recipes run recipes/fortune100 -p rank_start=1 -p rank_end=10
        edgar recipes run recipes/sct_extraction --dry-run
    """
    console.print(f"[cyan]Loading recipe: {recipe_dir}[/cyan]\n")

    try:
        # Load and validate recipe
        recipe = load_recipe(recipe_dir)

        # Parse parameters from --param options
        params = {}
        for p in param:
            if "=" not in p:
                console.print(
                    f"[red]Error: Invalid parameter format '{p}'. Expected key=value[/red]"
                )
                return

            key, value = p.split("=", 1)  # Split on first = only
            params[key.strip()] = value.strip()

        # Show recipe info
        info = get_recipe_info(recipe)
        console.print(
            Panel(
                f"[bold]{info['title']}[/bold]\n"
                f"{info['description']}\n\n"
                f"[cyan]Steps:[/cyan] {info['step_count']}\n"
                f"[cyan]Parameters:[/cyan] {len(params)} provided, {info['parameter_count']} defined",
                title="Recipe Execution Plan",
            )
        )

        # Dry run: show execution plan
        if dry_run:
            console.print(
                "\n[yellow]DRY RUN MODE - No steps will be executed[/yellow]\n"
            )

            # Show parameters
            if params:
                param_table = Table(title="Parameters")
                param_table.add_column("Name", style="cyan")
                param_table.add_column("Value", style="green")

                for key, value in params.items():
                    param_table.add_row(key, value)

                console.print(param_table)

            # Show step execution plan
            steps_table = Table(title="Step Execution Plan")
            steps_table.add_column("Order", style="blue", justify="right")
            steps_table.add_column("Step Name", style="cyan")
            steps_table.add_column("Type", style="magenta")
            steps_table.add_column("Condition", style="yellow")

            for i, step in enumerate(recipe.steps, 1):
                condition = step.condition if step.condition else "-"
                steps_table.add_row(str(i), step.name, step.type.value, condition)

            console.print(steps_table)

            console.print(
                "\n[green]Dry run complete. Use without --dry-run to execute.[/green]"
            )
            return

        # Execute recipe with progress tracking
        console.print("\n[green]Starting recipe execution...[/green]\n")

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Track current step
            current_task = None

            def on_step_start(step_name: str):
                nonlocal current_task
                if current_task is not None:
                    progress.remove_task(current_task)
                current_task = progress.add_task(f"Executing: {step_name}", total=None)

            def on_step_complete(result):
                nonlocal current_task
                if current_task is not None:
                    progress.remove_task(current_task)
                    current_task = None

                # Show result
                if result.success:
                    console.print(
                        f"[green]✓ {result.step_name}[/green] ({result.duration:.2f}s)"
                    )
                else:
                    console.print(f"[red]✗ {result.step_name}[/red] - {result.error}")

            # Create runner with callbacks
            runner = RecipeRunner(
                on_step_start=on_step_start, on_step_complete=on_step_complete
            )

            # Run the recipe
            try:
                results = asyncio.run(runner.run(recipe, params))

                # Show summary
                console.print("\n[bold green]Recipe execution complete! ✓[/bold green]")
                console.print(f"[cyan]Steps completed:[/cyan] {len(results)}")

                # Show output summary
                if results:
                    console.print("\n[cyan]Step Outputs:[/cyan]")
                    for step_name, outputs in results.items():
                        if outputs:
                            console.print(
                                f"  [green]• {step_name}:[/green] {len(outputs)} outputs"
                            )

            except ValueError as e:
                console.print(f"\n[red]Parameter error: {e}[/red]")
            except RuntimeError as e:
                console.print(f"\n[red]Execution failed: {e}[/red]")
            except Exception as e:
                console.print(f"\n[red]Unexpected error: {e}[/red]")
                raise

    except FileNotFoundError as e:
        console.print(f"[red]Error: Recipe not found - {e}[/red]")
    except ValidationError as e:
        console.print("[red]Recipe validation failed:[/red]")
        console.print(f"[red]{e}[/red]")
    except yaml.YAMLError as e:
        console.print("[red]YAML syntax error:[/red]")
        console.print(f"[red]{e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise
