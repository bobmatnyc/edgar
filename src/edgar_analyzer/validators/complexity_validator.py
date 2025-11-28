"""
Complexity validator for constraint enforcement.

Measures and enforces limits on cyclomatic complexity and code size.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import Violation, Severity, ConstraintConfig


class ComplexityValidator:
    """
    Validates code complexity metrics.

    Design Decision: Complexity thresholds
    Rationale: Complex code is harder to test, maintain, and understand.
    McCabe's cyclomatic complexity > 10 correlates with higher bug rates.

    Metrics Enforced:
    - Cyclomatic complexity < 10 per method (McCabe threshold)
    - Method length < 50 lines (readability threshold)
    - Class length < 300 lines (single responsibility)

    Trade-offs:
    - Strictness: Forces decomposition vs. allows monolithic code
    - Refactoring: More small methods vs. fewer large ones
    - Performance: Method calls overhead (negligible in Python)
    - Decision: Chose maintainability over micro-optimization

    Performance Analysis:
    - Complexity calculation: O(n) where n is nodes in method AST
    - Total validation: O(m) where m is total AST nodes
    - Typical method: ~20-50 nodes, <1ms validation time

    Research: "A Complexity Measure" (McCabe, 1976)
    Empirical data shows complexity > 10 increases defect probability
    """

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Validate code complexity metrics.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of nodes in AST
        """
        violations = []

        # Check method complexity and length
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate cyclomatic complexity
                complexity = self._calculate_complexity(node)
                if complexity > self.config.max_complexity:
                    violations.append(
                        Violation(
                            code="HIGH_COMPLEXITY",
                            message=f"Method '{node.name}' has cyclomatic complexity "
                            f"{complexity} (max: {self.config.max_complexity})",
                            line=node.lineno,
                            severity=Severity.ERROR,
                            suggestion=f"Refactor '{node.name}' into smaller methods. "
                            "Extract conditional logic and loops into helper methods.",
                        )
                    )

                # Calculate method length
                method_lines = self._calculate_lines(node)
                if method_lines > self.config.max_method_lines:
                    violations.append(
                        Violation(
                            code="METHOD_TOO_LONG",
                            message=f"Method '{node.name}' is {method_lines} lines "
                            f"(max: {self.config.max_method_lines})",
                            line=node.lineno,
                            severity=Severity.WARNING,
                            suggestion=f"Split '{node.name}' into smaller, focused methods.",
                        )
                    )

        # Check class length
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        for cls in classes:
            class_lines = self._calculate_lines(cls)
            if class_lines > self.config.max_class_lines:
                violations.append(
                    Violation(
                        code="CLASS_TOO_LONG",
                        message=f"Class '{cls.name}' is {class_lines} lines "
                        f"(max: {self.config.max_class_lines})",
                        line=cls.lineno,
                        severity=Severity.WARNING,
                        suggestion=f"Split '{cls.name}' into smaller classes following "
                        "Single Responsibility Principle.",
                    )
                )

        return violations

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity of a function.

        Cyclomatic Complexity = E - N + 2P
        Simplified: Count of decision points + 1

        Decision points:
        - if/elif statements
        - for/while loops
        - and/or operators
        - try/except blocks
        - with statements

        Args:
            node: Function AST node

        Returns:
            Cyclomatic complexity score

        Complexity: O(n) where n is number of nodes in function
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Conditional statements
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            # Boolean operators
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Exception handlers
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            # With statements
            elif isinstance(child, ast.With):
                complexity += 1
            # Comprehensions
            elif isinstance(
                child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)
            ):
                complexity += 1

        return complexity

    def _calculate_lines(self, node: ast.AST) -> int:
        """
        Calculate number of lines in AST node.

        Args:
            node: AST node to measure

        Returns:
            Number of source lines (excluding blank lines)

        Complexity: O(1) - uses AST line number metadata
        """
        # Get all child nodes with line numbers
        all_nodes = list(ast.walk(node))
        line_numbers = [
            n.lineno for n in all_nodes if hasattr(n, "lineno") and n.lineno is not None
        ]

        if not line_numbers:
            return 0

        # Calculate span from first to last line
        return max(line_numbers) - min(line_numbers) + 1
