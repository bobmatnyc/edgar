"""Architecture constraint validator for generated code.

This module validates that generated code follows required architecture
patterns including interfaces, dependency injection, and type safety.
"""

import ast
from dataclasses import dataclass
from typing import Any

from edgar.validators.ast_validator import ValidationResult


@dataclass(frozen=True)
class ConstraintValidator:
    """Validates architecture constraints in generated code.

    Checks for:
    - Interface implementation (IDataSource, IDataExtractor)
    - Dependency injection patterns (frozen dataclasses)
    - Type hint coverage (all functions typed)
    - Pydantic model usage
    - Exception handling patterns
    """

    required_interfaces: list[str] = None  # type: ignore

    def __post_init__(self) -> None:
        """Initialize default required interfaces."""
        if self.required_interfaces is None:
            object.__setattr__(
                self,
                "required_interfaces",
                ["IDataSource", "IDataExtractor"],
            )

    def validate(
        self,
        code: str,
        constraints: dict[str, Any],
    ) -> ValidationResult:
        """Validate architecture constraints in code.

        Args:
            code: Python code to validate
            constraints: Dictionary of constraint requirements

        Returns:
            ValidationResult with errors and warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            errors.append("Cannot validate constraints: invalid syntax")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Validate interface implementation
        self._validate_interfaces(tree, errors, warnings)

        # Validate dependency injection
        self._validate_dependency_injection(tree, errors, warnings)

        # Validate type hints
        self._validate_type_hints(tree, errors, warnings)

        # Validate Pydantic models
        self._validate_pydantic_usage(tree, errors, warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_interfaces(
        self,
        tree: ast.AST,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate required interface implementations.

        Checks that code implements required interfaces (IDataSource, IDataExtractor):
        - IDataSource: async def fetch(self) -> dict[str, Any]
        - IDataExtractor: def extract(self, raw_data: dict[str, Any]) -> BaseModel

        Adds errors if required interfaces are not implemented.
        Adds warnings if method signatures don't match exactly.
        """
        # Expected interface method signatures
        interface_specs = {
            "IDataSource": {
                "fetch": {
                    "is_async": True,
                    "params": [],  # Only self
                    "return_annotation": "dict[str, Any]",
                }
            },
            "IDataExtractor": {
                "extract": {
                    "is_async": False,
                    "params": ["raw_data"],  # Parameter names
                    "return_annotation": "BaseModel",
                }
            },
        }

        # Track which interfaces are implemented
        implemented_interfaces: dict[str, bool] = {
            iface: False for iface in self.required_interfaces
        }

        # Collect all class definitions
        class_visitor = InterfaceVisitor()
        class_visitor.visit(tree)

        for class_def in class_visitor.classes:
            # Check if class inherits from any required interface
            for base in class_def.bases:
                base_name = self._get_name(base)
                if base_name in self.required_interfaces:
                    implemented_interfaces[base_name] = True

                    # Validate method signatures for this interface
                    if base_name in interface_specs:
                        self._validate_interface_methods(
                            class_def,
                            base_name,
                            interface_specs[base_name],
                            warnings,
                        )

        # Report missing interfaces
        for iface, is_implemented in implemented_interfaces.items():
            if not is_implemented:
                errors.append(f"Missing required interface implementation: {iface}")

    def _validate_dependency_injection(
        self,
        tree: ast.AST,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate dependency injection patterns.

        Checks for:
        - Classes should be frozen dataclasses (@dataclass(frozen=True))
        - Constructor should accept dependencies (dataclass fields)
        - No hardcoded configuration (string literals for URLs, API keys)
        - No global mutable state

        Adds errors for DI pattern violations.
        """
        di_visitor = DependencyInjectionVisitor()
        di_visitor.visit(tree)

        # Check for frozen dataclasses
        for class_def in di_visitor.classes_without_frozen_dataclass:
            errors.append(
                f"Class '{class_def.name}' at line {class_def.lineno} "
                f"should use @dataclass(frozen=True) for immutability"
            )

        # Check for hardcoded configuration
        for constant in di_visitor.hardcoded_strings:
            # constant.value should be a string based on our visitor logic
            if isinstance(constant.value, str) and self._looks_like_config(constant.value):
                preview = constant.value[:50] if len(constant.value) > 50 else constant.value
                errors.append(
                    f"Hardcoded configuration at line {constant.lineno}: "
                    f"'{preview}...' - use dependency injection instead"
                )

        # Check for global mutable state
        for assign in di_visitor.global_assignments:
            target_name = self._get_assignment_target_name(assign)
            if target_name and target_name.isupper():
                # Constants are OK (ALL_CAPS naming)
                continue
            errors.append(
                f"Global mutable state at line {assign.lineno}: "
                f"'{target_name}' - use dependency injection instead"
            )

    def _validate_type_hints(
        self,
        tree: ast.AST,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate type hint coverage.

        Ensures 100% type hint coverage:
        - All function parameters must have type annotations (except 'self')
        - All functions must have return type annotations

        Adds errors for missing type hints.
        """
        type_hint_visitor = TypeHintVisitor()
        type_hint_visitor.visit(tree)

        # Check for functions with missing parameter type hints
        for func_def in type_hint_visitor.functions_with_missing_param_hints:
            errors.append(
                f"Function '{func_def.name}' at line {func_def.lineno} "
                f"has parameters without type hints"
            )

        # Check for functions with missing return type hints
        for func_def in type_hint_visitor.functions_with_missing_return_hints:
            errors.append(
                f"Function '{func_def.name}' at line {func_def.lineno} "
                f"missing return type annotation"
            )

    def _validate_pydantic_usage(
        self,
        tree: ast.AST,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate Pydantic model usage.

        Checks:
        - Classes inherit from BaseModel
        - Fields use Field() with descriptions
        - Proper validator usage (field_validator, model_validator)

        Adds warnings for models without descriptions.
        """
        pydantic_visitor = PydanticVisitor()
        pydantic_visitor.visit(tree)

        # Check for Pydantic models without field descriptions
        for class_def in pydantic_visitor.models_without_descriptions:
            warnings.append(
                f"Pydantic model '{class_def.name}' at line {class_def.lineno} "
                f"has fields without Field() descriptions"
            )

        # Check for proper validator decorators
        for func_def in pydantic_visitor.validators_with_incorrect_decorators:
            warnings.append(
                f"Validator '{func_def.name}' at line {func_def.lineno} "
                f"should use @field_validator or @model_validator decorator"
            )

    # Helper methods for validation logic

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def _validate_interface_methods(
        self,
        class_def: ast.ClassDef,
        interface_name: str,
        method_specs: dict[str, dict[str, Any]],
        warnings: list[str],
    ) -> None:
        """Validate that class methods match interface specifications."""
        class_methods = {
            method.name: method
            for method in class_def.body
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        for method_name, spec in method_specs.items():
            if method_name not in class_methods:
                warnings.append(
                    f"Class '{class_def.name}' implements {interface_name} "
                    f"but missing method '{method_name}'"
                )
                continue

            method = class_methods[method_name]

            # Check async/sync
            is_async = isinstance(method, ast.AsyncFunctionDef)
            if is_async != spec["is_async"]:
                expected = "async " if spec["is_async"] else ""
                warnings.append(
                    f"Method '{class_def.name}.{method_name}' at line {method.lineno} "
                    f"should be {expected}def, not {'async ' if is_async else ''}def"
                )

            # Check parameters (skip self)
            params = [arg.arg for arg in method.args.args[1:]]  # Skip self
            expected_params = spec["params"]
            if params != expected_params:
                warnings.append(
                    f"Method '{class_def.name}.{method_name}' at line {method.lineno} "
                    f"has parameters {params}, expected {expected_params}"
                )

    def _looks_like_config(self, value: str) -> bool:
        """Check if string looks like configuration (URL, API key, etc.)."""
        config_indicators = [
            "http://",
            "https://",
            "api_key",
            "secret",
            "password",
            "token",
            "://",
            ".com",
            ".org",
            ".net",
        ]
        lower_value = value.lower()
        return any(indicator in lower_value for indicator in config_indicators)

    def _get_assignment_target_name(self, assign: ast.Assign) -> str | None:
        """Extract variable name from assignment target."""
        if assign.targets and isinstance(assign.targets[0], ast.Name):
            return assign.targets[0].id
        return None


# AST Visitor Classes


class InterfaceVisitor(ast.NodeVisitor):
    """Visitor to collect class definitions for interface validation."""

    def __init__(self) -> None:
        self.classes: list[ast.ClassDef] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and collect it."""
        self.classes.append(node)
        self.generic_visit(node)


class DependencyInjectionVisitor(ast.NodeVisitor):
    """Visitor to check dependency injection patterns."""

    def __init__(self) -> None:
        self.classes_without_frozen_dataclass: list[ast.ClassDef] = []
        self.hardcoded_strings: list[ast.Constant] = []
        self.global_assignments: list[ast.Assign] = []
        self._in_class = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and check for frozen dataclass."""
        self._in_class = True

        # Skip Pydantic models (they don't need frozen dataclass)
        is_pydantic_model = any(self._get_base_name(base) == "BaseModel" for base in node.bases)

        if not is_pydantic_model:
            # Check if class has @dataclass(frozen=True) decorator
            has_frozen_dataclass = False
            for decorator in node.decorator_list:
                if self._is_frozen_dataclass_decorator(decorator):
                    has_frozen_dataclass = True
                    break

            if not has_frozen_dataclass:
                self.classes_without_frozen_dataclass.append(node)

        self.generic_visit(node)
        self._in_class = False

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant and collect string literals."""
        if isinstance(node.value, str) and len(node.value) > 5:
            self.hardcoded_strings.append(node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment and check for global mutable state."""
        if not self._in_class:
            self.global_assignments.append(node)
        self.generic_visit(node)

    def _get_base_name(self, node: ast.AST) -> str:
        """Extract base class name."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def _is_frozen_dataclass_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator is @dataclass(frozen=True)."""
        # Handle @dataclass(frozen=True)
        if isinstance(decorator, ast.Call):
            func_name = ""
            if isinstance(decorator.func, ast.Name):
                func_name = decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                func_name = decorator.func.attr

            if func_name == "dataclass":
                # Check for frozen=True keyword argument
                for keyword in decorator.keywords:
                    if keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant):
                        return keyword.value.value is True

        return False


class TypeHintVisitor(ast.NodeVisitor):
    """Visitor to check type hint coverage."""

    def __init__(self) -> None:
        self.functions_with_missing_param_hints: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self.functions_with_missing_return_hints: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition and check type hints."""
        self._check_function_hints(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition and check type hints."""
        self._check_function_hints(node)
        self.generic_visit(node)

    def _check_function_hints(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check if function has complete type hints."""
        # Check parameter type hints (skip self and cls)
        for i, arg in enumerate(node.args.args):
            if i == 0 and arg.arg in ("self", "cls"):
                continue
            if arg.annotation is None:
                self.functions_with_missing_param_hints.append(node)
                break

        # Check return type hint
        if node.returns is None:
            self.functions_with_missing_return_hints.append(node)


class PydanticVisitor(ast.NodeVisitor):
    """Visitor to check Pydantic model usage."""

    def __init__(self) -> None:
        self.models_without_descriptions: list[ast.ClassDef] = []
        self.validators_with_incorrect_decorators: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self._current_class: ast.ClassDef | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and check Pydantic patterns."""
        self._current_class = node

        # Check if class inherits from BaseModel
        is_pydantic_model = any(self._get_base_name(base) == "BaseModel" for base in node.bases)

        if is_pydantic_model:
            # Check for Field() usage with descriptions
            has_field_without_description = False
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    # Field without value or without Field() call with description
                    if item.value is None:
                        # No default value, definitely no description
                        has_field_without_description = True
                        break
                    elif not self._has_field_with_description(item.value):
                        # Has value but not Field() with description
                        has_field_without_description = True
                        break

            if has_field_without_description:
                self.models_without_descriptions.append(node)

        self.generic_visit(node)
        self._current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition and check validator decorators."""
        if self._current_class and node.name.startswith("validate_"):
            # Check for proper validator decorators
            has_validator_decorator = any(
                self._is_validator_decorator(dec) for dec in node.decorator_list
            )
            if not has_validator_decorator:
                self.validators_with_incorrect_decorators.append(node)

        self.generic_visit(node)

    def _get_base_name(self, node: ast.AST) -> str:
        """Extract base class name."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def _has_field_with_description(self, node: ast.AST) -> bool:
        """Check if node is a Field() call with description."""
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name == "Field":
                # Check for description keyword argument
                return any(kw.arg == "description" for kw in node.keywords)

        return False

    def _is_validator_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator is a Pydantic validator."""
        validator_names = ["field_validator", "model_validator", "validator"]
        if isinstance(decorator, ast.Name):
            return decorator.id in validator_names
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id in validator_names
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in validator_names
        return False
