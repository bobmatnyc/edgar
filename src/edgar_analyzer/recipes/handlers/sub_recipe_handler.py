"""Sub-recipe step handler for executing nested recipes.

This module provides the SubRecipeHandler for executing sub-recipes as steps
within a parent recipe. Sub-recipes are loaded from sibling directories and executed
with their own parameter context.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from edgar_analyzer.recipes.context import ExecutionContext
from edgar_analyzer.recipes.loader import load_recipe
from edgar_analyzer.recipes.schema import Step

if TYPE_CHECKING:
    from edgar_analyzer.recipes.runner import RecipeRunner

logger = structlog.get_logger(__name__)


class SubRecipeHandler:
    """Handler for executing sub-recipe steps.

    Sub-recipes allow composition of recipes by referencing other recipe directories.
    The sub-recipe is loaded, executed with mapped parameters, and outputs are
    returned to the parent recipe context.

    Example YAML:
        - name: extract_sct
          type: sub_recipe
          sub_recipe:
            recipe: sct_extraction  # Directory name
          inputs:
            cik: $params.cik
            year: $params.year
          outputs:
            - sct_data
            - executive_count

    Sub-recipe Resolution:
        1. First try: parent_recipe_dir.parent / recipe_name
        2. Then try: parent_recipe_dir / recipe_name

    This allows sub-recipes to be:
        - Sibling directories (preferred): recipes/sct_extraction/
        - Nested directories: recipes/parent/sub_recipe/
    """

    def __init__(self, runner: "RecipeRunner") -> None:
        """Initialize the sub-recipe handler.

        Args:
            runner: Reference to parent RecipeRunner for recursive execution
        """
        self.runner = runner

    async def execute(self, step: Step, context: ExecutionContext) -> dict[str, Any]:
        """Execute a sub-recipe step.

        Args:
            step: Step configuration with sub_recipe settings
            context: Current execution context with params and step outputs

        Returns:
            Dictionary of sub-recipe outputs

        Raises:
            ValueError: If sub_recipe config is missing or sub-recipe not found
            RuntimeError: If sub-recipe execution fails
        """
        # Validate sub_recipe configuration
        if not step.sub_recipe:
            raise ValueError(
                f"Step '{step.name}': sub_recipe type requires sub_recipe configuration"
            )

        recipe_name = step.sub_recipe.recipe
        logger.info(
            "executing_sub_recipe",
            step_name=step.name,
            sub_recipe_name=recipe_name,
        )

        # Resolve sub-recipe directory
        sub_recipe_dir = self._resolve_sub_recipe_path(recipe_name, context)
        logger.debug(
            "resolved_sub_recipe_path",
            recipe_name=recipe_name,
            path=str(sub_recipe_dir),
        )

        # Load sub-recipe
        try:
            sub_recipe = load_recipe(sub_recipe_dir)
            logger.debug(
                "loaded_sub_recipe",
                recipe_name=sub_recipe.name,
                step_count=len(sub_recipe.steps),
                parameter_count=len(sub_recipe.parameters),
            )
        except Exception as e:
            raise ValueError(
                f"Failed to load sub-recipe '{recipe_name}' from {sub_recipe_dir}: {e}"
            ) from e

        # Resolve step inputs as sub-recipe parameters
        sub_params = self._resolve_sub_recipe_params(step, context)
        logger.debug("resolved_sub_recipe_params", params=sub_params)

        # Execute sub-recipe recursively
        try:
            sub_outputs = await self.runner.run(sub_recipe, sub_params)
            logger.info(
                "sub_recipe_completed",
                step_name=step.name,
                sub_recipe_name=recipe_name,
                output_keys=list(sub_outputs.keys()),
            )
            return sub_outputs

        except Exception as e:
            logger.error(
                "sub_recipe_failed",
                step_name=step.name,
                sub_recipe_name=recipe_name,
                error=str(e),
            )
            raise RuntimeError(
                f"Sub-recipe '{recipe_name}' failed in step '{step.name}': {e}"
            ) from e

    def _resolve_sub_recipe_path(
        self, recipe_name: str, context: ExecutionContext
    ) -> Path:
        """Resolve the path to a sub-recipe directory.

        Resolution order:
        1. Sibling directory: context.recipe_dir.parent / recipe_name
        2. Child directory: context.recipe_dir / recipe_name

        Args:
            recipe_name: Name of the sub-recipe (directory name)
            context: Current execution context

        Returns:
            Resolved Path to sub-recipe directory

        Raises:
            ValueError: If sub-recipe directory cannot be found
        """
        if not context.recipe_dir:
            raise ValueError(
                "Cannot resolve sub-recipe path: recipe_dir not set in context"
            )

        # Try sibling directory first (preferred pattern)
        # recipes/parent/ -> recipes/sub_recipe/
        sibling_path = context.recipe_dir.parent / recipe_name
        if sibling_path.exists() and sibling_path.is_dir():
            config_path = sibling_path / "config.yaml"
            if config_path.exists():
                return sibling_path
            logger.debug(
                "sibling_path_found_but_no_config",
                path=str(sibling_path),
                recipe_name=recipe_name,
            )

        # Try child directory (nested pattern)
        # recipes/parent/sub_recipe/
        child_path = context.recipe_dir / recipe_name
        if child_path.exists() and child_path.is_dir():
            config_path = child_path / "config.yaml"
            if config_path.exists():
                return child_path
            logger.debug(
                "child_path_found_but_no_config",
                path=str(child_path),
                recipe_name=recipe_name,
            )

        # Sub-recipe not found
        raise ValueError(
            f"Sub-recipe '{recipe_name}' not found. Searched:\n"
            f"  - Sibling: {sibling_path}\n"
            f"  - Child: {child_path}\n"
            f"Ensure the recipe directory exists and contains config.yaml"
        )

    def _resolve_sub_recipe_params(
        self, step: Step, context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve step inputs as parameters for the sub-recipe.

        Step inputs are mapped to sub-recipe parameters. Variable references
        ($params.*, $steps.*.*) are resolved from the parent context.

        Args:
            step: Step configuration with inputs
            context: Parent execution context

        Returns:
            Dictionary of resolved parameter values for sub-recipe
        """
        if not step.inputs:
            return {}

        # Resolve all input values using context
        return {key: context.resolve_value(value) for key, value in step.inputs.items()}
