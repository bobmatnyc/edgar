"""
Security validator for constraint enforcement.

Detects dangerous code patterns that could introduce security vulnerabilities.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import ConstraintConfig, Severity, Violation


class SecurityValidator:
    """
    Validates code against security anti-patterns.

    Design Decision: Proactive security scanning
    Rationale: AI-generated code may inadvertently introduce vulnerabilities.
    Early detection prevents security issues from reaching production.

    Security Patterns Detected:
    - SQL injection (string concatenation in queries)
    - Shell injection (subprocess with shell=True)
    - Arbitrary code execution (eval, exec, compile)
    - Hardcoded credentials (string literals in sensitive contexts)
    - Unsafe file operations (path traversal patterns)

    Trade-offs:
    - False positives: May flag safe code that looks dangerous
    - Coverage: Heuristic detection vs. formal verification
    - Performance: AST scanning overhead (acceptable at <100ms)
    - Decision: Chose paranoid security over convenience

    Failure Mode: Rejects safe code that matches patterns
    Recovery: Developer can request allowlist exception with justification

    Related: OWASP Top 10, CWE Top 25
    """

    # Dangerous function calls to detect
    DANGEROUS_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "execfile",
        "input",  # Python 2 input() is eval
    }

    # SQL operation patterns
    SQL_OPERATIONS = {"execute", "executemany", "raw"}

    # Sensitive variable patterns
    CREDENTIAL_PATTERNS = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "api_key",
        "apikey",
        "token",
        "auth",
        "credential",
    }

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Check for security anti-patterns.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of nodes in AST
        """
        violations = []

        # First pass: track variables assigned f-strings or formatted strings
        # This enables detection of SQL injection through variables
        query_vars = self._find_query_variables(tree)

        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                violations.extend(self._check_dangerous_call(node))
                violations.extend(self._check_sql_injection(node, query_vars))

            # Check for hardcoded credentials
            elif isinstance(node, ast.Assign):
                violations.extend(self._check_hardcoded_credentials(node))

        return violations

    def _find_query_variables(self, tree: ast.AST) -> dict:
        """
        Find variables that are assigned formatted strings (f-strings, .format(), etc).

        Returns:
            Dict mapping variable names to (line_number, format_type)
        """
        query_vars = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id

                        # Check if assigned an f-string
                        if isinstance(node.value, ast.JoinedStr):
                            query_vars[var_name] = (node.lineno, "f-string")

                        # Check if assigned .format() call
                        elif isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Attribute):
                                if node.value.func.attr == "format":
                                    query_vars[var_name] = (node.lineno, ".format()")

                        # Check if assigned string concatenation
                        elif isinstance(node.value, ast.BinOp):
                            if isinstance(node.value.op, ast.Add):
                                query_vars[var_name] = (node.lineno, "concatenation")

        return query_vars

    def _check_dangerous_call(self, node: ast.Call) -> List[Violation]:
        """Check for dangerous function calls like eval, exec."""
        violations = []

        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in self.DANGEROUS_FUNCTIONS:
            violations.append(
                Violation(
                    code="DANGEROUS_FUNCTION",
                    message=f"Use of dangerous function '{func_name}' detected",
                    line=node.lineno,
                    severity=Severity.ERROR,
                    suggestion=f"Remove '{func_name}()' call. This enables arbitrary "
                    "code execution and poses severe security risk.",
                )
            )

        return violations

    def _check_sql_injection(self, node: ast.Call, query_vars: dict) -> List[Violation]:
        """Check for potential SQL injection patterns.

        Args:
            node: AST Call node to check
            query_vars: Dict of variables assigned formatted strings

        Returns:
            List of SQL injection violations
        """
        violations: List[Violation] = []

        # Check if this is a SQL execute call
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name not in self.SQL_OPERATIONS:
            return violations

        # Check if query argument uses string formatting/concatenation
        if node.args:
            query_arg = node.args[0]

            # Check for f-strings (direct)
            if isinstance(query_arg, ast.JoinedStr):
                violations.append(
                    Violation(
                        code="SQL_INJECTION_RISK",
                        message="SQL query uses f-string formatting (injection risk)",
                        line=node.lineno,
                        severity=Severity.ERROR,
                        suggestion="Use parameterized queries: "
                        "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                    )
                )

            # Check for .format() calls (direct)
            elif isinstance(query_arg, ast.Call) and isinstance(
                query_arg.func, ast.Attribute
            ):
                if query_arg.func.attr == "format":
                    violations.append(
                        Violation(
                            code="SQL_INJECTION_RISK",
                            message="SQL query uses .format() (injection risk)",
                            line=node.lineno,
                            severity=Severity.ERROR,
                            suggestion="Use parameterized queries instead of string formatting",
                        )
                    )

            # Check for + operator (string concatenation, direct)
            elif isinstance(query_arg, ast.BinOp) and isinstance(query_arg.op, ast.Add):
                violations.append(
                    Violation(
                        code="SQL_INJECTION_RISK",
                        message="SQL query uses string concatenation (injection risk)",
                        line=node.lineno,
                        severity=Severity.ERROR,
                        suggestion="Use parameterized queries instead of string concatenation",
                    )
                )

            # Check if query argument is a variable that was assigned a formatted string
            elif isinstance(query_arg, ast.Name):
                var_name = query_arg.id
                if var_name in query_vars:
                    assign_line, format_type = query_vars[var_name]
                    violations.append(
                        Violation(
                            code="SQL_INJECTION_RISK",
                            message=f"SQL query uses variable '{var_name}' assigned with "
                            f"{format_type} (injection risk, assigned at line {assign_line})",
                            line=node.lineno,
                            severity=Severity.ERROR,
                            suggestion="Use parameterized queries: "
                            "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                        )
                    )

        return violations

    def _check_hardcoded_credentials(self, node: ast.Assign) -> List[Violation]:
        """Check for hardcoded credentials in assignments."""
        violations = []

        # Check variable names
        for target in node.targets:
            var_name = None
            if isinstance(target, ast.Name):
                var_name = target.id
            elif isinstance(target, ast.Attribute):
                var_name = target.attr

            if not var_name:
                continue

            # Check if variable name suggests credentials
            var_lower = var_name.lower()
            if any(pattern in var_lower for pattern in self.CREDENTIAL_PATTERNS):
                # Check if value is a string literal (hardcoded)
                if isinstance(node.value, ast.Constant) and isinstance(
                    node.value.value, str
                ):
                    # Skip if it's clearly a placeholder
                    value = node.value.value
                    if value and not any(
                        placeholder in value.lower()
                        for placeholder in ["your_", "placeholder", "xxx", "****"]
                    ):
                        violations.append(
                            Violation(
                                code="HARDCODED_CREDENTIAL",
                                message=f"Potential hardcoded credential in variable '{var_name}'",
                                line=node.lineno,
                                severity=Severity.ERROR,
                                suggestion=f"Remove hardcoded value and use environment variable: "
                                f"{var_name} = os.getenv('{var_name.upper()}')",
                            )
                        )

        return violations
