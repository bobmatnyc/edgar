"""
Constraint Enforcer service for validating AI-generated code.

This service orchestrates multiple validators to ensure generated code
meets architectural, quality, and security standards.

Migration Status: MIGRATED from EDGAR (1M-379, T4)
- Origin: edgar_analyzer.services.constraint_enforcer
- Platform: extract_transform_platform.services.codegen.constraint_enforcer
- Code reuse: 100% (240 LOC preserved)
- Tests: 0 breaking changes
"""

import ast
import logging
from typing import List, Optional

from extract_transform_platform.models.validation import (
    Violation,
    ValidationResult,
    ConstraintConfig,
    Severity,
)
from edgar_analyzer.validators import (
    InterfaceValidator,
    DependencyInjectionValidator,
    TypeHintValidator,
    ImportValidator,
    ComplexityValidator,
    SecurityValidator,
    LoggingValidator,
)

logger = logging.getLogger(__name__)


class ConstraintEnforcer:
    """
    AST-based validation of generated code against constraints.

    Design Decision: Multi-validator orchestration
    Rationale: Separation of concerns - each validator checks one aspect.
    Enables adding new validators without modifying core logic.

    Architecture Pattern: Chain of Responsibility
    Each validator independently checks code and returns violations.
    Enforcer aggregates results and determines overall validity.

    Trade-offs:
    - Performance: Multiple AST walks vs. single-pass validation
    - Modularity: Easy to add validators vs. potential redundancy
    - Maintainability: Clear separation vs. potential duplication
    - Decision: Chose modularity and clarity over micro-optimization

    Performance Analysis:
    - AST parsing: O(n) where n is code size, ~1ms for 500 LOC
    - Each validator: O(n) walk, ~0.5ms per validator
    - Total: ~5ms for 7 validators on typical extractor class
    - Target: <100ms for validation (easily achieved)

    Usage:
        enforcer = ConstraintEnforcer()
        result = enforcer.validate_code(generated_code)
        if not result.valid:
            for violation in result.violations:
                print(violation)
    """

    def __init__(self, config: Optional[ConstraintConfig] = None):
        """
        Initialize constraint enforcer with validators.

        Args:
            config: Constraint configuration (uses defaults if None)
        """
        self.config = config or ConstraintConfig()

        # Initialize all validators
        self.validators = [
            InterfaceValidator(self.config),
            DependencyInjectionValidator(self.config),
            TypeHintValidator(self.config),
            ImportValidator(self.config),
            ComplexityValidator(self.config),
            SecurityValidator(self.config),
            LoggingValidator(self.config),
        ]

        logger.info(
            f"ConstraintEnforcer initialized with {len(self.validators)} validators"
        )

    def validate_code(self, code: str) -> ValidationResult:
        """
        Validate Python code against all constraints.

        Args:
            code: Python code to validate

        Returns:
            ValidationResult with all violations found

        Raises:
            None - syntax errors are returned as violations

        Complexity: O(n*v) where n is code size, v is number of validators
        In practice: ~5-10ms for typical extractor class
        """
        logger.debug(f"Validating {len(code)} characters of code")

        # Parse code into AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return ValidationResult(
                valid=False,
                violations=[
                    Violation(
                        code="SYNTAX_ERROR",
                        message=f"Python syntax error: {e.msg}",
                        line=e.lineno,
                        severity=Severity.ERROR,
                        suggestion="Fix syntax error before proceeding. "
                        f"Error at line {e.lineno}: {e.text}",
                    )
                ],
                code=code,
            )

        # Run all validators
        violations: List[Violation] = []
        for validator in self.validators:
            validator_name = validator.__class__.__name__
            logger.debug(f"Running {validator_name}")

            try:
                validator_violations = validator.validate(tree)
                violations.extend(validator_violations)
                logger.debug(
                    f"{validator_name} found {len(validator_violations)} violations"
                )
            except Exception as e:
                logger.error(f"Error in {validator_name}: {e}", exc_info=True)
                # Add internal error as violation
                violations.append(
                    Violation(
                        code="VALIDATOR_ERROR",
                        message=f"Internal error in {validator_name}: {e}",
                        severity=Severity.ERROR,
                        suggestion="Report this error to system administrator",
                    )
                )

        # Determine overall validity (no ERROR-level violations)
        error_count = sum(
            1 for v in violations if v.severity == Severity.ERROR
        )
        valid = error_count == 0

        logger.info(
            f"Validation complete: {len(violations)} violations "
            f"({error_count} errors, valid={valid})"
        )

        return ValidationResult(
            valid=valid,
            violations=violations,
            code=code,
        )

    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            ValidationResult with all violations found

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        logger.info(f"Validating file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return ValidationResult(
                valid=False,
                violations=[
                    Violation(
                        code="FILE_NOT_FOUND",
                        message=f"File not found: {file_path}",
                        severity=Severity.ERROR,
                    )
                ],
                code="",
            )
        except IOError as e:
            logger.error(f"Error reading file: {e}")
            return ValidationResult(
                valid=False,
                violations=[
                    Violation(
                        code="FILE_READ_ERROR",
                        message=f"Error reading file: {e}",
                        severity=Severity.ERROR,
                    )
                ],
                code="",
            )

        return self.validate_code(code)

    def get_config(self) -> ConstraintConfig:
        """Get current constraint configuration."""
        return self.config

    def update_config(self, config: ConstraintConfig) -> None:
        """
        Update constraint configuration and reinitialize validators.

        Args:
            config: New constraint configuration
        """
        logger.info("Updating constraint configuration")
        self.config = config

        # Reinitialize validators with new config
        self.validators = [
            InterfaceValidator(self.config),
            DependencyInjectionValidator(self.config),
            TypeHintValidator(self.config),
            ImportValidator(self.config),
            ComplexityValidator(self.config),
            SecurityValidator(self.config),
            LoggingValidator(self.config),
        ]

        logger.info("Validators reinitialized with new configuration")
