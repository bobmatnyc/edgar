"""
Unit tests for ConstraintEnforcer service.

Tests all validators and constraint enforcement logic.
"""

import pytest

from edgar_analyzer.models.validation import (
    ConstraintConfig,
    ValidationResult,
    Severity,
)
from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer


class TestConstraintEnforcer:
    """Test cases for ConstraintEnforcer service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enforcer = ConstraintEnforcer()

    def test_valid_code_passes(self):
        """Test that valid code passes all constraints."""
        valid_code = '''
"""Valid extractor module."""

from logging import getLogger
from typing import Dict, Any
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor


logger = getLogger(__name__)


class WeatherExtractor(IDataExtractor):
    """Extract weather data from API."""

    @inject
    def __init__(self, api_client: Any):
        """Initialize extractor with dependencies."""
        self.api_client = api_client

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract weather data.

        Args:
            params: Extraction parameters

        Returns:
            Extracted weather data
        """
        logger.info(f"Extracting weather data with params: {params}")
        try:
            data = self.api_client.get("/weather", params=params)
            logger.debug(f"Received data: {data}")
            return data
        except Exception as e:
            logger.error(f"Error extracting weather data: {e}")
            raise
'''
        result = self.enforcer.validate_code(valid_code)
        assert result.valid, f"Valid code should pass, got violations: {result.violations}"
        assert len(result.violations) == 0

    def test_syntax_error_detected(self):
        """Test that syntax errors are detected."""
        invalid_code = '''
def broken_syntax(
    # Missing closing parenthesis
'''
        result = self.enforcer.validate_code(invalid_code)
        assert not result.valid
        assert len(result.violations) == 1
        assert result.violations[0].code == "SYNTAX_ERROR"

    def test_missing_interface_detected(self):
        """Test that missing IDataExtractor interface is detected."""
        code_without_interface = '''
class WeatherExtractor:
    """Missing interface."""
    pass
'''
        result = self.enforcer.validate_code(code_without_interface)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "MISSING_INTERFACE"]
        assert len(violations) == 1
        assert "IDataExtractor" in violations[0].message

    def test_missing_inject_decorator_detected(self):
        """Test that missing @inject decorator is detected."""
        code_without_inject = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def __init__(self, api_client):
        self.api_client = api_client
'''
        result = self.enforcer.validate_code(code_without_inject)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "MISSING_DECORATOR"]
        assert len(violations) == 1
        assert "@inject" in violations[0].message

    def test_missing_type_hints_detected(self):
        """Test that missing type hints are detected."""
        code_without_types = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor
from dependency_injector.wiring import inject

class WeatherExtractor(IDataExtractor):
    @inject
    def __init__(self, api_client):
        self.api_client = api_client

    def extract(self, params):
        return {}
'''
        result = self.enforcer.validate_code(code_without_types)
        assert not result.valid
        type_violations = [
            v
            for v in result.violations
            if v.code in ("MISSING_TYPE_HINT", "MISSING_RETURN_TYPE")
        ]
        assert len(type_violations) > 0

    def test_forbidden_import_detected(self):
        """Test that forbidden imports are detected."""
        code_with_forbidden_import = '''
import os
import subprocess

from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def extract(self):
        os.system("ls")
'''
        result = self.enforcer.validate_code(code_with_forbidden_import)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "FORBIDDEN_IMPORT"]
        assert len(violations) >= 2  # os and subprocess
        assert any("os" in v.message for v in violations)
        assert any("subprocess" in v.message for v in violations)

    def test_high_complexity_detected(self):
        """Test that high cyclomatic complexity is detected."""
        complex_code = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def complex_method(self, x: int) -> int:
        """Very complex method."""
        if x > 0:
            if x > 10:
                if x > 20:
                    if x > 30:
                        if x > 40:
                            if x > 50:
                                if x > 60:
                                    if x > 70:
                                        if x > 80:
                                            if x > 90:
                                                return 100
        return 0
'''
        result = self.enforcer.validate_code(complex_code)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "HIGH_COMPLEXITY"]
        assert len(violations) > 0

    def test_print_statement_detected(self):
        """Test that print() statements are detected."""
        code_with_print = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def extract(self):
        print("Debug message")
        return {}
