"""
Type hint validator for constraint enforcement.

Ensures all methods have proper type annotations for parameters and return values.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import ConstraintConfig, Severity, Violation


class TypeHintValidator:
    """
    Validates type hint usage in code.

    Design Decision: Mandatory type hints
    Rationale: Type hints enable static analysis, IDE support, and runtime validation.
    Catches type errors before runtime, improving code reliability.

    Trade-offs:
    - Verbosity: More code vs. better documentation
    - Maintenance: Type updates when signatures change
    - Performance: Minimal runtime cost with modern Python
    - Decision: Chose type safety over brevity

    Performance: mypy with type hints catches 15-20% of bugs at dev time
    (based on Dropbox study of 4M+ lines of Python)
    """

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Validate that all methods have type hints.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of nodes in AST
        """
        if not self.config.enforce_type_hints:
            return []

        violations = []

        # Find all function definitions
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            # Skip private methods (internal implementation)
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue

            # Check argument type hints
            args_without_hints = []
            for i, arg in enumerate(node.args.args):
                # Skip 'self' and 'cls' parameters
                if i == 0 and arg.arg in ("self", "cls"):
                    continue

                if arg.annotation is None:
                    args_without_hints.append(arg.arg)

            if args_without_hints:
                violations.append(
                    Violation(
                        code="MISSING_TYPE_HINT",
                        message=f"Method '{node.name}' has parameters without type hints: "
                        f"{', '.join(args_without_hints)}",
                        line=node.lineno,
                        severity=Severity.ERROR,
                        suggestion="Add type hints to all parameters: "
                        f"def {node.name}(self, {args_without_hints[0]}: <type>):",
                    )
                )

            # Check return type annotation
            if node.returns is None and node.name not in ("__init__", "__post_init__"):
                violations.append(
                    Violation(
                        code="MISSING_RETURN_TYPE",
                        message=f"Method '{node.name}' has no return type annotation",
                        line=node.lineno,
                        severity=Severity.ERROR,
                        suggestion=f"Add return type: def {node.name}(...) -> <ReturnType>:",
                    )
                )

        return violations
