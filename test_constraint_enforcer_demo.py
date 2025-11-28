#!/usr/bin/env python3
"""
Demonstration script for Constraint Enforcer system.

This script shows all validators in action with real examples.
"""

import sys
sys.path.insert(0, 'src')

from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer
from edgar_analyzer.models.validation import ConstraintConfig, Severity


def print_result(title: str, result):
    """Print validation result."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")

    if result.valid:
        print("✅ PASSED - Code meets all constraints")
    else:
        print(f"❌ FAILED - {result.errors_count} errors, {result.warnings_count} warnings")
        print(f"\nViolations:")
        for violation in result.violations:
            print(f"  {violation}")


def test_valid_extractor():
    """Test 1: Valid weather extractor (should pass)."""
    code = '''
"""Weather API extractor."""

from logging import getLogger
from typing import Dict, Any
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor

logger = getLogger(__name__)


class WeatherExtractor(IDataExtractor):
    """Extract weather data from API."""

    @inject
    def __init__(self, http_client: Any):
        """Initialize extractor."""
        self.http_client = http_client

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract weather data.

        Args:
            params: Extraction parameters

        Returns:
            Weather data
        """
        logger.info(f"Extracting weather: {params}")
        try:
            data = self.http_client.get("/weather", params=params)
            logger.debug(f"Received: {data}")
            return data
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 1: Valid Weather Extractor", result)
    return result.valid


def test_missing_interface():
    """Test 2: Missing interface (should fail)."""
    code = '''
class BadExtractor:
    """Missing IDataExtractor interface."""
    pass
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 2: Missing Interface", result)
    return not result.valid  # Should fail


def test_forbidden_imports():
    """Test 3: Forbidden imports (should fail)."""
    code = '''
import os
import subprocess

from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class DangerousExtractor(IDataExtractor):
    def extract(self):
        os.system("ls")
        subprocess.call("pwd")
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 3: Forbidden Imports", result)
    return not result.valid  # Should fail


def test_security_violations():
    """Test 4: Security violations (should fail)."""
    code = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class InsecureExtractor(IDataExtractor):
    def __init__(self):
        self.api_key = "sk_live_hardcoded_12345"

    def query(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)

    def dangerous(self, code):
        return eval(code)
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 4: Security Violations", result)
    return not result.valid  # Should fail


def test_high_complexity():
    """Test 5: High complexity (should fail)."""
    code = '''
from typing import Dict, Any
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class ComplexExtractor(IDataExtractor):
    def complex_method(self, x: int) -> int:
        """High complexity method."""
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

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 5: High Complexity", result)
    return not result.valid  # Should fail


def test_missing_type_hints():
    """Test 6: Missing type hints (should fail)."""
    code = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor
from dependency_injector.wiring import inject

class UntypedExtractor(IDataExtractor):
    @inject
    def __init__(self, client):
        self.client = client

    def extract(self, params):
        return {}
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 6: Missing Type Hints", result)
    return not result.valid  # Should fail


def test_print_statements():
    """Test 7: Print statements (should fail)."""
    code = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class DebuggingExtractor(IDataExtractor):
    def extract(self, params):
        print("Debug message")
        return {}
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 7: Print Statements", result)
    return not result.valid  # Should fail


def test_custom_config():
    """Test 8: Custom configuration (permissive)."""
    code = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class SimpleExtractor(IDataExtractor):
    def extract(self, params):
        print("Allowed with custom config")
        return {}
'''

    # Create permissive config
    config = ConstraintConfig(
        allow_print_statements=True,
        enforce_type_hints=False,
    )

    enforcer = ConstraintEnforcer(config=config)
    result = enforcer.validate_code(code)
    print_result("TEST 8: Custom Config (Permissive)", result)
    return result.valid  # Should pass with permissive config


def test_syntax_error():
    """Test 9: Syntax error handling."""
    code = '''
def broken(
    # Missing closing parenthesis
'''

    enforcer = ConstraintEnforcer()
    result = enforcer.validate_code(code)
    print_result("TEST 9: Syntax Error Handling", result)
    return not result.valid  # Should fail


def test_performance():
    """Test 10: Performance benchmark."""
    code = '''
"""Large extractor for performance testing."""

from logging import getLogger
from typing import Dict, Any, Optional, List
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor

logger = getLogger(__name__)


class PerformanceTestExtractor(IDataExtractor):
    """Performance test extractor with multiple methods."""

    @inject
    def __init__(self, client: Any, config: Dict[str, Any]):
        """Initialize extractor."""
        self.client = client
        self.config = config

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data."""
        logger.info("Extracting data")
        return {}

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data."""
        logger.debug("Validating data")
        return True

    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data."""
        logger.debug("Transforming data")
        return data
'''

    import time

    enforcer = ConstraintEnforcer()

    start = time.time()
    result = enforcer.validate_code(code)
    elapsed = (time.time() - start) * 1000  # Convert to ms

    print_result("TEST 10: Performance Benchmark", result)
    print(f"\nValidation time: {elapsed:.2f}ms (target: <100ms)")

    return result.valid and elapsed < 100


def main():
    """Run all tests."""
    print("CONSTRAINT ENFORCER DEMONSTRATION")
    print("=" * 80)

    tests = [
        ("Valid Extractor", test_valid_extractor),
        ("Missing Interface", test_missing_interface),
        ("Forbidden Imports", test_forbidden_imports),
        ("Security Violations", test_security_violations),
        ("High Complexity", test_high_complexity),
        ("Missing Type Hints", test_missing_type_hints),
        ("Print Statements", test_print_statements),
        ("Custom Config", test_custom_config),
        ("Syntax Error", test_syntax_error),
        ("Performance", test_performance),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"Error: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
