"""
Integration tests for Example Parser system.

Tests the complete flow from example parsing through prompt generation,
using realistic scenarios like the Weather API proof-of-concept.
"""

import pytest

from edgar_analyzer.models.project_config import ExampleConfig
from edgar_analyzer.services.example_parser import ExampleParser
from edgar_analyzer.services.prompt_generator import PromptGenerator
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer


class TestWeatherAPIIntegration:
    """Integration tests using Weather API as example."""

    @pytest.fixture
    def weather_examples(self):
        """Create realistic Weather API examples."""
        return [
            ExampleConfig(
                input={
                    "coord": {"lon": -0.13, "lat": 51.51},
                    "weather": [
                        {
                            "id": 300,
                            "main": "Drizzle",
                            "description": "light intensity drizzle",
                            "icon": "09d",
                        }
                    ],
                    "main": {
                        "temp": 15.5,
                        "feels_like": 14.2,
                        "temp_min": 14,
                        "temp_max": 17,
                        "pressure": 1012,
                        "humidity": 82,
                    },
                    "name": "London",
                },
                output={
                    "city": "London",
                    "temperature_c": 15.5,
                    "humidity_percent": 82,
                    "conditions": "light intensity drizzle",
                },
                description="London weather with drizzle",
            ),
            ExampleConfig(
                input={
                    "coord": {"lon": 139.69, "lat": 35.69},
                    "weather": [
                        {
                            "id": 800,
                            "main": "Clear",
                            "description": "clear sky",
                            "icon": "01d",
                        }
                    ],
                    "main": {
                        "temp": 22.3,
                        "feels_like": 21.8,
                        "temp_min": 21,
                        "temp_max": 24,
                        "pressure": 1015,
                        "humidity": 65,
                    },
                    "name": "Tokyo",
                },
                output={
                    "city": "Tokyo",
                    "temperature_c": 22.3,
                    "humidity_percent": 65,
                    "conditions": "clear sky",
                },
                description="Tokyo weather with clear skies",
            ),
            ExampleConfig(
                input={
                    "coord": {"lon": -74.01, "lat": 40.71},
                    "weather": [
                        {
                            "id": 500,
                            "main": "Rain",
                            "description": "light rain",
                            "icon": "10d",
                        }
                    ],
                    "main": {
                        "temp": 18.0,
                        "feels_like": 17.5,
                        "temp_min": 16,
                        "temp_max": 20,
                        "pressure": 1010,
                        "humidity": 75,
                    },
                    "name": "New York",
                },
                output={
                    "city": "New York",
                    "temperature_c": 18.0,
                    "humidity_percent": 75,
                    "conditions": "light rain",
                },
                description="New York weather with light rain",
            ),
        ]

    def test_complete_parsing_flow(self, weather_examples):
        """Test complete flow from examples to patterns."""
        # Create services
        schema_analyzer = SchemaAnalyzer()
        parser = ExampleParser(schema_analyzer)

        # Parse examples
        parsed = parser.parse_examples(weather_examples)

        # Verify parsing results
        assert parsed.num_examples == 3
        assert len(parsed.patterns) > 0
        assert len(parsed.input_schema.fields) > 0
        assert len(parsed.output_schema.fields) == 4  # city, temp, humidity, conditions

        # Verify input schema
        assert parsed.input_schema.is_nested
        assert parsed.input_schema.has_arrays

        # Verify output schema
        assert not parsed.output_schema.is_nested
        assert not parsed.output_schema.has_arrays

        # Verify patterns found for each output field
        assert parsed.get_pattern_for_field("city") is not None
        assert parsed.get_pattern_for_field("temperature_c") is not None
        assert parsed.get_pattern_for_field("humidity_percent") is not None
        assert parsed.get_pattern_for_field("conditions") is not None

    def test_pattern_accuracy(self, weather_examples):
        """Test that detected patterns are accurate."""
        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(weather_examples)

        # City pattern - should be direct mapping with rename
        city_pattern = parsed.get_pattern_for_field("city")
        assert city_pattern is not None
        assert city_pattern.confidence == 1.0
        assert "name" in city_pattern.source_path.lower()

        # Temperature pattern - should be nested extraction
        temp_pattern = parsed.get_pattern_for_field("temperature_c")
        assert temp_pattern is not None
        assert temp_pattern.confidence == 1.0
        assert "main.temp" in temp_pattern.source_path

        # Conditions pattern - should be array first element
        conditions_pattern = parsed.get_pattern_for_field("conditions")
        assert conditions_pattern is not None
        # Should extract from weather array's description field

    def test_prompt_generation_from_weather_examples(self, weather_examples):
        """Test generating complete prompt from weather examples."""
        # Parse examples
        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(weather_examples)

        # Generate prompt
        generator = PromptGenerator()
        prompt = generator.generate_prompt(parsed, project_name="weather_api")

        # Verify prompt structure
        assert len(prompt.sections) >= 5
        assert prompt.metadata["num_patterns"] >= 4
        assert prompt.metadata["num_examples"] == 3

        # Verify prompt content
        text = prompt.to_text()
        assert "weather_api" in text
        assert "city" in text
        assert "temperature_c" in text
        assert "humidity_percent" in text
        assert "conditions" in text

        # Verify implementation guidance
        assert "def transform" in text
        assert "Dict[str, Any]" in text

    def test_markdown_output_quality(self, weather_examples):
        """Test quality of Markdown output."""
        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(weather_examples)

        generator = PromptGenerator()
        prompt = generator.generate_prompt(parsed)

        markdown = prompt.to_markdown()

        # Should have proper markdown structure
        assert "##" in markdown  # Section headers
        assert "**" in markdown  # Bold text
        assert "```" in markdown  # Code blocks

        # Should be substantial
        assert len(markdown) > 1000

    def test_high_confidence_patterns_only(self, weather_examples):
        """Test that all patterns are high confidence for good examples."""
        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(weather_examples)

        # With 3 consistent examples, all patterns should be high confidence
        high_conf = parsed.high_confidence_patterns
        assert len(high_conf) >= 3  # At least 3 fields should have high confidence

        # No low confidence patterns
        low_conf = parsed.low_confidence_patterns
        assert len(low_conf) == 0

    def test_schema_differences_identified(self, weather_examples):
        """Test that schema differences are properly identified."""
        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(weather_examples)

        # Should identify differences between input and output
        assert len(parsed.schema_differences) > 0

        # Should detect removed fields (coord, weather.id, etc.)
        removed = [
            d for d in parsed.schema_differences if d.difference_type == "removed"
        ]
        assert len(removed) > 0

        # Should detect added fields are actually transformed (not truly "added")
        # or detect field renames


