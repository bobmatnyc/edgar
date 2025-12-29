"""
Logging validator for constraint enforcement.

Ensures code uses structured logging instead of print statements.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import ConstraintConfig, Severity, Violation


class LoggingValidator:
    """
    Validates logging practices.

    Design Decision: Structured logging mandatory
    Rationale: Production systems require proper logging for debugging and monitoring.
    print() statements don't support log levels, formatting, or centralized collection.

    Logging Requirements:
    - Use logger.info(), logger.error(), logger.debug() instead of print()
    - Log all API calls (info level)
    - Log all error conditions (error level)
    - Log all state transitions (debug level)

    Trade-offs:
    - Verbosity: More setup vs. simple print()
    - Performance: Logging overhead (~1-10μs per call, negligible)
    - Production readiness: Structured logs vs. debugging convenience
    - Decision: Chose production-ready logging

    Performance:
    - logger.info(): ~2-5μs overhead
    - print(): ~1-3μs overhead
    - Difference negligible except in tight loops (avoid logging there)

    Optimization Note: For performance-critical sections, use:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(expensive_operation())
    """

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Validate logging practices.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of nodes in AST
        """
        violations = []

        # Check for print() statements
        if not self.config.allow_print_statements:
            violations.extend(self._check_print_statements(tree))

        # Check for proper logging usage
        violations.extend(self._check_logging_usage(tree))

        return violations

    def _check_print_statements(self, tree: ast.AST) -> List[Violation]:
        """Check for print() statements in production code."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id

                if func_name == "print":
                    violations.append(
                        Violation(
                            code="PRINT_STATEMENT",
                            message="Use of print() instead of structured logging",
                            line=node.lineno,
                            severity=Severity.ERROR,
                            suggestion="Replace print() with logger.info() or logger.debug(). "
                            "Import: from logging import getLogger; logger = getLogger(__name__)",
                        )
                    )

        return violations

    def _check_logging_usage(self, tree: ast.AST) -> List[Violation]:
        """Check that API calls and errors are logged."""
        violations = []

        # Find methods that should have logging
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            # Skip private methods and special methods
            if node.name.startswith("_"):
                continue

            # Check if method has any logging calls
            has_logging = self._has_logging_calls(node)

            # Check if method makes API calls
            has_api_calls = self._has_api_calls(node)

            # Check if method has error handling
            has_error_handling = self._has_error_handling(node)

            # Warn if API calls without logging
            if has_api_calls and not has_logging:
                violations.append(
                    Violation(
                        code="MISSING_API_LOGGING",
                        message=f"Method '{node.name}' makes API calls but has no logging",
                        line=node.lineno,
                        severity=Severity.WARNING,
                        suggestion=f"Add logging to '{node.name}': "
                        "logger.info('Making API call to...')",
                    )
                )

            # Warn if error handling without logging
            if has_error_handling and not has_logging:
                violations.append(
                    Violation(
                        code="MISSING_ERROR_LOGGING",
                        message=f"Method '{node.name}' has error handling but no logging",
                        line=node.lineno,
                        severity=Severity.WARNING,
                        suggestion=f"Add error logging in '{node.name}': "
                        "logger.error('Error occurred: %s', e)",
                    )
                )

        return violations

    def _has_logging_calls(self, node: ast.FunctionDef) -> bool:
        """Check if function has logging calls."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                # Check for logger.info(), logger.error(), etc.
                if child.func.attr in (
                    "debug",
                    "info",
                    "warning",
                    "error",
                    "critical",
                ):
                    return True
        return False

    def _has_api_calls(self, node: ast.FunctionDef) -> bool:
        """Check if function makes HTTP/API calls."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Check for common HTTP client methods
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in (
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                        "request",
                    ):
                        return True

                # Check for function names suggesting API calls
                if isinstance(child.func, ast.Name):
                    name = child.func.id.lower()
                    if "request" in name or "fetch" in name or "call" in name:
                        return True

        return False

    def _has_error_handling(self, node: ast.FunctionDef) -> bool:
        """Check if function has try/except blocks."""
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return True
        return False
