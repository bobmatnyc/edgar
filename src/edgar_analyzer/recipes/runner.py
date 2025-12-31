"""Recipe runner for orchestrating recipe execution.

This module provides the main orchestrator for executing recipes, managing step
execution, handling errors, and tracking execution state.
"""

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import structlog

from edgar_analyzer.recipes.loader import ensure_recipe_dirs
from edgar_analyzer.recipes.schema import Recipe, Step, StepType, ParameterType

logger = structlog.get_logger(__name__)


@dataclass
class StepResult:
    """Result of executing a single recipe step.

    Attributes:
        step_name: Name of the step that was executed
        success: Whether the step completed successfully
        outputs: Dictionary of step output values
        error: Error message if step failed (None if successful)
        duration: Time taken to execute the step in seconds
    """

    step_name: str
    success: bool
    outputs: dict[str, Any]
    error: Optional[str] = None
    duration: float = 0.0


class RecipeRunner:
    """Main orchestrator for recipe execution.

    The RecipeRunner manages the complete lifecycle of recipe execution:
    - Parameter resolution and validation
    - Step execution in sequence
    - Conditional step execution
    - Error handling and recovery
    - Context management for step outputs

    Example:
        runner = RecipeRunner(
            on_step_start=lambda step_name: print(f"Starting {step_name}"),
            on_step_complete=lambda result: print(f"Completed {result.step_name}")
        )

        recipe = load_recipe("recipes/fortune100")
        results = await runner.run(recipe, {"rank_start": 1, "rank_end": 10})
    """

    def __init__(
        self,
        on_step_start: Optional[Callable[[str], None]] = None,
        on_step_complete: Optional[Callable[[StepResult], None]] = None,
    ):
        """Initialize the recipe runner.

        Args:
            on_step_start: Optional callback invoked when a step starts.
                Receives step name as argument.
            on_step_complete: Optional callback invoked when a step completes.
                Receives StepResult as argument.
        """
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete

        # Lazy-initialized handlers (to avoid circular imports)
        self._python_handler: Optional[Any] = None
        self._extractor_handler: Optional[Any] = None
        self._sub_recipe_handler: Optional[Any] = None

    async def run(
        self, recipe: Recipe, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Execute a recipe with the provided parameters.

        This is the main entry point for recipe execution. It:
        1. Ensures recipe directories exist
        2. Resolves and validates parameters
        3. Executes steps in sequence
        4. Handles conditional execution
        5. Manages execution context
        6. Returns all step outputs

        Args:
            recipe: Recipe to execute
            params: Parameters to pass to the recipe (optional)

        Returns:
            Dictionary mapping step names to their output values

        Raises:
            RuntimeError: If a step fails and error_handling.on_step_failure is "stop"
            ValueError: If required parameters are missing or invalid

        Example:
            recipe = load_recipe("recipes/fortune100")
            results = await runner.run(recipe, {
                "rank_start": 1,
                "rank_end": 10,
                "output_format": "json"
            })
            print(f"Extracted data: {results['extract_sct']}")
        """
        logger.info("starting_recipe_execution", recipe_name=recipe.name)

        # Ensure recipe directories exist
        ensure_recipe_dirs(recipe)

        # Resolve parameters (merge provided with defaults, validate required)
        resolved_params = self._resolve_params(recipe, params or {})
        logger.debug("resolved_parameters", params=resolved_params)

        # Initialize execution context
        from edgar_analyzer.recipes.context import ExecutionContext

        context = ExecutionContext(
            params=resolved_params,
            recipe_dir=recipe.recipe_dir,
        )

        # Execute steps in sequence
        all_outputs: dict[str, Any] = {}
        error_handling = recipe.error_handling or {}
        on_step_failure = error_handling.get("on_step_failure", "stop")

        for step in recipe.steps:
            # Evaluate condition (if present)
            if step.condition:
                should_execute = self._evaluate_condition(step.condition, context)
                if not should_execute:
                    logger.info(
                        "skipping_step_condition_false",
                        step_name=step.name,
                        condition=step.condition,
                    )
                    continue

            # Notify step start
            if self.on_step_start:
                self.on_step_start(step.name)

            logger.info(
                "executing_step", step_name=step.name, step_type=step.type.value
            )

            # Execute step
            start_time = time.time()
            try:
                step_result = await self._execute_step(step, context)
                duration = time.time() - start_time

                # Store outputs in context
                if step_result and isinstance(step_result, dict):
                    context.set_step_outputs(step.name, step_result)
                    all_outputs[step.name] = step_result

                result = StepResult(
                    step_name=step.name,
                    success=True,
                    outputs=step_result or {},
                    duration=duration,
                )

                logger.info(
                    "step_completed",
                    step_name=step.name,
                    duration=duration,
                    outputs=step_result,
                )

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"{type(e).__name__}: {str(e)}"

                result = StepResult(
                    step_name=step.name,
                    success=False,
                    outputs={},
                    error=error_msg,
                    duration=duration,
                )

                logger.error(
                    "step_failed",
                    step_name=step.name,
                    error=error_msg,
                    duration=duration,
                )

                # Handle failure based on error_handling configuration
                if on_step_failure == "stop":
                    raise RuntimeError(
                        f"Step '{step.name}' failed: {error_msg}. "
                        f"Recipe execution stopped."
                    ) from e
                elif on_step_failure == "continue":
                    logger.warning(
                        "continuing_after_step_failure",
                        step_name=step.name,
                        error=error_msg,
                    )
                    # Store empty output for failed step
                    context.set_step_outputs(step.name, {})
                    all_outputs[step.name] = {}

            # Notify step complete
            if self.on_step_complete:
                self.on_step_complete(result)

        logger.info(
            "recipe_execution_complete",
            recipe_name=recipe.name,
            total_outputs=len(all_outputs),
        )

        return all_outputs

    def _resolve_params(
        self, recipe: Recipe, provided: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve recipe parameters by merging provided values with defaults.

        This method:
        1. Validates all required parameters are provided
        2. Merges provided parameters with defaults
        3. Coerces parameter types to match schema definitions
        4. Applies validation rules (min, max, pattern, etc.)

        Args:
            recipe: Recipe with parameter definitions
            provided: User-provided parameter values

        Returns:
            Dictionary of resolved parameter values with correct types

        Raises:
            ValueError: If required parameters are missing or validation fails
        """
        resolved: dict[str, Any] = {}

        for param in recipe.parameters:
            # Check if parameter is provided
            if param.name in provided:
                value = provided[param.name]
            elif param.required:
                raise ValueError(
                    f"Required parameter '{param.name}' not provided. "
                    f"Description: {param.description or 'No description'}"
                )
            else:
                # Use default (may be None for optional parameters)
                value = param.default

            # Coerce type
            try:
                value = self._coerce_type(value, param.type)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Parameter '{param.name}': failed to coerce to {param.type.value}: {e}"
                ) from e

            # Apply validation rules
            if param.validation:
                self._validate_param(param.name, value, param.type, param.validation)

            resolved[param.name] = value

        # Log any provided parameters that aren't in the schema
        for key in provided:
            if key not in resolved:
                logger.warning(
                    "unused_parameter",
                    parameter=key,
                    value=provided[key],
                    message="Parameter not defined in recipe schema",
                )

        return resolved

    def _coerce_type(self, value: Any, param_type: ParameterType) -> Any:
        """Coerce a value to the specified parameter type.

        Handles type conversion from strings (common in CLI/config) to the
        appropriate Python types.

        Args:
            value: Value to coerce
            param_type: Target parameter type

        Returns:
            Value coerced to the correct type

        Raises:
            ValueError: If value cannot be coerced to target type
        """
        # Handle None values (optional parameters with default: null)
        if value is None:
            return None

        if param_type == ParameterType.STRING:
            return str(value)

        elif param_type == ParameterType.INTEGER:
            if isinstance(value, int):
                return value
            try:
                return int(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot convert '{value}' to integer") from e

        elif param_type == ParameterType.FLOAT:
            if isinstance(value, (int, float)):
                return float(value)
            try:
                return float(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot convert '{value}' to float") from e

        elif param_type == ParameterType.BOOLEAN:
            if isinstance(value, bool):
                return value
            # Handle string representations of booleans
            if isinstance(value, str):
                lower = value.lower()
                if lower in ("true", "yes", "1", "on"):
                    return True
                elif lower in ("false", "no", "0", "off"):
                    return False
                else:
                    raise ValueError(f"Cannot convert '{value}' to boolean")
            # Handle numeric representations
            return bool(value)

        elif param_type == ParameterType.LIST:
            if isinstance(value, list):
                return value
            # Handle comma-separated strings
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            # Wrap single values in list
            return [value]

        else:
            raise ValueError(f"Unknown parameter type: {param_type}")

    def _validate_param(
        self,
        param_name: str,
        value: Any,
        param_type: ParameterType,
        validation: dict[str, Any],
    ) -> None:
        """Apply validation rules to a parameter value.

        Args:
            param_name: Name of parameter (for error messages)
            value: Value to validate
            param_type: Parameter type
            validation: Validation rules dict (min, max, pattern, etc.)

        Raises:
            ValueError: If validation fails
        """
        # Numeric range validation
        if param_type in (ParameterType.INTEGER, ParameterType.FLOAT):
            if "min" in validation and value < validation["min"]:
                raise ValueError(
                    f"Parameter '{param_name}' value {value} is less than minimum {validation['min']}"
                )
            if "max" in validation and value > validation["max"]:
                raise ValueError(
                    f"Parameter '{param_name}' value {value} is greater than maximum {validation['max']}"
                )

        # String length validation
        if param_type == ParameterType.STRING:
            if "min_length" in validation and len(value) < validation["min_length"]:
                raise ValueError(
                    f"Parameter '{param_name}' length {len(value)} is less than minimum {validation['min_length']}"
                )
            if "max_length" in validation and len(value) > validation["max_length"]:
                raise ValueError(
                    f"Parameter '{param_name}' length {len(value)} is greater than maximum {validation['max_length']}"
                )
            if "pattern" in validation:
                import re

                pattern = validation["pattern"]
                if not re.match(pattern, value):
                    raise ValueError(
                        f"Parameter '{param_name}' value '{value}' does not match pattern '{pattern}'"
                    )

        # List length validation
        if param_type == ParameterType.LIST:
            if "min_items" in validation and len(value) < validation["min_items"]:
                raise ValueError(
                    f"Parameter '{param_name}' has {len(value)} items, minimum is {validation['min_items']}"
                )
            if "max_items" in validation and len(value) > validation["max_items"]:
                raise ValueError(
                    f"Parameter '{param_name}' has {len(value)} items, maximum is {validation['max_items']}"
                )

    def _evaluate_condition(self, condition: str, context: Any) -> bool:
        """Evaluate a conditional expression for step execution.

        Supports simple boolean expressions with parameter and step output references.
        Expressions can use:
        - Comparisons: ==, !=, <, >, <=, >=
        - Boolean operators: and, or, not
        - Parameter references: $params.name
        - Step output references: $steps.step_name.output

        Args:
            condition: Condition expression string
            context: ExecutionContext with parameters and step outputs

        Returns:
            True if condition evaluates to true, False otherwise

        Example:
            "$params.include_sct == true"
            "$params.rank_start < 10"
            "$steps.load_companies.count > 0"
        """
        # Replace parameter references
        expr = condition
        for param_name, param_value in context.parameters.items():
            placeholder = f"$params.{param_name}"
            if placeholder in expr:
                # Quote strings for safe evaluation
                if isinstance(param_value, str):
                    expr = expr.replace(placeholder, f"'{param_value}'")
                else:
                    expr = expr.replace(placeholder, str(param_value))

        # Replace step output references
        for step_name, step_output in context.step_outputs.items():
            # Handle common patterns like $steps.step_name.field
            if f"$steps.{step_name}." in expr:
                # Extract field access (e.g., $steps.load_companies.count)
                import re

                pattern = rf"\$steps\.{step_name}\.(\w+)"
                matches = re.findall(pattern, expr)
                for field in matches:
                    placeholder = f"$steps.{step_name}.{field}"
                    if isinstance(step_output, dict) and field in step_output:
                        value = step_output[field]
                        if isinstance(value, str):
                            expr = expr.replace(placeholder, f"'{value}'")
                        else:
                            expr = expr.replace(placeholder, str(value))
                    else:
                        # Field not found, replace with None
                        expr = expr.replace(placeholder, "None")

        # Evaluate the expression
        try:
            # Use eval with a restricted namespace for safety
            # Only allow boolean operations and comparisons
            safe_dict = {
                "__builtins__": {
                    "True": True,
                    "False": False,
                    "None": None,
                }
            }
            result = eval(expr, safe_dict)
            logger.debug("evaluated_condition", condition=condition, result=result)
            return bool(result)
        except Exception as e:
            logger.error(
                "condition_evaluation_failed",
                condition=condition,
                expression=expr,
                error=str(e),
            )
            # Default to False if evaluation fails
            return False

    async def _execute_step(self, step: Step, context: Any) -> dict[str, Any]:
        """Execute a single step using the appropriate handler.

        Dispatches to type-specific handlers (python, extractor, sub_recipe) based
        on the step type.

        Args:
            step: Step to execute
            context: ExecutionContext with parameters and outputs

        Returns:
            Dictionary of step outputs

        Raises:
            ValueError: If step type is unknown or handler is not available
            RuntimeError: If step execution fails
        """
        if step.type == StepType.PYTHON:
            if not self._python_handler:
                # Lazy import to avoid circular dependencies
                from edgar_analyzer.recipes.handlers.python import (
                    PythonStepHandler,
                )

                self._python_handler = PythonStepHandler()
            return await self._python_handler.execute(step, context)

        elif step.type == StepType.EXTRACTOR:
            if not self._extractor_handler:
                # Lazy import to avoid circular dependencies
                from edgar_analyzer.recipes.handlers.extractor_handler import (
                    ExtractorHandler,
                )

                self._extractor_handler = ExtractorHandler()
            return await self._extractor_handler.execute(step, context)

        elif step.type == StepType.SUB_RECIPE:
            if not self._sub_recipe_handler:
                # Lazy import to avoid circular dependencies
                from edgar_analyzer.recipes.handlers.sub_recipe_handler import (
                    SubRecipeHandler,
                )

                self._sub_recipe_handler = SubRecipeHandler(runner=self)
            return await self._sub_recipe_handler.execute(step, context)

        elif step.type == StepType.SHELL:
            raise ValueError(
                f"Shell step type is not yet implemented. "
                f"Use python or extractor steps instead for step '{step.name}'."
            )

        else:
            raise ValueError(f"Unknown step type: {step.type}")
