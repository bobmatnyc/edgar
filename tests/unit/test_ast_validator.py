"""Tests for ASTValidator."""

import pytest

from edgar.validators.ast_validator import ASTValidator, ValidationResult


class TestASTValidator:
    """Test suite for ASTValidator."""

    @pytest.fixture
    def validator(self) -> ASTValidator:
        """Create validator instance."""
        return ASTValidator()

    class TestSyntaxValidation:
        """Tests for syntax validation."""

        def test_valid_python_passes(self, validator: ASTValidator) -> None:
            """Valid Python code passes."""
            code = '''
def hello(name: str) -> str:
    return f"Hello, {name}!"
'''
            result = validator.validate(code)
            assert result.valid
            assert len(result.errors) == 0

        def test_invalid_syntax_fails(self, validator: ASTValidator) -> None:
            """Invalid syntax fails."""
            code = "def broken("
            result = validator.validate(code)
            assert not result.valid
            assert len(result.errors) > 0
            assert "syntax" in result.errors[0].lower()

        def test_empty_code_passes(self, validator: ASTValidator) -> None:
            """Empty string is valid Python."""
            result = validator.validate("")
            assert result.valid
            assert len(result.errors) == 0

        def test_only_comments_passes(self, validator: ASTValidator) -> None:
            """Comments-only code is valid."""
            code = "# Just a comment"
            result = validator.validate(code)
            assert result.valid
            assert len(result.errors) == 0

        def test_multiline_syntax_error(self, validator: ASTValidator) -> None:
            """Multiline syntax error is detected."""
            code = '''
def valid_function():
    pass

def broken_function(
    # Missing closing parenthesis
'''
            result = validator.validate(code)
            assert not result.valid
            assert len(result.errors) > 0

        def test_indentation_error(self, validator: ASTValidator) -> None:
            """Indentation error is detected."""
            code = '''
def test():
pass
'''
            result = validator.validate(code)
            assert not result.valid
            assert len(result.errors) > 0

        def test_complex_valid_code(self, validator: ASTValidator) -> None:
            """Complex valid code passes."""
            code = '''
from typing import Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field

@dataclass(frozen=True)
class MyService:
    client: str

    async def fetch(self) -> dict[str, Any]:
        return {"data": "test"}

class MyModel(BaseModel):
    value: int = Field(..., description="A value")
'''
            result = validator.validate(code)
            assert result.valid
            assert len(result.errors) == 0

    class TestValidationResult:
        """Tests for ValidationResult dataclass."""

        def test_valid_result(self) -> None:
            """Valid result has no errors."""
            result = ValidationResult(valid=True, errors=[], warnings=[])
            assert result.valid
            assert len(result.errors) == 0
            assert len(result.warnings) == 0

        def test_invalid_result(self) -> None:
            """Invalid result has errors."""
            result = ValidationResult(
                valid=False,
                errors=["Syntax error"],
                warnings=[],
            )
            assert not result.valid
            assert len(result.errors) == 1
            assert result.errors[0] == "Syntax error"

        def test_valid_with_warnings(self) -> None:
            """Result can be valid but have warnings."""
            result = ValidationResult(
                valid=True,
                errors=[],
                warnings=["Missing docstring"],
            )
            assert result.valid
            assert len(result.errors) == 0
            assert len(result.warnings) == 1

        def test_invalid_with_warnings(self) -> None:
            """Invalid result can also have warnings."""
            result = ValidationResult(
                valid=False,
                errors=["Syntax error"],
                warnings=["Missing docstring"],
            )
            assert not result.valid
            assert len(result.errors) == 1
            assert len(result.warnings) == 1

    class TestEdgeCases:
        """Edge case tests."""

        def test_whitespace_only(self, validator: ASTValidator) -> None:
            """Whitespace-only code is valid."""
            result = validator.validate("   \n\n  \t  ")
            assert result.valid

        def test_unicode_characters(self, validator: ASTValidator) -> None:
            """Unicode characters in strings are valid."""
            code = '''
text = "Hello 世界 🌍"
'''
            result = validator.validate(code)
            assert result.valid

        def test_very_long_line(self, validator: ASTValidator) -> None:
            """Very long lines are syntactically valid."""
            long_string = "x" * 10000
            code = f'text = "{long_string}"'
            result = validator.validate(code)
            assert result.valid

        def test_nested_structures(self, validator: ASTValidator) -> None:
            """Deeply nested structures are valid."""
            code = '''
def outer():
    def middle():
        def inner():
            class Nested:
                def method(self):
                    return {"a": {"b": {"c": 1}}}
            return Nested()
        return inner()
    return middle()
'''
            result = validator.validate(code)
            assert result.valid
