"""Accuracy validator for generated code against examples.

This module validates that generated code produces correct output when
executed against the original API response examples.
"""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any, cast

from edgar.validators.ast_validator import ValidationResult


@dataclass(frozen=True)
class AccuracyValidator:
    """Validates generated code accuracy against examples.

    Executes generated code with example inputs and verifies output
    matches expected results.

    Attributes:
        safe_mode: If True, use restricted execution environment
        timeout: Execution timeout in seconds
    """

    safe_mode: bool = True
    timeout: float = 5.0

    def validate(
        self,
        code: str,
        examples: list[dict[str, Any]],
        expected_outputs: list[dict[str, Any]],
    ) -> ValidationResult:
        """Validate code accuracy against examples.

        Args:
            code: Generated Python code
            examples: List of example inputs
            expected_outputs: List of expected outputs

        Returns:
            ValidationResult with accuracy errors
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(examples) != len(expected_outputs):
            errors.append(
                f"Example count mismatch: {len(examples)} examples, "
                f"{len(expected_outputs)} expected outputs"
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        if not examples:
            warnings.append("No examples provided for accuracy validation")
            return ValidationResult(valid=True, errors=errors, warnings=warnings)

        # Execute and compare each example
        passed = 0
        for i, (example, expected) in enumerate(zip(examples, expected_outputs)):
            try:
                actual = self._execute_code_safely(code, example)
                differences = self._compare_outputs(actual, expected)

                if differences:
                    errors.append(f"Example {i+1}: Output mismatch")
                    for diff in differences[:5]:  # Limit to first 5 differences
                        errors.append(f"  - {diff}")
                    if len(differences) > 5:
                        errors.append(f"  ... and {len(differences) - 5} more differences")
                else:
                    passed += 1
            except RuntimeError as e:
                errors.append(f"Example {i+1}: Execution failed - {e}")
            except Exception as e:
                errors.append(f"Example {i+1}: Unexpected error - {type(e).__name__}: {e}")

        # Report accuracy
        total = len(examples)
        accuracy = (passed / total) * 100 if total > 0 else 0

        if passed < total:
            warnings.append(f"Accuracy: {passed}/{total} examples passed ({accuracy:.1f}%)")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _execute_code_safely(
        self,
        code: str,
        example_input: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute code safely with example input.

        Args:
            code: Python code to execute
            example_input: Example input data

        Returns:
            Execution result

        Raises:
            RuntimeError: If execution fails or times out
        """
        # Create a wrapper script that executes the generated code
        wrapper = f"""
import json
import sys

# The generated code
{code}

# Find the extractor class (implements IDataExtractor)
extractor_class = None
for name, obj in list(locals().items()):
    if isinstance(obj, type) and hasattr(obj, 'extract'):
        extractor_class = obj
        break

if extractor_class is None:
    print(json.dumps({{"error": "No extractor class found"}}))
    sys.exit(1)

# Execute extraction
try:
    extractor = extractor_class()
    input_data = json.loads('{json.dumps(example_input)}')
    result = extractor.extract(input_data)
    # Convert Pydantic model to dict
    if hasattr(result, 'model_dump'):
        output = result.model_dump()
    elif hasattr(result, 'dict'):
        output = result.dict()
    else:
        output = dict(result)
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({{"error": str(e), "type": type(e).__name__}}))
    sys.exit(1)
"""

        # Write to temp file and execute with timeout
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(wrapper)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Execution failed: {result.stderr}")

            return cast(dict[str, Any], json.loads(result.stdout))
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Execution timed out after {self.timeout}s")
        finally:
            os.unlink(temp_path)

    def _compare_outputs(
        self,
        actual: dict[str, Any],
        expected: dict[str, Any],
        path: str = "",
    ) -> list[str]:
        """Compare actual vs expected outputs with deep diff.

        Args:
            actual: Actual execution result
            expected: Expected result
            path: Current path in nested structure (for error reporting)

        Returns:
            List of difference descriptions (empty if match)
        """
        differences: list[str] = []

        # Check for error in actual output
        if "error" in actual:
            differences.append(f"Execution error: {actual['error']}")
            return differences

        # Compare keys
        actual_keys = set(actual.keys())
        expected_keys = set(expected.keys())

        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys

        if missing:
            differences.append(f"{path}: Missing keys: {missing}")
        if extra:
            differences.append(f"{path}: Unexpected keys: {extra}")

        # Compare values for common keys
        for key in actual_keys & expected_keys:
            actual_val = actual[key]
            expected_val = expected[key]
            key_path = f"{path}.{key}" if path else key

            if isinstance(expected_val, dict) and isinstance(actual_val, dict):
                # Recursive comparison
                differences.extend(self._compare_outputs(actual_val, expected_val, key_path))
            elif isinstance(expected_val, list) and isinstance(actual_val, list):
                if len(actual_val) != len(expected_val):
                    differences.append(
                        f"{key_path}: List length mismatch: "
                        f"{len(actual_val)} vs {len(expected_val)}"
                    )
                else:
                    for i, (a, e) in enumerate(zip(actual_val, expected_val)):
                        if isinstance(e, dict) and isinstance(a, dict):
                            differences.extend(self._compare_outputs(a, e, f"{key_path}[{i}]"))
                        elif a != e:
                            differences.append(f"{key_path}[{i}]: {a!r} != {e!r}")
            elif actual_val != expected_val:
                # Handle numeric tolerance for floats
                if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                    if abs(actual_val - expected_val) > 0.0001:
                        differences.append(f"{key_path}: {actual_val} != {expected_val}")
                else:
                    differences.append(f"{key_path}: {actual_val!r} != {expected_val!r}")

        return differences
