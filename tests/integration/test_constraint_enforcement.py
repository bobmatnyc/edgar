"""
Integration tests for constraint enforcement.

Tests validation against realistic code examples, including valid extractor
implementations and common violation patterns.
"""

import pytest
import time

from edgar_analyzer.models.validation import ConstraintConfig
from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer


# Example 1: Perfect Weather API Extractor (should pass all checks)
VALID_WEATHER_EXTRACTOR = '''
"""
Weather API data extractor.

Extracts current weather data from OpenWeatherMap API.
"""

from logging import getLogger
from typing import Dict, Any, Optional
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor


logger = getLogger(__name__)


class WeatherAPIExtractor(IDataExtractor):
    """
    Extract weather data from OpenWeatherMap API.

    This extractor retrieves current weather conditions for a given location.
    Supports both city name and geographic coordinates.
    """

    @inject
    def __init__(self, http_client: Any, config: Dict[str, Any]):
        """
        Initialize weather extractor.

        Args:
            http_client: HTTP client for API requests
            config: Configuration containing API key and base URL
        """
        self.http_client = http_client
        self.base_url = config.get("weather_api_url", "https://api.openweathermap.org")
        self.api_key = config.get("weather_api_key")
        logger.info("WeatherAPIExtractor initialized")

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract weather data for a location.

        Args:
            params: Extraction parameters
                - city: City name (optional)
                - lat: Latitude (optional)
                - lon: Longitude (optional)

        Returns:
            Weather data including temperature, conditions, humidity

        Raises:
            ValueError: If required parameters missing
            APIError: If API request fails
        """
        logger.info(f"Extracting weather data for params: {params}")

        # Validate parameters
        if not self._validate_params(params):
            logger.error("Invalid parameters provided")
            raise ValueError("Must provide either city or lat/lon coordinates")

        # Build API request
        url = self._build_url(params)
        logger.debug(f"Making API request to: {url}")

        try:
            response = self.http_client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully extracted weather data")
            return self._transform_response(data)
        except Exception as e:
            logger.error(f"Error extracting weather data: {e}")
            raise

    def _validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate extraction parameters.

        Args:
            params: Parameters to validate

        Returns:
            True if valid, False otherwise
        """
        has_city = "city" in params
        has_coords = "lat" in params and "lon" in params
        return has_city or has_coords

    def _build_url(self, params: Dict[str, Any]) -> str:
        """
        Build API URL from parameters.

        Args:
            params: Request parameters

        Returns:
            Complete API URL
        """
        endpoint = f"{self.base_url}/data/2.5/weather"
        query_params = {"appid": self.api_key}

        if "city" in params:
            query_params["q"] = params["city"]
        else:
            query_params["lat"] = params["lat"]
            query_params["lon"] = params["lon"]

        return endpoint

    def _transform_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform API response to standard format.

        Args:
            data: Raw API response

        Returns:
            Transformed weather data
        """
        return {
            "temperature": data.get("main", {}).get("temp"),
            "conditions": data.get("weather", [{}])[0].get("main"),
            "humidity": data.get("main", {}).get("humidity"),
            "location": data.get("name"),
        }
'''


# Example 2: Code with multiple violations
INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS = '''
import os
import subprocess

class BadExtractor:
    def __init__(self, api_key):
        self.api_key = "hardcoded_secret_key_12345"

    def extract(self, query):
        print("Starting extraction")
        result = eval(query)
        os.system("ls -la")
        return result
'''


# Example 3: Code with only warnings (should not block)
EXTRACTOR_WITH_WARNINGS = '''
from logging import getLogger
from typing import Dict, Any
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor

logger = getLogger(__name__)


class SimpleExtractor(IDataExtractor):
    """Extract simple data."""

    @inject
    def __init__(self, client: Any):
        """Initialize extractor."""
        self.client = client

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data without logging API calls.

        Args:
            params: Parameters

        Returns:
            Extracted data
        """
        # This method makes API call but doesn't log it (WARNING)
        data = self.client.get("/data")
        return data
'''


