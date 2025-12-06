"""
Interface validator for constraint enforcement.

Ensures that extractor classes implement the IDataExtractor interface.
"""

import ast
from typing import List

from edgar_analyzer.models.validation import ConstraintConfig, Severity, Violation


class InterfaceValidator:
    """
    Validates that classes implement required interfaces.

    Design Decision: Enforce IDataExtractor interface
    Rationale: Interface compliance ensures all extractors have consistent API.
    This enables dynamic loading and uniform handling of all data sources.

    Trade-offs:
    - Strictness: Requires explicit interface implementation vs. duck typing
    - Maintainability: Clear contracts vs. flexibility
    - Decision: Chose strictness for multi-source platform consistency
    """

    def __init__(self, config: ConstraintConfig):
        """Initialize validator with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Validate that extractor classes implement IDataExtractor.

        Args:
            tree: AST of the code to validate

        Returns:
            List of violations found (empty if valid)

        Complexity: O(n) where n is number of nodes in AST
        """
        if not self.config.enforce_interface:
            return []

        violations = []

        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        for cls in classes:
            # Check if this is an extractor class
            if cls.name.endswith("Extractor"):
                # Get base classes
                bases = []
                for base in cls.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        # Handle cases like module.ClassName
                        bases.append(base.attr)

                # Check for IDataExtractor
                if "IDataExtractor" not in bases:
                    violations.append(
                        Violation(
                            code="MISSING_INTERFACE",
                            message=f"Class '{cls.name}' must implement IDataExtractor interface",
                            line=cls.lineno,
                            severity=Severity.ERROR,
                            suggestion="Add 'IDataExtractor' to class bases: "
                            f"class {cls.name}(IDataExtractor):",
                        )
                    )

        return violations
