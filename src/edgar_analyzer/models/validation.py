"""
Validation models for constraint enforcement.

This module defines the data structures used to represent validation results
and constraint violations in the Constraint Enforcer system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(Enum):
    """Severity level of a constraint violation."""

    ERROR = "error"  # Must be fixed - blocking
    WARNING = "warning"  # Should be fixed - non-blocking
    INFO = "info"  # Informational - best practice


@dataclass
class Violation:
    """
    Represents a single constraint violation.

    Design Decision: Structured violation reporting
    Rationale: Line numbers and severity enable actionable feedback to AI.
    Each violation includes context for automated fixing.

    Attributes:
        code: Unique violation code (e.g., 'MISSING_INTERFACE')
        message: Human-readable description of the violation
        line: Line number where violation occurs (None for file-level)
        severity: Severity level (ERROR, WARNING, INFO)
        suggestion: Optional fix suggestion for the AI
    """

    code: str
    message: str
    line: Optional[int] = None
    severity: Severity = Severity.ERROR
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format violation for display."""
        location = f"line {self.line}" if self.line else "file-level"
        severity_marker = {
            Severity.ERROR: "❌",
            Severity.WARNING: "⚠️",
            Severity.INFO: "ℹ️",
        }[self.severity]

        base = f"{severity_marker} [{self.code}] {self.message} ({location})"
        if self.suggestion:
            base += f"\n   Suggestion: {self.suggestion}"
        return base


@dataclass
class ValidationResult:
    """
    Complete validation result for a code snippet.

    Design Decision: Aggregate validation results
    Rationale: Single result object simplifies error handling and reporting.
    Groups violations by severity for prioritized fixing.

    Attributes:
        valid: True if no ERROR-level violations found
        violations: List of all violations found
        code: The code that was validated
        warnings_count: Count of WARNING-level violations
        errors_count: Count of ERROR-level violations
    """

    valid: bool
    violations: List[Violation] = field(default_factory=list)
    code: str = ""

    @property
    def errors_count(self) -> int:
        """Count of ERROR-level violations."""
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)

    @property
    def warnings_count(self) -> int:
        """Count of WARNING-level violations."""
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of INFO-level violations."""
        return sum(1 for v in self.violations if v.severity == Severity.INFO)

    def get_violations_by_severity(self, severity: Severity) -> List[Violation]:
        """Get all violations of a specific severity level."""
        return [v for v in self.violations if v.severity == severity]

    def __str__(self) -> str:
        """Format validation result for display."""
        if self.valid:
            return "✅ Code passes all constraints"

        lines = [
            f"❌ Validation failed: {self.errors_count} errors, "
            f"{self.warnings_count} warnings, {self.info_count} info"
        ]

        # Group by severity
        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            severity_violations = self.get_violations_by_severity(severity)
            if severity_violations:
                lines.append(f"\n{severity.value.upper()}S:")
                for violation in severity_violations:
                    lines.append(f"  {violation}")

        return "\n".join(lines)


@dataclass
class ConstraintConfig:
    """
    Configuration for constraint enforcement rules.

    Design Decision: Configurable constraints
    Rationale: Different projects may have different thresholds.
    Allows tuning without code changes.

    Attributes:
        max_complexity: Maximum cyclomatic complexity per method
        max_method_lines: Maximum lines per method
        max_class_lines: Maximum lines per class
        forbidden_imports: Set of forbidden module names
        required_decorators: Decorators required on specific methods
        enforce_type_hints: Whether to require type hints
        enforce_docstrings: Whether to require docstrings
    """

    max_complexity: int = 10
    max_method_lines: int = 50
    max_class_lines: int = 300
    forbidden_imports: set = field(
        default_factory=lambda: {
            "os",
            "subprocess",
            "eval",
            "exec",
            "compile",
            "__import__",
        }
    )
    required_decorators: dict = field(
        default_factory=lambda: {"__init__": ["inject"]}
    )
    enforce_type_hints: bool = True
    enforce_docstrings: bool = True
    enforce_interface: bool = True
    allow_print_statements: bool = False

    @classmethod
    def from_dict(cls, config: dict) -> "ConstraintConfig":
        """Create config from dictionary (e.g., loaded from YAML)."""
        return cls(
            max_complexity=config.get("max_complexity", 10),
            max_method_lines=config.get("max_method_lines", 50),
            max_class_lines=config.get("max_class_lines", 300),
            forbidden_imports=set(
                config.get(
                    "forbidden_imports",
                    ["os", "subprocess", "eval", "exec", "compile", "__import__"],
                )
            ),
            required_decorators=config.get("required_decorators", {"__init__": ["inject"]}),
            enforce_type_hints=config.get("enforce_type_hints", True),
            enforce_docstrings=config.get("enforce_docstrings", True),
            enforce_interface=config.get("enforce_interface", True),
            allow_print_statements=config.get("allow_print_statements", False),
        )
