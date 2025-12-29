"""Tests for AccuracyValidator."""

import pytest

from edgar.validators.accuracy_validator import AccuracyValidator


class TestAccuracyValidator:
    """Test suite for AccuracyValidator."""

    @pytest.fixture
    def validator(self) -> AccuracyValidator:
        """Create validator instance."""
        return AccuracyValidator(timeout=5.0)

    class TestValidation:
        """Tests for validate method."""

        def test_matching_outputs_pass(self, validator: AccuracyValidator) -> None:
            """Code that produces correct output passes."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        return Output(value=raw_data["input"] * 2)
'''
            examples = [{"input": 5}]
            expected = [{"value": 10}]

            result = validator.validate(code, examples, expected)
            assert result.valid
            assert len(result.errors) == 0

        def test_mismatched_outputs_fail(self, validator: AccuracyValidator) -> None:
            """Code that produces wrong output fails."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        return Output(value=999)  # Wrong value
'''
            examples = [{"input": 5}]
            expected = [{"value": 10}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            assert any("mismatch" in err.lower() for err in result.errors)

        def test_example_count_mismatch_fails(self, validator: AccuracyValidator) -> None:
            """Mismatched example/expected counts fail."""
            code = "class Extractor: pass"
            examples = [{"a": 1}, {"b": 2}]
            expected = [{"x": 1}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            assert any("mismatch" in err.lower() for err in result.errors)

        def test_empty_examples_warns(self, validator: AccuracyValidator) -> None:
            """Empty examples list should warn."""
            code = "class Extractor: pass"
            result = validator.validate(code, [], [])
            assert result.valid  # Technically valid
            assert len(result.warnings) > 0
            assert any("no examples" in warning.lower() for warning in result.warnings)

        def test_multiple_examples(self, validator: AccuracyValidator) -> None:
            """Multiple examples are all validated."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    doubled: int

class Extractor:
    def extract(self, raw_data):
        return Output(doubled=raw_data["x"] * 2)
'''
            examples = [{"x": 1}, {"x": 5}, {"x": 10}]
            expected = [{"doubled": 2}, {"doubled": 10}, {"doubled": 20}]

            result = validator.validate(code, examples, expected)
            assert result.valid

        def test_partial_success_reports_accuracy(self, validator: AccuracyValidator) -> None:
            """Partial success reports accuracy percentage."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        # Only correct for x=1
        if raw_data["x"] == 1:
            return Output(value=2)
        return Output(value=999)
'''
            examples = [{"x": 1}, {"x": 5}]
            expected = [{"value": 2}, {"value": 10}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            # Should report accuracy in warnings
            assert any("50" in warning or "1/2" in warning for warning in result.warnings)

        def test_execution_error_captured(self, validator: AccuracyValidator) -> None:
            """Runtime errors during execution are captured."""
            code = '''
class Extractor:
    def extract(self, raw_data):
        raise ValueError("Test error")
'''
            examples = [{"x": 1}]
            expected = [{"value": 1}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            assert any("execution failed" in err.lower() or "error" in err.lower() for err in result.errors)

        def test_missing_extractor_class_fails(self, validator: AccuracyValidator) -> None:
            """Code without extractor class fails."""
            code = '''
def some_function():
    pass
'''
            examples = [{"x": 1}]
            expected = [{"value": 1}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            assert any("failed" in err.lower() or "error" in err.lower() for err in result.errors)

    class TestOutputComparison:
        """Tests for _compare_outputs method."""

        def test_identical_dicts_match(self, validator: AccuracyValidator) -> None:
            """Identical dicts produce no differences."""
            actual = {"a": 1, "b": "test"}
            expected = {"a": 1, "b": "test"}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) == 0

        def test_different_values_detected(self, validator: AccuracyValidator) -> None:
            """Different values are detected."""
            actual = {"a": 1}
            expected = {"a": 2}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "a" in diffs[0]

        def test_missing_keys_detected(self, validator: AccuracyValidator) -> None:
            """Missing keys are detected."""
            actual = {"a": 1}
            expected = {"a": 1, "b": 2}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "missing" in diffs[0].lower() or "b" in diffs[0].lower()

        def test_extra_keys_detected(self, validator: AccuracyValidator) -> None:
            """Extra keys are detected."""
            actual = {"a": 1, "b": 2, "c": 3}
            expected = {"a": 1, "b": 2}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "unexpected" in diffs[0].lower() or "c" in diffs[0].lower()

        def test_nested_dict_comparison(self, validator: AccuracyValidator) -> None:
            """Nested dicts are compared recursively."""
            actual = {"outer": {"inner": 1}}
            expected = {"outer": {"inner": 2}}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "inner" in diffs[0]

        def test_deeply_nested_dicts(self, validator: AccuracyValidator) -> None:
            """Deeply nested structures are compared."""
            actual = {"a": {"b": {"c": {"d": 1}}}}
            expected = {"a": {"b": {"c": {"d": 2}}}}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0

        def test_list_comparison(self, validator: AccuracyValidator) -> None:
            """Lists are compared element by element."""
            actual = {"items": [1, 2, 3]}
            expected = {"items": [1, 2, 3]}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) == 0

        def test_list_length_mismatch(self, validator: AccuracyValidator) -> None:
            """List length differences are detected."""
            actual = {"items": [1, 2]}
            expected = {"items": [1, 2, 3]}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "length" in diffs[0].lower() or "2" in diffs[0] and "3" in diffs[0]

        def test_list_value_mismatch(self, validator: AccuracyValidator) -> None:
            """List value differences are detected."""
            actual = {"items": [1, 2, 3]}
            expected = {"items": [1, 99, 3]}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "99" in diffs[0] or "[1]" in diffs[0]

        def test_list_of_dicts_comparison(self, validator: AccuracyValidator) -> None:
            """Lists of dicts are compared recursively."""
            actual = {"items": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}
            expected = {"items": [{"id": 1, "name": "a"}, {"id": 2, "name": "c"}]}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "name" in diffs[0]

        def test_float_tolerance(self, validator: AccuracyValidator) -> None:
            """Floats within tolerance match."""
            actual = {"value": 1.00001}
            expected = {"value": 1.0}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) == 0  # Within 0.0001 tolerance

        def test_float_outside_tolerance(self, validator: AccuracyValidator) -> None:
            """Floats outside tolerance are detected."""
            actual = {"value": 1.001}
            expected = {"value": 1.0}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0

        def test_int_float_comparison(self, validator: AccuracyValidator) -> None:
            """Int and float are compared numerically."""
            actual = {"value": 5}
            expected = {"value": 5.0}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) == 0

        def test_error_in_actual_output(self, validator: AccuracyValidator) -> None:
            """Error in actual output is reported."""
            actual = {"error": "Execution error", "type": "ValueError"}
            expected = {"value": 1}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            assert "error" in diffs[0].lower()

        def test_complex_nested_structure(self, validator: AccuracyValidator) -> None:
            """Complex nested structures are compared correctly."""
            actual = {
                "data": {
                    "users": [
                        {"id": 1, "tags": ["a", "b"]},
                        {"id": 2, "tags": ["c"]},
                    ]
                }
            }
            expected = {
                "data": {
                    "users": [
                        {"id": 1, "tags": ["a", "b"]},
                        {"id": 2, "tags": ["c"]},
                    ]
                }
            }
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) == 0

        def test_path_reporting_in_nested_diffs(self, validator: AccuracyValidator) -> None:
            """Diff messages include full path to nested field."""
            actual = {"data": {"user": {"name": "Alice"}}}
            expected = {"data": {"user": {"name": "Bob"}}}
            diffs = validator._compare_outputs(actual, expected)
            assert len(diffs) > 0
            # Should include path like "data.user.name"
            assert "data" in diffs[0] or "user" in diffs[0] or "name" in diffs[0]

    class TestSafeExecution:
        """Tests for _execute_code_safely method."""

        def test_successful_execution(self, validator: AccuracyValidator) -> None:
            """Valid code executes successfully."""
            code = '''
from pydantic import BaseModel

class Result(BaseModel):
    doubled: int

class Extractor:
    def extract(self, raw_data):
        return Result(doubled=raw_data["x"] * 2)
'''
            result = validator._execute_code_safely(code, {"x": 5})
            assert "doubled" in result
            assert result["doubled"] == 10

        def test_execution_error_handled(self, validator: AccuracyValidator) -> None:
            """Execution errors are captured in validate method."""
            code = '''
class Extractor:
    def extract(self, raw_data):
        raise ValueError("Test error")
'''
            examples = [{}]
            expected = [{"value": 1}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            assert any("failed" in err.lower() or "error" in err.lower() for err in result.errors)

        def test_timeout_enforcement(self) -> None:
            """Long-running code times out."""
            validator = AccuracyValidator(timeout=0.5)
            code = '''
import time

class Extractor:
    def extract(self, raw_data):
        time.sleep(10)  # Long sleep
        return {}
'''
            with pytest.raises(RuntimeError, match="timed out"):
                validator._execute_code_safely(code, {})

        def test_pydantic_v1_dict_method(self, validator: AccuracyValidator) -> None:
            """Handles Pydantic v1 .dict() method."""
            code = '''
from pydantic import BaseModel

class Result(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        return Result(value=42)
'''
            result = validator._execute_code_safely(code, {})
            assert "value" in result
            assert result["value"] == 42

        def test_pydantic_v2_model_dump(self, validator: AccuracyValidator) -> None:
            """Handles Pydantic v2 .model_dump() method."""
            # This test will work with either Pydantic v1 or v2
            code = '''
from pydantic import BaseModel

class Result(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        return Result(value=42)
'''
            result = validator._execute_code_safely(code, {})
            assert "value" in result
            assert result["value"] == 42

        def test_complex_pydantic_model(self, validator: AccuracyValidator) -> None:
            """Handles complex Pydantic models with nested structures."""
            code = '''
from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    id: int
    name: str

class Result(BaseModel):
    items: List[Item]
    count: int

class Extractor:
    def extract(self, raw_data):
        items = [Item(id=i, name=f"item_{i}") for i in range(3)]
        return Result(items=items, count=len(items))
'''
            result = validator._execute_code_safely(code, {})
            assert "items" in result
            assert "count" in result
            assert result["count"] == 3
            assert len(result["items"]) == 3

    class TestEdgeCases:
        """Edge case tests."""

        def test_no_extractor_class(self, validator: AccuracyValidator) -> None:
            """Code without extractor class raises RuntimeError."""
            code = '''
def some_function():
    pass
'''
            with pytest.raises(RuntimeError, match="Execution failed"):
                validator._execute_code_safely(code, {})

        def test_extractor_without_extract_method(self, validator: AccuracyValidator) -> None:
            """Extractor without extract method raises RuntimeError."""
            code = '''
class Extractor:
    def process(self, data):
        return data
'''
            with pytest.raises(RuntimeError, match="Execution failed"):
                validator._execute_code_safely(code, {})

        def test_extract_method_raises_exception(self, validator: AccuracyValidator) -> None:
            """Extract method that raises exception raises RuntimeError."""
            code = '''
class Extractor:
    def extract(self, raw_data):
        raise RuntimeError("Something went wrong")
'''
            with pytest.raises(RuntimeError, match="Execution failed"):
                validator._execute_code_safely(code, {})

        def test_syntax_error_in_code(self, validator: AccuracyValidator) -> None:
            """Syntax errors raise RuntimeError."""
            code = '''
class Extractor
    def extract(self, raw_data):
        return {}
'''
            with pytest.raises(RuntimeError, match="SyntaxError"):
                validator._execute_code_safely(code, {})

        def test_import_error_handled(self, validator: AccuracyValidator) -> None:
            """Import errors raise RuntimeError."""
            code = '''
from nonexistent_module import something

class Extractor:
    def extract(self, raw_data):
        return {}
'''
            with pytest.raises(RuntimeError, match="ModuleNotFoundError"):
                validator._execute_code_safely(code, {})

        def test_multiple_extractor_classes(self, validator: AccuracyValidator) -> None:
            """First extractor class with extract method is used."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    value: int

