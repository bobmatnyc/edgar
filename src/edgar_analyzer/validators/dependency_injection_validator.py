"""
Dependency injection validator for constraint enforcement.

Ensures that __init__ methods use the @inject decorator for DI container.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import ConstraintConfig, Severity, Violation


class DependencyInjectionValidator:
    """
    Validates dependency injection patterns.

    Design Decision: Mandatory @inject decorator
    Rationale: Dependency injection enables testability and loose coupling.
    The @inject decorator integrates with dependency-injector container.

    Trade-offs:
    - Boilerplate: Requires decorator on all __init__ methods
    - Flexibility: Container management vs. manual instantiation
    - Testing: Mock injection vs. complex setup
    - Decision: Chose DI for scalability and testability
    """

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Validate that __init__ methods have @inject decorator.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of nodes in AST
        """
        violations = []

        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        for cls in classes:
            # Only check extractor classes
            if not cls.name.endswith("Extractor"):
                continue

            # Find __init__ method
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef):
                    continue

                method_name = method.name

                # Check if this method requires decorators
                if method_name not in self.config.required_decorators:
                    continue

                required_decorators = self.config.required_decorators[method_name]

                # Get existing decorators
                existing_decorators = []
                for decorator in method.decorator_list:
                    if isinstance(decorator, ast.Name):
                        existing_decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Call) and isinstance(
                        decorator.func, ast.Name
                    ):
                        existing_decorators.append(decorator.func.id)

                # Check for missing required decorators
                for required in required_decorators:
                    if required not in existing_decorators:
                        violations.append(
                            Violation(
                                code="MISSING_DECORATOR",
                                message=f"{cls.name}.{method_name} must have @{required} decorator",
                                line=method.lineno,
                                severity=Severity.ERROR,
                                suggestion=f"Add decorator: @{required}",
                            )
                        )

        return violations
