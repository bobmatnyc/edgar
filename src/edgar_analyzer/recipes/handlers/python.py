"""Python function step handler for recipe execution.

Dynamically imports and executes Python functions with input/output mapping.
"""

import asyncio
import importlib
from typing import Any

import structlog

from edgar_analyzer.recipes.context import ExecutionContext
from edgar_analyzer.recipes.schema import Step

logger = structlog.get_logger(__name__)


class PythonStepHandler:
    """Handler for executing Python function steps.

    Dynamically imports Python modules and executes functions with runtime
    input resolution and output mapping.

    Features:
    - Dynamic module and function import from fully qualified paths
    - Input resolution via ExecutionContext (supports $params.* and $steps.*.*)
    - Automatic sync/async function detection and execution
    - Flexible output mapping (single/multiple, dict/tuple/scalar)

    Example Step Configuration:
        ```yaml
        - name: load_companies
          type: python
          python:
            function: edgar_analyzer.data.fortune100_loader.load_fortune_100_companies
          inputs:
            rank_start: $params.rank_start
            rank_end: $params.rank_end
          outputs:
            - companies
        ```

    Output Mapping Strategies:
    1. Single output + scalar/list result: `{output_name: result}`
    2. Single output + dict result: `{output_name: result}` (preserve dict)
    3. Multiple outputs + dict result: extract matching keys from dict
    4. Multiple outputs + tuple/list result: positional mapping
    """

    async def execute(self, step: Step, context: ExecutionContext) -> dict[str, Any]:
        """Execute a Python function step.

        Args:
            step: Step definition with python.function and inputs
            context: Execution context for input resolution

        Returns:
            Dictionary of output values mapped to output names

        Raises:
            ValueError: If function path is missing or invalid
            ValueError: If module or function cannot be imported
            Exception: If function execution fails (wrapped with context)

        Example:
            >>> handler = PythonStepHandler()
            >>> step = Step(
            ...     name="load_companies",
            ...     type=StepType.PYTHON,
            ...     python=PythonStep(function="mymodule.load_data"),
            ...     inputs={"limit": 10},
            ...     outputs=["data"]
            ... )
            >>> ctx = ExecutionContext(params={})
            >>> result = await handler.execute(step, ctx)
            >>> result
            {"data": [...]}
        """
        # Validate function path
        if not step.python or not step.python.function:
            raise ValueError(
                f"Step '{step.name}' is missing python.function. "
                "Expected format: 'module.submodule.function_name'"
            )

        function_path = step.python.function
        logger.info(
            "executing_python_step",
            step_name=step.name,
            function=function_path,
            inputs=step.inputs,
            outputs=step.outputs,
        )

        # Import module and get function
        try:
            function = self._import_function(function_path)
        except (ImportError, AttributeError) as e:
            raise ValueError(
                f"Failed to import function '{function_path}' for step '{step.name}': {e}"
            ) from e

        # Resolve inputs using context
        resolved_inputs = {}
        if step.inputs:
            resolved_inputs = {
                key: context.resolve_value(value) for key, value in step.inputs.items()
            }

        logger.debug(
            "resolved_inputs",
            step_name=step.name,
            inputs=resolved_inputs,
        )

        # Execute function (handle both sync and async)
        try:
            if asyncio.iscoroutinefunction(function):
                result = await function(**resolved_inputs)
            else:
                result = function(**resolved_inputs)
        except Exception as e:
            logger.exception(
                "python_step_execution_failed",
                step_name=step.name,
                function=function_path,
                error=str(e),
            )
            raise Exception(
                f"Step '{step.name}' failed executing {function_path}: {e}"
            ) from e

        # Map result to outputs
        outputs = self._map_outputs(step.name, result, step.outputs or [])

        logger.info(
            "python_step_completed",
            step_name=step.name,
            outputs=list(outputs.keys()),
        )

        return outputs

    def _import_function(self, function_path: str) -> Any:
        """Dynamically import a function from a fully qualified path.

        Args:
            function_path: Fully qualified function path (e.g., "module.submodule.func")

        Returns:
            Imported function object

        Raises:
            ValueError: If function_path format is invalid
            ImportError: If module cannot be imported
            AttributeError: If function not found in module

        Example:
            >>> handler = PythonStepHandler()
            >>> func = handler._import_function("json.dumps")
            >>> func is json.dumps
            True
        """
        parts = function_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid function path '{function_path}'. "
                "Expected format: 'module.submodule.function_name'"
            )

        module_path, function_name = parts

        logger.debug(
            "importing_function",
            module_path=module_path,
            function_name=function_name,
        )

        # Import module
        module = importlib.import_module(module_path)

        # Get function from module
        if not hasattr(module, function_name):
            raise AttributeError(
                f"Module '{module_path}' has no function '{function_name}'. "
                f"Available: {[attr for attr in dir(module) if not attr.startswith('_')]}"
            )

        return getattr(module, function_name)

    def _map_outputs(
        self, step_name: str, result: Any, output_names: list[str]
    ) -> dict[str, Any]:
        """Map function result to named outputs.

        Mapping Strategies:
        1. No outputs declared: Return empty dict (result discarded)
        2. Single output + non-dict result: `{output_name: result}`
        3. Single output + dict result: `{output_name: result}` (preserve dict)
        4. Multiple outputs + dict result: Extract matching keys
        5. Multiple outputs + tuple/list result: Positional mapping

        Args:
            step_name: Name of step (for error messages)
            result: Function return value
            output_names: List of declared output names

        Returns:
            Dictionary mapping output names to values

        Raises:
            ValueError: If output mapping fails (missing keys, length mismatch)

        Examples:
            >>> handler = PythonStepHandler()

            # Single output, scalar result
            >>> handler._map_outputs("step1", 42, ["count"])
            {"count": 42}

            # Single output, dict result (preserved)
            >>> handler._map_outputs("step1", {"a": 1, "b": 2}, ["data"])
            {"data": {"a": 1, "b": 2}}

            # Multiple outputs, dict result (extract keys)
            >>> handler._map_outputs("step1", {"x": 10, "y": 20}, ["x", "y"])
            {"x": 10, "y": 20}

            # Multiple outputs, tuple result (positional)
            >>> handler._map_outputs("step1", (10, 20), ["x", "y"])
            {"x": 10, "y": 20}
        """
        # No outputs declared - discard result
        if not output_names:
            logger.debug(
                "no_outputs_declared",
                step_name=step_name,
                result_type=type(result).__name__,
            )
            return {}

        # Single output - wrap result
        if len(output_names) == 1:
            output_name = output_names[0]
            logger.debug(
                "single_output_mapping",
                step_name=step_name,
                output_name=output_name,
                result_type=type(result).__name__,
            )
            return {output_name: result}

        # Multiple outputs - extract from dict or positional mapping
        if isinstance(result, dict):
            # Extract matching keys from dict
            return self._map_dict_outputs(step_name, result, output_names)
        elif isinstance(result, (tuple, list)):
            # Positional mapping
            return self._map_sequence_outputs(step_name, result, output_names)
        else:
            raise ValueError(
                f"Step '{step_name}' declares {len(output_names)} outputs "
                f"but function returned {type(result).__name__}. "
                f"Expected dict or tuple/list for multiple outputs."
            )

    def _map_dict_outputs(
        self, step_name: str, result: dict[str, Any], output_names: list[str]
    ) -> dict[str, Any]:
        """Extract outputs from dict result by matching keys.

        Args:
            step_name: Name of step (for error messages)
            result: Dict returned by function
            output_names: List of declared output names

        Returns:
            Dict with extracted values

        Raises:
            ValueError: If any output name is missing from result dict

        Example:
            >>> handler = PythonStepHandler()
            >>> result = {"companies": [...], "count": 10, "extra": "ignored"}
            >>> handler._map_dict_outputs("step1", result, ["companies", "count"])
            {"companies": [...], "count": 10}
        """
        outputs = {}
        missing_keys = []

        for output_name in output_names:
            if output_name not in result:
                missing_keys.append(output_name)
            else:
                outputs[output_name] = result[output_name]

        if missing_keys:
            raise ValueError(
                f"Step '{step_name}' expects outputs {output_names} "
                f"but function result is missing keys: {missing_keys}. "
                f"Available keys: {list(result.keys())}"
            )

        logger.debug(
            "dict_output_mapping",
            step_name=step_name,
            extracted_keys=list(outputs.keys()),
        )

        return outputs

    def _map_sequence_outputs(
        self, step_name: str, result: tuple | list, output_names: list[str]
    ) -> dict[str, Any]:
        """Map outputs from tuple/list result by position.

        Args:
            step_name: Name of step (for error messages)
            result: Tuple or list returned by function
            output_names: List of declared output names

        Returns:
            Dict with positionally mapped values

        Raises:
            ValueError: If result length doesn't match output count

        Example:
            >>> handler = PythonStepHandler()
            >>> handler._map_sequence_outputs("step1", (10, 20, 30), ["x", "y", "z"])
            {"x": 10, "y": 20, "z": 30}
        """
        if len(result) != len(output_names):
            raise ValueError(
                f"Step '{step_name}' expects {len(output_names)} outputs {output_names} "
                f"but function returned {len(result)} values: {result}"
            )

        outputs = dict(zip(output_names, result))

        logger.debug(
            "sequence_output_mapping",
            step_name=step_name,
            outputs=list(outputs.keys()),
        )

        return outputs