class NotUsed:
    def extract(self, raw_data):
        return Output(value=999)

class Extractor:
    def extract(self, raw_data):
        return Output(value=42)
'''
            result = validator._execute_code_safely(code, {})
            # Should use first class with extract method
            assert "value" in result

        def test_unicode_in_output(self, validator: AccuracyValidator) -> None:
            """Unicode characters in output are handled."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    message: str

class Extractor:
    def extract(self, raw_data):
        return Output(message="Hello 世界 🌍")
'''
            result = validator._execute_code_safely(code, {})
            assert "message" in result
            assert "世界" in result["message"]

        def test_very_large_output(self, validator: AccuracyValidator) -> None:
            """Very large outputs are handled."""
            code = '''
from pydantic import BaseModel
from typing import List

class Output(BaseModel):
    items: List[int]

class Extractor:
    def extract(self, raw_data):
        return Output(items=list(range(10000)))
'''
            result = validator._execute_code_safely(code, {})
            assert "items" in result
            assert len(result["items"]) == 10000

    class TestAccuracyMetrics:
        """Tests for accuracy reporting and metrics."""

        def test_100_percent_accuracy(self, validator: AccuracyValidator) -> None:
            """100% accuracy has no warnings."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        return Output(value=raw_data["x"])
'''
            examples = [{"x": 1}, {"x": 2}, {"x": 3}]
            expected = [{"value": 1}, {"value": 2}, {"value": 3}]

            result = validator.validate(code, examples, expected)
            assert result.valid
            # No accuracy warnings for 100% pass rate
            accuracy_warnings = [w for w in result.warnings if "accuracy" in w.lower()]
            assert len(accuracy_warnings) == 0

        def test_0_percent_accuracy(self, validator: AccuracyValidator) -> None:
            """0% accuracy reports all failures."""
            code = '''
from pydantic import BaseModel

class Output(BaseModel):
    value: int

class Extractor:
    def extract(self, raw_data):
        return Output(value=999)  # Always wrong
'''
            examples = [{"x": 1}, {"x": 2}]
            expected = [{"value": 1}, {"value": 2}]

            result = validator.validate(code, examples, expected)
            assert not result.valid
            # Should report 0/2 or 0.0%
            assert any("0" in warning for warning in result.warnings)
