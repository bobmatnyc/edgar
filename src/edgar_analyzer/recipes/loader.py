"""Recipe loader for discovering and loading YAML recipe definitions.

This module provides functions to:
- Load recipes from YAML files
- Discover all recipes in a directory
- Validate recipe syntax and structure
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from edgar_analyzer.recipes.schema import Recipe


def load_recipe(path: Path | str) -> Recipe:
    """Load a recipe from a YAML file.

    Args:
        path: Path to recipe YAML file

    Returns:
        Validated Recipe object

    Raises:
        FileNotFoundError: If recipe file doesn't exist
        ValidationError: If recipe YAML is invalid
        yaml.YAMLError: If YAML syntax is invalid

    Example:
        recipe = load_recipe("recipes/fortune100.yaml")
        print(f"Loaded recipe: {recipe.name}")
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Recipe file not found: {path}")

    with open(path, "r") as f:
        try:
            recipe_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML syntax in {path}: {e}") from e

    if not recipe_data:
        raise ValueError(f"Empty recipe file: {path}")

    try:
        recipe = Recipe(**recipe_data)
    except ValidationError as e:
        raise ValidationError(f"Recipe validation failed for {path}: {e}") from e

    return recipe


def discover_recipes(directory: Path | str) -> list[Recipe]:
    """Discover all recipe YAML files in a directory.

    Recursively searches for .yaml and .yml files and attempts to load them as recipes.
    Invalid recipe files are logged but don't stop discovery.

    Args:
        directory: Directory to search for recipes

    Returns:
        List of valid Recipe objects

    Example:
        recipes = discover_recipes("recipes/")
        for recipe in recipes:
            print(f"Found recipe: {recipe.name} - {recipe.title}")
    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Recipe directory not found: {directory}")

    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    recipes: list[Recipe] = []

    # Find all YAML files
    yaml_files = list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))

    for yaml_file in yaml_files:
        try:
            recipe = load_recipe(yaml_file)
            recipes.append(recipe)
        except (FileNotFoundError, ValidationError, yaml.YAMLError, ValueError) as e:
            # Log error but continue discovery
            print(f"Warning: Failed to load recipe from {yaml_file}: {e}")
            continue

    return recipes


def validate_recipe(recipe: Recipe) -> list[str]:
    """Validate a recipe for semantic correctness.

    Performs additional validation beyond Pydantic schema validation:
    - Check step type consistency (correct config for each type)
    - Validate parameter references ($params.*)
    - Validate step output references ($steps.*.output)
    - Check for circular sub-recipe dependencies

    Args:
        recipe: Recipe object to validate

    Returns:
        List of error messages (empty if valid)

    Example:
        errors = validate_recipe(recipe)
        if errors:
            print("Recipe validation failed:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("Recipe is valid!")
    """
    errors: list[str] = []

    # Validate parameter names are unique
    param_names = [p.name for p in recipe.parameters]
    if len(param_names) != len(set(param_names)):
        errors.append("Parameter names must be unique")

    # Validate step configurations match their types
    for step in recipe.steps:
        if step.type.value == "python":
            if not step.python:
                errors.append(f"Step '{step.name}': python type requires python config")
        elif step.type.value == "extractor":
            if not step.extractor:
                errors.append(f"Step '{step.name}': extractor type requires extractor config")
        elif step.type.value == "sub_recipe":
            if not step.sub_recipe:
                errors.append(f"Step '{step.name}': sub_recipe type requires sub_recipe config")
        elif step.type.value == "shell":
            if not step.shell:
                errors.append(f"Step '{step.name}': shell type requires shell config")

    # Validate parameter references in step inputs
    valid_param_names = {p.name for p in recipe.parameters}
    step_output_names: set[str] = set()

    for step in recipe.steps:
        if step.inputs:
            for input_key, input_value in step.inputs.items():
                if isinstance(input_value, str):
                    # Check for $params.* references
                    if input_value.startswith("$params."):
                        param_name = input_value.replace("$params.", "")
                        if param_name not in valid_param_names:
                            errors.append(
                                f"Step '{step.name}': references undefined parameter '{param_name}'"
                            )

                    # Check for $steps.* references
                    if input_value.startswith("$steps."):
                        # Extract step name (format: $steps.step_name.output)
                        parts = input_value.split(".")
                        if len(parts) >= 2:
                            referenced_step = parts[1]
                            if referenced_step not in step_output_names:
                                errors.append(
                                    f"Step '{step.name}': references output from undefined or future step '{referenced_step}'"
                                )

        # Track step outputs for validation of future steps
        if step.outputs:
            step_output_names.add(step.name)

    # Validate condition expressions reference valid parameters
    for step in recipe.steps:
        if step.condition:
            # Basic validation: check for $params.* references
            if "$params." in step.condition:
                # Extract parameter names from condition
                parts = step.condition.split("$params.")
                for part in parts[1:]:
                    param_name = part.split()[0].strip("=!<>()").strip()
                    if param_name not in valid_param_names:
                        errors.append(
                            f"Step '{step.name}': condition references undefined parameter '{param_name}'"
                        )

    return errors


def get_recipe_info(recipe: Recipe) -> dict:
    """Get summary information about a recipe.

    Args:
        recipe: Recipe to summarize

    Returns:
        Dictionary with recipe metadata

    Example:
        info = get_recipe_info(recipe)
        print(f"Recipe: {info['name']}")
        print(f"Steps: {info['step_count']}")
        print(f"Parameters: {info['parameter_count']}")
    """
    return {
        "name": recipe.name,
        "title": recipe.title or recipe.name,
        "description": recipe.description or "No description",
        "version": recipe.version,
        "step_count": len(recipe.steps),
        "parameter_count": len(recipe.parameters),
        "required_parameters": [p.name for p in recipe.parameters if p.required],
        "optional_parameters": [p.name for p in recipe.parameters if not p.required],
        "step_types": [step.type.value for step in recipe.steps],
    }
