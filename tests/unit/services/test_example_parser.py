"""
Unit tests for ExampleParser service.

Tests cover:
- Simple field mappings
- Nested structure handling
- Array operations
- Type conversions
- Pattern detection accuracy
- Confidence scoring
- Edge cases
"""

import pytest

from edgar_analyzer.models.patterns import PatternType
from edgar_analyzer.models.project_config import ExampleConfig
from edgar_analyzer.services.example_parser import ExampleParser
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer


class TestExampleParser:
    """Test suite for ExampleParser service."""

    @pytest.fixture
    def parser(self):
        """Create ExampleParser instance."""
        return ExampleParser(SchemaAnalyzer())

    def test_simple_field_mapping(self, parser):
        """Test detection of simple field mapping pattern."""
        examples = [
            ExampleConfig(
                input={"name": "London", "temp": 15.5},
                output={"city": "London", "temperature": 15.5}
            ),
            ExampleConfig(
                input={"name": "Tokyo", "temp": 22.3},
                output={"city": "Tokyo", "temperature": 22.3}
            )
        ]

        parsed = parser.parse_examples(examples)

        assert parsed.num_examples == 2
        assert len(parsed.patterns) > 0

        # Should detect field mapping for 'city'
        city_pattern = parsed.get_pattern_for_field("city")
        assert city_pattern is not None
        assert city_pattern.confidence == 1.0

    def test_nested_field_extraction(self, parser):
        """Test detection of nested field extraction."""
        examples = [
            ExampleConfig(
                input={"main": {"temp": 15.5, "humidity": 80}},
                output={"temperature_c": 15.5}
            ),
            ExampleConfig(
                input={"main": {"temp": 22.3, "humidity": 65}},
                output={"temperature_c": 22.3}
            )
        ]

        parsed = parser.parse_examples(examples)

        assert parsed.num_examples == 2
        assert len(parsed.patterns) > 0

        # Should detect nested extraction
        temp_pattern = parsed.get_pattern_for_field("temperature_c")
        assert temp_pattern is not None
        assert temp_pattern.type == PatternType.FIELD_EXTRACTION
        assert "main.temp" in temp_pattern.source_path

    def test_array_first_element(self, parser):
        """Test detection of array first element extraction."""
        examples = [
            ExampleConfig(
                input={"weather": [{"description": "light rain"}, {"description": "clouds"}]},
                output={"conditions": "light rain"}
            ),
            ExampleConfig(
                input={"weather": [{"description": "clear sky"}]},
                output={"conditions": "clear sky"}
            )
        ]

        parsed = parser.parse_examples(examples)

        assert parsed.num_examples == 2
        conditions_pattern = parsed.get_pattern_for_field("conditions")
        assert conditions_pattern is not None
        # Should detect array first pattern
        assert conditions_pattern.type in [PatternType.ARRAY_FIRST, PatternType.FIELD_EXTRACTION]

    def test_constant_value_pattern(self, parser):
        """Test detection of constant value pattern."""
        examples = [
            ExampleConfig(
                input={"name": "London"},
                output={"source": "openweather"}
            ),
            ExampleConfig(
                input={"name": "Tokyo"},
                output={"source": "openweather"}
            )
        ]

        parsed = parser.parse_examples(examples)

        source_pattern = parsed.get_pattern_for_field("source")
        assert source_pattern is not None
        assert source_pattern.type == PatternType.CONSTANT
        assert source_pattern.confidence == 1.0

    def test_type_conversion_pattern(self, parser):
        """Test detection of type conversion."""
        examples = [
            ExampleConfig(
                input={"count": "42"},
                output={"count": 42}
            ),
            ExampleConfig(
                input={"count": "100"},
                output={"count": 100}
            )
        ]

        parsed = parser.parse_examples(examples)

        count_pattern = parsed.get_pattern_for_field("count")
        assert count_pattern is not None
        # Type conversion should be detected

    def test_empty_examples(self, parser):
        """Test handling of empty examples list."""
        parsed = parser.parse_examples([])

        assert parsed.num_examples == 0
        assert len(parsed.patterns) == 0
        assert len(parsed.input_schema.fields) == 0

    def test_multiple_patterns_same_field(self, parser):
        """Test when multiple patterns could apply to same field."""
        examples = [
            ExampleConfig(
                input={"name": "London", "city": "London"},
                output={"location": "London"}
            ),
            ExampleConfig(
                input={"name": "Tokyo", "city": "Tokyo"},
                output={"location": "Tokyo"}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should identify one primary pattern
        location_pattern = parsed.get_pattern_for_field("location")
        assert location_pattern is not None
        assert location_pattern.confidence > 0.0

    def test_high_confidence_patterns(self, parser):
        """Test high confidence pattern detection."""
        examples = [
            ExampleConfig(
                input={"temp": 15.5},
                output={"temperature": 15.5}
            ),
            ExampleConfig(
                input={"temp": 22.3},
                output={"temperature": 22.3}
            ),
            ExampleConfig(
                input={"temp": 18.0},
                output={"temperature": 18.0}
            )
        ]

        parsed = parser.parse_examples(examples)

        high_conf = parsed.high_confidence_patterns
        assert len(high_conf) > 0
        assert all(p.confidence >= 0.9 for p in high_conf)

    def test_warnings_generation(self, parser):
        """Test warning generation for edge cases."""
        # Only 1 example - should warn
        examples = [
            ExampleConfig(
                input={"temp": 15.5},
                output={"temperature": 15.5}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should have warnings about few examples
        assert len(parsed.warnings) > 0

    def test_schema_differences_detected(self, parser):
        """Test that schema differences are properly detected."""
        examples = [
            ExampleConfig(
                input={"name": "London", "extra_field": "value"},
                output={"city": "London"}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should detect that 'extra_field' was removed
        assert len(parsed.schema_differences) > 0

    def test_pattern_examples_included(self, parser):
        """Test that patterns include example value pairs."""
        examples = [
            ExampleConfig(
                input={"name": "London"},
                output={"city": "London"}
            ),
            ExampleConfig(
                input={"name": "Tokyo"},
                output={"city": "Tokyo"}
            )
        ]

        parsed = parser.parse_examples(examples)

        city_pattern = parsed.get_pattern_for_field("city")
        assert city_pattern is not None
        assert len(city_pattern.examples) > 0

    def test_complex_nested_structure(self, parser):
        """Test handling of complex nested structures."""
        examples = [
            ExampleConfig(
                input={
                    "data": {
                        "metrics": {
                            "temperature": 15.5
                        }
                    }
                },
                output={"temp": 15.5}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should handle deep nesting
        assert parsed.input_schema.is_nested
        temp_pattern = parsed.get_pattern_for_field("temp")
        assert temp_pattern is not None

    def test_null_value_handling(self, parser):
        """Test handling of null/None values."""
        examples = [
            ExampleConfig(
                input={"name": "London", "optional": None},
                output={"city": "London"}
            ),
            ExampleConfig(
                input={"name": "Tokyo", "optional": "value"},
                output={"city": "Tokyo"}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should handle None without errors
        assert parsed.num_examples == 2

    def test_pattern_confidence_calculation(self, parser):
        """Test confidence score calculation."""
        # Pattern that works for 2 out of 3 examples
        examples = [
            ExampleConfig(
                input={"temp": 15.5},
                output={"temperature": 15.5}
            ),
            ExampleConfig(
                input={"temp": 22.3},
                output={"temperature": 22.3}
            ),
            ExampleConfig(
                input={"temp": 18.0},
                output={"temperature": 18.0}
            )
        ]

        parsed = parser.parse_examples(examples)

        # All examples match - should be high confidence
        temp_pattern = parsed.get_pattern_for_field("temperature")
        assert temp_pattern is not None
        assert temp_pattern.confidence >= 0.9

    def test_multiple_output_fields(self, parser):
        """Test parsing with multiple output fields."""
        examples = [
            ExampleConfig(
                input={"name": "London", "temp": 15.5, "humidity": 80},
                output={"city": "London", "temperature": 15.5, "humidity_percent": 80}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should detect patterns for all output fields
        assert parsed.get_pattern_for_field("city") is not None
        assert parsed.get_pattern_for_field("temperature") is not None
        assert parsed.get_pattern_for_field("humidity_percent") is not None


class TestPatternDetection:
    """Test specific pattern detection logic."""

    @pytest.fixture
    def parser(self):
        """Create ExampleParser instance."""
        return ExampleParser(SchemaAnalyzer())

    def test_field_rename_detection(self, parser):
        """Test detection of field renames."""
        examples = [
            ExampleConfig(
                input={"old_name": "value1"},
                output={"new_name": "value1"}
            ),
            ExampleConfig(
                input={"old_name": "value2"},
                output={"new_name": "value2"}
            )
        ]

        parsed = parser.parse_examples(examples)
        pattern = parsed.get_pattern_for_field("new_name")

        assert pattern is not None
        assert pattern.confidence == 1.0

    def test_direct_copy_pattern(self, parser):
        """Test direct copy when field name unchanged."""
        examples = [
            ExampleConfig(
                input={"name": "London"},
                output={"name": "London"}
            ),
            ExampleConfig(
                input={"name": "Tokyo"},
                output={"name": "Tokyo"}
            )
        ]

        parsed = parser.parse_examples(examples)
        pattern = parsed.get_pattern_for_field("name")

        assert pattern is not None
        assert pattern.type == PatternType.FIELD_MAPPING
        assert "Direct copy" in pattern.transformation

    def test_calculation_pattern_detection(self, parser):
        """Test detection of calculated fields."""
        # This will be detected as COMPLEX since we don't do math analysis yet
        examples = [
            ExampleConfig(
                input={"celsius": 0},
                output={"fahrenheit": 32}
            ),
            ExampleConfig(
                input={"celsius": 100},
                output={"fahrenheit": 212}
            )
        ]

        parsed = parser.parse_examples(examples)
        pattern = parsed.get_pattern_for_field("fahrenheit")

        # Should detect some pattern (likely COMPLEX)
        assert pattern is not None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def parser(self):
        """Create ExampleParser instance."""
        return ExampleParser(SchemaAnalyzer())

    def test_empty_input_dict(self, parser):
        """Test handling of empty input dictionary."""
        examples = [
            ExampleConfig(
                input={},
                output={"constant": "value"}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should handle empty input
        assert parsed.num_examples == 1

    def test_empty_output_dict(self, parser):
        """Test handling of empty output dictionary."""
        examples = [
            ExampleConfig(
                input={"field": "value"},
                output={}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should handle empty output
        assert parsed.num_examples == 1
        assert len(parsed.patterns) == 0

    def test_single_example(self, parser):
        """Test behavior with single example."""
        examples = [
            ExampleConfig(
                input={"name": "London"},
                output={"city": "London"}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should still work but warn
        assert parsed.num_examples == 1
        assert len(parsed.warnings) > 0

    def test_array_with_mixed_types(self, parser):
        """Test handling of arrays with mixed types."""
        examples = [
            ExampleConfig(
                input={"items": [1, "string", 3.14]},
                output={"first": 1}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should handle without crashing
        assert parsed.num_examples == 1

    def test_deeply_nested_arrays(self, parser):
        """Test handling of deeply nested array structures."""
        examples = [
            ExampleConfig(
                input={"data": [[{"value": 42}]]},
                output={"result": 42}
            )
        ]

        parsed = parser.parse_examples(examples)

        # Should handle deep nesting
        assert parsed.input_schema.has_arrays