'''
        result = self.enforcer.validate_code(code_with_print)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "PRINT_STATEMENT"]
        assert len(violations) == 1

    def test_dangerous_function_detected(self):
        """Test that dangerous functions like eval are detected."""
        code_with_eval = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def extract(self, code: str):
        result = eval(code)
        return result
'''
        result = self.enforcer.validate_code(code_with_eval)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "DANGEROUS_FUNCTION"]
        assert len(violations) == 1
        assert "eval" in violations[0].message

    def test_sql_injection_detected(self):
        """Test that SQL injection patterns are detected."""
        code_with_sql_injection = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def query_data(self, user_id: str):
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
'''
        result = self.enforcer.validate_code(code_with_sql_injection)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "SQL_INJECTION_RISK"]
        assert len(violations) > 0

    def test_hardcoded_credential_detected(self):
        """Test that hardcoded credentials are detected."""
        code_with_credentials = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def __init__(self):
        self.api_key = "sk_live_1234567890abcdef"
        self.password = "SuperSecret123"
'''
        result = self.enforcer.validate_code(code_with_credentials)
        assert not result.valid
        violations = [v for v in result.violations if v.code == "HARDCODED_CREDENTIAL"]
        assert len(violations) >= 1

    def test_severity_levels(self):
        """Test that violations have appropriate severity levels."""
        code_with_multiple_issues = '''
import os  # ERROR

from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    def extract(self):  # WARNING - missing logging
        pass
'''
        result = self.enforcer.validate_code(code_with_multiple_issues)
        assert not result.valid

        # Check severity counts
        errors = result.get_violations_by_severity(Severity.ERROR)
        warnings = result.get_violations_by_severity(Severity.WARNING)

        assert len(errors) > 0  # Forbidden import
        # May have warnings for missing logging or other issues

    def test_config_update(self):
        """Test that configuration can be updated."""
        # Create custom config
        custom_config = ConstraintConfig(
            max_complexity=5,  # Lower threshold
            allow_print_statements=True,  # Allow prints
        )

        enforcer = ConstraintEnforcer(config=custom_config)

        # Code with print should now pass
        code_with_print = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor
from dependency_injector.wiring import inject
from typing import Dict, Any

class WeatherExtractor(IDataExtractor):
    @inject
    def __init__(self, client: Any):
        self.client = client

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        print("Allowed now")
        return {}
'''
        result = enforcer.validate_code(code_with_print)
        print_violations = [v for v in result.violations if v.code == "PRINT_STATEMENT"]
        assert len(print_violations) == 0  # Print should be allowed

    def test_validation_result_string_representation(self):
        """Test that ValidationResult has useful string representation."""
        code_with_issues = '''
import os

class BadExtractor:
    pass
'''
        result = self.enforcer.validate_code(code_with_issues)
        result_str = str(result)

        assert "❌" in result_str
        assert "error" in result_str.lower()
        assert "FORBIDDEN_IMPORT" in result_str or "MISSING_INTERFACE" in result_str

    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        result = self.enforcer.validate_file("/nonexistent/file.py")
        assert not result.valid
        assert result.violations[0].code == "FILE_NOT_FOUND"

    def test_empty_code(self):
        """Test validation of empty code."""
        result = self.enforcer.validate_code("")
        # Empty code should be valid (no violations)
        assert result.valid

    def test_method_too_long_detected(self):
        """Test that excessively long methods are detected."""
        # Generate a method with > 50 lines
        long_method = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor
from typing import Dict, Any

class WeatherExtractor(IDataExtractor):
    def very_long_method(self, x: int) -> int:
        """A very long method."""
'''
        # Add 60 lines of code
        for i in range(60):
            long_method += f"        y{i} = {i}\n"
        long_method += "        return 0\n"

        result = self.enforcer.validate_code(long_method)
        violations = [v for v in result.violations if v.code == "METHOD_TOO_LONG"]
        assert len(violations) > 0

    def test_class_too_long_detected(self):
        """Test that excessively long classes are detected."""
        # Generate a class with > 300 lines
        long_class = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    """Very long class."""
'''
        # Add many methods to make it long
        for i in range(50):
            long_class += f'''
    def method_{i}(self) -> int:
        """Method {i}."""
        x = {i}
        y = x + 1
        return y
'''

        result = self.enforcer.validate_code(long_class)
        violations = [v for v in result.violations if v.code == "CLASS_TOO_LONG"]
        assert len(violations) > 0


class TestValidationModels:
    """Test validation data models."""

    def test_violation_string_representation(self):
        """Test Violation string representation."""
        from edgar_analyzer.models.validation import Violation, Severity

        violation = Violation(
            code="TEST_VIOLATION",
            message="Test message",
            line=42,
            severity=Severity.ERROR,
            suggestion="Fix it",
        )

        violation_str = str(violation)
        assert "TEST_VIOLATION" in violation_str
        assert "Test message" in violation_str
        assert "42" in violation_str
        assert "Fix it" in violation_str

    def test_validation_result_counts(self):
        """Test ValidationResult violation counts."""
        from edgar_analyzer.models.validation import (
            ValidationResult,
            Violation,
            Severity,
        )

        violations = [
            Violation("ERR1", "Error 1", severity=Severity.ERROR),
            Violation("ERR2", "Error 2", severity=Severity.ERROR),
            Violation("WARN1", "Warning 1", severity=Severity.WARNING),
            Violation("INFO1", "Info 1", severity=Severity.INFO),
        ]

        result = ValidationResult(valid=False, violations=violations)

        assert result.errors_count == 2
        assert result.warnings_count == 1
        assert result.info_count == 1

    def test_constraint_config_from_dict(self):
        """Test ConstraintConfig creation from dictionary."""
        config_dict = {
            "max_complexity": 15,
            "max_method_lines": 100,
            "forbidden_imports": ["os", "subprocess"],
            "enforce_type_hints": False,
        }

        config = ConstraintConfig.from_dict(config_dict)

        assert config.max_complexity == 15
        assert config.max_method_lines == 100
        assert "os" in config.forbidden_imports
        assert config.enforce_type_hints is False