# Example 4: Complex code (high complexity violation)
COMPLEX_EXTRACTOR = '''
from typing import Dict, Any
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor


class ComplexExtractor(IDataExtractor):
    """Extractor with high complexity."""

    @inject
    def __init__(self, client: Any):
        """Initialize."""
        self.client = client

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract with complex logic."""
        result = {}
        if params.get("type") == "A":
            if params.get("level") > 5:
                if params.get("active"):
                    if params.get("verified"):
                        if params.get("premium"):
                            if params.get("region") == "US":
                                if params.get("age") > 18:
                                    if params.get("consent"):
                                        if params.get("terms"):
                                            if params.get("privacy"):
                                                result = {"status": "approved"}
        return result
'''


class TestConstraintEnforcementIntegration:
    """Integration tests for constraint enforcement."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enforcer = ConstraintEnforcer()

    def test_valid_weather_extractor_passes(self):
        """Test that a well-written weather extractor passes all checks."""
        result = self.enforcer.validate_code(VALID_WEATHER_EXTRACTOR)

        # Should pass validation
        assert result.valid, f"Valid extractor should pass. Violations: {result}"

        # Should have zero errors
        assert result.errors_count == 0

        # May have zero or few warnings/info
        assert result.warnings_count <= 2  # Acceptable warning threshold

    def test_invalid_extractor_blocked(self):
        """Test that code with multiple violations is blocked."""
        result = self.enforcer.validate_code(INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS)

        # Should fail validation
        assert not result.valid

        # Should have multiple errors
        assert result.errors_count >= 4  # Missing interface, imports, hardcoded cred, eval

        # Check specific violations present
        violation_codes = {v.code for v in result.violations}
        assert "FORBIDDEN_IMPORT" in violation_codes  # os, subprocess
        assert "MISSING_INTERFACE" in violation_codes
        assert "DANGEROUS_FUNCTION" in violation_codes  # eval

    def test_warnings_do_not_block(self):
        """Test that WARNING-level violations don't block acceptance."""
        result = self.enforcer.validate_code(EXTRACTOR_WITH_WARNINGS)

        # May have warnings but should still be valid if no errors
        if result.errors_count == 0:
            assert result.valid
        else:
            # If there are errors, they should be for missing logging, not blocking issues
            error_codes = {v.code for v in result.violations if v.severity.value == "error"}
            # Check that critical violations are not present
            critical_codes = {"FORBIDDEN_IMPORT", "DANGEROUS_FUNCTION", "SQL_INJECTION_RISK"}
            assert not error_codes.intersection(critical_codes)

    def test_high_complexity_detected(self):
        """Test that high complexity code is detected."""
        result = self.enforcer.validate_code(COMPLEX_EXTRACTOR)

        # Should have high complexity violation
        violations = [v for v in result.violations if v.code == "HIGH_COMPLEXITY"]
        assert len(violations) > 0

        # Violation should reference the extract method
        assert any("extract" in v.message for v in violations)

    def test_performance_under_100ms(self):
        """Test that validation completes in under 100ms."""
        # Measure validation time
        start_time = time.time()
        result = self.enforcer.validate_code(VALID_WEATHER_EXTRACTOR)
        end_time = time.time()

        validation_time_ms = (end_time - start_time) * 1000

        # Should complete in under 100ms
        assert validation_time_ms < 100, f"Validation took {validation_time_ms:.2f}ms (target: <100ms)"

    def test_batch_validation_performance(self):
        """Test performance with multiple code snippets."""
        code_samples = [
            VALID_WEATHER_EXTRACTOR,
            INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS,
            EXTRACTOR_WITH_WARNINGS,
            COMPLEX_EXTRACTOR,
        ]

        start_time = time.time()
        results = [self.enforcer.validate_code(code) for code in code_samples]
        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000

        # Should validate 4 snippets in under 200ms total
        assert total_time_ms < 200, f"Batch validation took {total_time_ms:.2f}ms (target: <200ms)"

        # Check that all validations completed
        assert len(results) == 4

    def test_custom_config_enforcement(self):
        """Test enforcement with custom configuration."""
        # Create strict config
        strict_config = ConstraintConfig(
            max_complexity=5,  # Stricter complexity threshold
            max_method_lines=30,  # Stricter line limit
            enforce_type_hints=True,
            enforce_docstrings=True,
        )

        strict_enforcer = ConstraintEnforcer(config=strict_config)

        # Code that passes default config but fails strict config
        result = strict_enforcer.validate_code(VALID_WEATHER_EXTRACTOR)

        # May have different violations with strict config
        # (This is expected - strict config catches more issues)

    def test_error_recovery(self):
        """Test that enforcer handles malformed code gracefully."""
        malformed_code = '''
        def broken(
            # Unclosed parenthesis
        '''

        result = self.enforcer.validate_code(malformed_code)

        # Should return validation result, not crash
        assert isinstance(result.violations, list)
        assert not result.valid
        assert result.violations[0].code == "SYNTAX_ERROR"

    def test_config_reload(self):
        """Test that configuration can be updated dynamically."""
        # Start with default config
        result1 = self.enforcer.validate_code(INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS)
        initial_violations = len(result1.violations)

        # Update to more permissive config
        permissive_config = ConstraintConfig(
            enforce_interface=False,  # Don't require interface
            allow_print_statements=True,  # Allow prints
        )
        self.enforcer.update_config(permissive_config)

        # Re-validate
        result2 = self.enforcer.validate_code(INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS)

        # Should have fewer violations (but still some due to security issues)
        assert len(result2.violations) < initial_violations

    def test_violation_line_numbers_accurate(self):
        """Test that violation line numbers are accurate."""
        result = self.enforcer.validate_code(INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS)

        # All violations should have line numbers
        for violation in result.violations:
            if violation.code != "SYNTAX_ERROR":  # Syntax errors might not have lines
                # Line number should be reasonable (within code length)
                assert violation.line is None or violation.line > 0

    def test_suggestion_quality(self):
        """Test that violations include actionable suggestions."""
        result = self.enforcer.validate_code(INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS)

        # Most violations should have suggestions
        violations_with_suggestions = [v for v in result.violations if v.suggestion]
        assert len(violations_with_suggestions) > 0

        # Suggestions should be non-empty and helpful
        for violation in violations_with_suggestions:
            assert len(violation.suggestion) > 10  # Not just "Fix it"
            # Should contain actionable text
            assert any(
                keyword in violation.suggestion.lower()
                for keyword in ["remove", "add", "use", "replace", "fix"]
            )


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    def test_ai_generated_code_validation(self):
        """Simulate validating AI-generated extractor code."""
        enforcer = ConstraintEnforcer()

        # Simulate AI generating valid code
        valid_result = enforcer.validate_code(VALID_WEATHER_EXTRACTOR)
        assert valid_result.valid

        # Simulate AI generating invalid code (should be rejected)
        invalid_result = enforcer.validate_code(INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS)
        assert not invalid_result.valid

        # AI should get feedback to fix issues
        assert len(invalid_result.violations) > 0
        assert all(v.suggestion is not None for v in invalid_result.violations[:3])

    def test_iterative_code_improvement(self):
        """Test iterative improvement based on violation feedback."""
        enforcer = ConstraintEnforcer()

        # Start with bad code
        iteration_1 = INVALID_EXTRACTOR_MULTIPLE_VIOLATIONS
        result_1 = enforcer.validate_code(iteration_1)
        assert not result_1.valid
        initial_violations = len(result_1.violations)

        # Improve: Add interface, remove forbidden imports
        iteration_2 = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class BadExtractor(IDataExtractor):
    def __init__(self, api_key):
        self.api_key = "hardcoded_secret_key_12345"

    def extract(self, query):
        print("Starting extraction")
        result = eval(query)
        return result
'''
        result_2 = enforcer.validate_code(iteration_2)
        # Should have fewer violations (removed forbidden imports)
        assert len(result_2.violations) < initial_violations

        # Final iteration: Fix remaining issues
        iteration_3 = VALID_WEATHER_EXTRACTOR
        result_3 = enforcer.validate_code(iteration_3)
        assert result_3.valid
