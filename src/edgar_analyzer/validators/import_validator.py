"""
Import validator for constraint enforcement.

Checks for forbidden imports that could pose security risks or violate architecture.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import Violation, Severity, ConstraintConfig


class ImportValidator:
    """
    Validates import statements against forbidden modules.

    Design Decision: Forbidden imports list
    Rationale: Prevent security vulnerabilities and enforce architecture boundaries.
    Modules like 'os', 'subprocess' allow arbitrary code execution.

    Security Constraints:
    - No shell command execution (subprocess, os.system)
    - No dynamic code execution (eval, exec, compile)
    - No filesystem access outside allowed paths (os module)
    - No arbitrary module loading (__import__)

    Trade-offs:
    - Security: Restricted functionality vs. complete access
    - Flexibility: AI creativity vs. safety guarantees
    - Decision: Chose security for production-safe code generation

    Related: OWASP Top 10 - Injection vulnerabilities
    """

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Check for forbidden imports.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of import statements
        """
        violations = []

        for node in ast.walk(tree):
            # Check regular imports: import os
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.config.forbidden_imports:
                        violations.append(
                            Violation(
                                code="FORBIDDEN_IMPORT",
                                message=f"Import of '{alias.name}' is not allowed (security risk)",
                                line=node.lineno,
                                severity=Severity.ERROR,
                                suggestion=f"Remove 'import {alias.name}'. "
                                "Use safer alternatives or request allowlist update.",
                            )
                        )

            # Check from imports: from os import system
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.config.forbidden_imports:
                    violations.append(
                        Violation(
                            code="FORBIDDEN_IMPORT",
                            message=f"Import from '{node.module}' is not allowed (security risk)",
                            line=node.lineno,
                            severity=Severity.ERROR,
                            suggestion=f"Remove 'from {node.module} import ...'. "
                            "Use safer alternatives or request allowlist update.",
                        )
                    )

                # Also check for forbidden submodules
                if node.module:
                    base_module = node.module.split(".")[0]
                    if base_module in self.config.forbidden_imports:
                        violations.append(
                            Violation(
                                code="FORBIDDEN_IMPORT",
                                message=f"Import from '{node.module}' (base: {base_module}) "
                                "is not allowed (security risk)",
                                line=node.lineno,
                                severity=Severity.ERROR,
                                suggestion=f"Remove 'from {node.module} import ...'. "
                                "Use safer alternatives.",
                            )
                        )

        return violations
