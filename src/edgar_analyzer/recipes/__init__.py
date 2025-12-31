"""Recipe system for EDGAR pipeline automation.

The recipe system provides a declarative way to define data extraction pipelines
using YAML files. Recipes can include multiple steps, parameters, and sub-recipes.

Example:
    from edgar_analyzer.recipes import load_recipe, execute_recipe

    recipe = load_recipe("recipes/fortune100.yaml")
    result = await execute_recipe(recipe, parameters={"rank_start": 1, "rank_end": 10})
"""

from edgar_analyzer.recipes.loader import load_recipe, discover_recipes, validate_recipe
from edgar_analyzer.recipes.schema import (
    Recipe,
    Step,
    Parameter,
    StepType,
    ParameterType,
)
from edgar_analyzer.recipes.runner import RecipeRunner, StepResult
from edgar_analyzer.recipes.context import ExecutionContext

__all__ = [
    "load_recipe",
    "discover_recipes",
    "validate_recipe",
    "Recipe",
    "Step",
    "Parameter",
    "StepType",
    "ParameterType",
    "RecipeRunner",
    "StepResult",
    "ExecutionContext",
]