class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""

    def test_minimal_example_set(self):
        """Test with minimal example set (single example)."""
        examples = [ExampleConfig(input={"field": "value"}, output={"result": "value"})]

        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(examples)

        # Should still work but warn
        assert parsed.num_examples == 1
        assert len(parsed.warnings) > 0

        # Should still generate prompt
        generator = PromptGenerator()
        prompt = generator.generate_prompt(parsed)
        assert len(prompt.sections) > 0

    def test_complex_nested_arrays(self):
        """Test with complex nested arrays."""
        examples = [
            ExampleConfig(
                input={
                    "results": [
                        {
                            "items": [
                                {"name": "item1", "value": 10},
                                {"name": "item2", "value": 20},
                            ]
                        }
                    ]
                },
                output={"first_item_name": "item1", "first_item_value": 10},
            )
        ]

        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(examples)

        # Should handle complex nesting
        assert parsed.input_schema.is_nested
        assert parsed.input_schema.has_arrays

    def test_type_conversion_detection(self):
        """Test detection of type conversions."""
        examples = [
            ExampleConfig(
                input={"temperature": "15.5", "count": "42"},
                output={"temperature": 15.5, "count": 42},
            ),
            ExampleConfig(
                input={"temperature": "22.3", "count": "100"},
                output={"temperature": 22.3, "count": 100},
            ),
        ]

        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(examples)

        # Should detect type conversions
        patterns = parsed.patterns
        assert len(patterns) == 2

        # Generate prompt should mention type conversions
        generator = PromptGenerator()
        prompt = generator.generate_prompt(parsed)
        text = prompt.to_text()

        # Should mention type handling
        assert "type" in text.lower() or "convert" in text.lower()

    def test_missing_field_handling(self):
        """Test handling when field missing in some examples."""
        examples = [
            ExampleConfig(
                input={"required": "value", "optional": "present"},
                output={"result": "value"},
            ),
            ExampleConfig(
                input={"required": "value"},  # optional missing
                output={"result": "value"},
            ),
        ]

        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(examples)

        # Should handle missing fields
        optional_field = parsed.input_schema.get_field("optional")
        assert optional_field is not None
        assert not optional_field.required


class TestEndToEndScenarios:
    """End-to-end integration scenarios."""

    def test_weather_api_full_workflow(self):
        """Test complete Weather API workflow end-to-end."""
        # Step 1: Define examples
        examples = [
            ExampleConfig(
                input={
                    "name": "London",
                    "main": {"temp": 15.5, "humidity": 82},
                    "weather": [{"description": "rain"}],
                },
                output={
                    "city": "London",
                    "temperature_c": 15.5,
                    "humidity_percent": 82,
                    "conditions": "rain",
                },
            ),
            ExampleConfig(
                input={
                    "name": "Tokyo",
                    "main": {"temp": 22.3, "humidity": 65},
                    "weather": [{"description": "clear"}],
                },
                output={
                    "city": "Tokyo",
                    "temperature_c": 22.3,
                    "humidity_percent": 65,
                    "conditions": "clear",
                },
            ),
        ]

        # Step 2: Parse examples
        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(examples)

        # Step 3: Verify patterns
        assert parsed.num_examples == 2
        assert len(parsed.high_confidence_patterns) >= 3

        # Step 4: Generate prompt
        generator = PromptGenerator()
        prompt = generator.generate_prompt(parsed, project_name="weather_api")

        # Step 5: Verify prompt quality
        markdown = prompt.to_markdown()

        # Verify comprehensive prompt
        assert "Input Schema" in markdown
        assert "Output Schema" in markdown
        assert "Pattern" in markdown
        assert "Implementation" in markdown

        # Verify all output fields covered
        assert "city" in markdown
        assert "temperature_c" in markdown
        assert "humidity_percent" in markdown
        assert "conditions" in markdown

        # Verify implementation guidance
        assert "def transform" in markdown
        assert "Dict[str, Any]" in markdown

        # Success criteria
        assert len(markdown) > 1500  # Substantial prompt
        assert len(parsed.warnings) <= 1  # Minimal warnings
        assert len(parsed.high_confidence_patterns) == len(
            parsed.patterns
        )  # All high conf

    def test_save_prompt_to_file(self, tmp_path):
        """Test saving generated prompt to file."""
        examples = [ExampleConfig(input={"field": "value"}, output={"result": "value"})]

        parser = ExampleParser(SchemaAnalyzer())
        parsed = parser.parse_examples(examples)

        generator = PromptGenerator()
        prompt = generator.generate_prompt(parsed)

        # Save to file
        output_file = tmp_path / "prompt.md"
        output_file.write_text(prompt.to_markdown())

        # Verify file created and readable
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 100
        assert "##" in content
