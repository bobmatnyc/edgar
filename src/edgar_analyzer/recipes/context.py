"""Execution context for recipe runners.

Manages parameter resolution and step output tracking during recipe execution.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExecutionContext:
    """Runtime context for recipe execution.

    Tracks recipe parameters and step outputs, enabling dynamic value resolution
    through variable references ($params.*, $steps.*.*).

    Attributes:
        params: Recipe parameter values provided at runtime
        steps: Step outputs keyed by step name, populated as steps complete
        recipe_dir: Path to recipe directory (for file resolution)

    Example:
        >>> ctx = ExecutionContext(
        ...     params={"rank_start": 1, "rank_end": 10},
        ...     recipe_dir=Path("recipes/fortune100")
        ... )
        >>> ctx.resolve_value("$params.rank_start")
        1
        >>> ctx.set_step_outputs("load_companies", {"companies": [...]})
        >>> ctx.resolve_value("$steps.load_companies.companies")
        [...]
    """

    params: dict[str, Any]
    steps: dict[str, dict[str, Any]] = field(default_factory=dict)
    recipe_dir: Path | None = None

    def resolve_value(self, value: Any) -> Any:
        """Resolve variable references in values.

        Supports:
        - Parameter references: $params.name -> params["name"]
        - Step output references: $steps.step_name.output_name -> steps["step_name"]["output_name"]
        - Nested structures: Recursively resolves dicts and lists

        Args:
            value: Value to resolve (may contain variable references)

        Returns:
            Resolved value with all references replaced

        Raises:
            ValueError: If reference points to unknown parameter or step output

        Examples:
            >>> ctx = ExecutionContext(params={"count": 5})
            >>> ctx.resolve_value("$params.count")
            5
            >>> ctx.resolve_value(["$params.count", 10])
            [5, 10]
            >>> ctx.resolve_value({"limit": "$params.count"})
            {"limit": 5}
        """
        # Handle string references
        if isinstance(value, str):
            if value.startswith("$params."):
                return self._resolve_param_reference(value)
            elif value.startswith("$steps."):
                return self._resolve_step_reference(value)
            return value

        # Handle nested structures
        if isinstance(value, dict):
            return {k: self.resolve_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve_value(item) for item in value]

        # Return primitives as-is
        return value

    def _resolve_param_reference(self, ref: str) -> Any:
        """Resolve $params.name reference.

        Args:
            ref: Reference string (e.g., "$params.rank_start")

        Returns:
            Parameter value

        Raises:
            ValueError: If parameter not found
        """
        param_name = ref.removeprefix("$params.")
        if param_name not in self.params:
            raise ValueError(
                f"Unknown parameter reference: {ref}. "
                f"Available parameters: {list(self.params.keys())}"
            )
        return self.params[param_name]

    def _resolve_step_reference(self, ref: str) -> Any:
        """Resolve $steps.step_name.output_name[.nested.path] reference.

        Supports nested access for sub-recipe outputs:
        - $steps.step_name.output_name
        - $steps.parent_step.sub_step.output_key
        - $steps.parent_step.sub_step.nested.key

        Args:
            ref: Reference string (e.g., "$steps.load_companies.companies")

        Returns:
            Step output value

        Raises:
            ValueError: If step or output not found
        """
        parts = ref.removeprefix("$steps.").split(".")
        if len(parts) < 2:
            raise ValueError(
                f"Invalid step reference: {ref}. "
                "Expected format: $steps.step_name.output_name[.nested.path]"
            )

        step_name = parts[0]
        path = parts[1:]

        if step_name not in self.steps:
            raise ValueError(
                f"Unknown step reference: {step_name}. "
                f"Available steps: {list(self.steps.keys())}"
            )

        # Navigate through the nested path
        current = self.steps[step_name]
        for i, key in enumerate(path):
            if isinstance(current, dict):
                if key not in current:
                    available = (
                        list(current.keys()) if isinstance(current, dict) else []
                    )
                    raise ValueError(
                        f"Unknown output '{key}' in step '{step_name}'. "
                        f"Available outputs: {available}"
                    )
                current = current[key]
            else:
                raise ValueError(
                    f"Cannot access '{key}' on non-dict value at path: "
                    f"$steps.{step_name}.{'.'.join(path[:i])}"
                )

        return current

    def set_step_outputs(self, step_name: str, outputs: dict[str, Any]) -> None:
        """Store outputs from a completed step.

        Args:
            step_name: Name of the step that completed
            outputs: Dictionary of output values from the step

        Example:
            >>> ctx = ExecutionContext(params={})
            >>> ctx.set_step_outputs("load_companies", {
            ...     "companies": [{"name": "Apple"}, {"name": "Microsoft"}],
            ...     "count": 2
            ... })
            >>> ctx.steps["load_companies"]["count"]
            2
        """
        self.steps[step_name] = outputs
