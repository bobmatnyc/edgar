"""
Unit tests for PromptGenerator service.

Tests cover:
- Prompt generation from parsed examples
- Section creation
- Schema formatting
- Pattern detail generation
- Markdown and text output
"""

import pytest

from edgar_analyzer.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
    SchemaField,
)
from edgar_analyzer.services.prompt_generator import PromptGenerator


class TestPromptGenerator:
    """Test suite for PromptGenerator service."""

    @pytest.fixture
    def generator(self):
        """Create PromptGenerator instance."""
        return PromptGenerator()

    @pytest.fixture
    def sample_parsed_examples(self):
        """Create sample ParsedExamples for testing."""
        input_schema = Schema(
            fields=[
                SchemaField(
                    path="name",
                    field_type=FieldTypeEnum.STRING,
                    required=True,
                    nullable=False,
                    nested_level=0,
                    sample_values=["London", "Tokyo"]
                ),
                SchemaField(
                    path="main.temp",
                    field_type=FieldTypeEnum.FLOAT,
                    required=True,
                    nullable=False,
                    nested_level=1,
                    sample_values=[15.5, 22.3]
                )
            ],
            is_nested=True,
            has_arrays=False
        )

        output_schema = Schema(
            fields=[
                SchemaField(
                    path="city",
                    field_type=FieldTypeEnum.STRING,
                    required=True,
                    nullable=False,
                    nested_level=0,
                    sample_values=["London", "Tokyo"]
                ),
                SchemaField(
                    path="temperature_c",
                    field_type=FieldTypeEnum.FLOAT,
                    required=True,
                    nullable=False,
                    nested_level=0,
                    sample_values=[15.5, 22.3]
                )
            ],
            is_nested=False,
            has_arrays=False
        )

        patterns = [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="name",
                target_path="city",
                transformation="Direct copy with rename",
                examples=[("London", "London"), ("Tokyo", "Tokyo")],
                source_type=FieldTypeEnum.STRING,
                target_type=FieldTypeEnum.STRING
            ),
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=1.0,
                source_path="main.temp",
                target_path="temperature_c",
                transformation="Extract nested field 'temp' from 'main' object",
                examples=[({"temp": 15.5}, 15.5), ({"temp": 22.3}, 22.3)],
                source_type=FieldTypeEnum.FLOAT,
                target_type=FieldTypeEnum.FLOAT
            )
        ]

        return ParsedExamples(
            input_schema=input_schema,
            output_schema=output_schema,
            patterns=patterns,
            num_examples=2,
            warnings=[]
        )

    def test_generate_prompt_basic(self, generator, sample_parsed_examples):
        """Test basic prompt generation."""
        prompt = generator.generate_prompt(sample_parsed_examples)

        assert prompt is not None
        assert len(prompt.sections) > 0
        assert prompt.metadata["num_patterns"] == 2
        assert prompt.metadata["num_examples"] == 2

    def test_prompt_has_required_sections(self, generator, sample_parsed_examples):
        """Test that prompt has all required sections."""
        prompt = generator.generate_prompt(sample_parsed_examples)

        section_titles = [s.title for s in prompt.sections]

        # Should have these key sections
        assert any("Example Parser" in t for t in section_titles)
        assert any("Input Schema" in t for t in section_titles)
        assert any("Output Schema" in t for t in section_titles)
        assert any("Pattern" in t for t in section_titles)
        assert any("Requirements" in t for t in section_titles)

    def test_to_text_output(self, generator, sample_parsed_examples):
        """Test conversion to plain text."""
        prompt = generator.generate_prompt(sample_parsed_examples)
        text = prompt.to_text()

        assert text is not None
        assert len(text) > 0
        assert "Input Schema" in text
        assert "Output Schema" in text

    def test_to_markdown_output(self, generator, sample_parsed_examples):
        """Test conversion to Markdown."""
        prompt = generator.generate_prompt(sample_parsed_examples)
        markdown = prompt.to_markdown()

        assert markdown is not None
        assert len(markdown) > 0
        assert "##" in markdown  # Should have markdown headers

    def test_schema_formatting(self, generator):
        """Test schema formatting in prompt."""
        schema = Schema(
            fields=[
                SchemaField(
                    path="field1",
                    field_type=FieldTypeEnum.STRING,
                    required=True,
                    nullable=False,
                    nested_level=0,
                    sample_values=["value1"]
                ),
                SchemaField(
                    path="field2",
                    field_type=FieldTypeEnum.INTEGER,
                    required=False,
                    nullable=True,
                    nested_level=0,
                    sample_values=[42]
                )
            ]
        )

        section = generator._create_input_schema_section(schema)

        assert section is not None
        assert "field1" in section.content
        assert "field2" in section.content
        assert "Optional" in section.content  # field2 is optional

    def test_pattern_detail_sections(self, generator, sample_parsed_examples):
        """Test pattern detail section generation."""
        prompt = generator.generate_prompt(sample_parsed_examples)

        # Should have detail sections for each pattern
        pattern_sections = [s for s in prompt.sections if "Pattern" in s.title and ":" in s.title]
        assert len(pattern_sections) == 2

    def test_pattern_confidence_shown(self, generator, sample_parsed_examples):
        """Test that pattern confidence is shown in prompt."""
        prompt = generator.generate_prompt(sample_parsed_examples)
        text = prompt.to_text()

        # Should show confidence percentage
        assert "100%" in text or "Confidence" in text

    def test_pattern_examples_included(self, generator, sample_parsed_examples):
        """Test that pattern examples are included in prompt."""
        prompt = generator.generate_prompt(sample_parsed_examples)
        text = prompt.to_text()

        # Should include example values
        assert "London" in text or "Tokyo" in text

    def test_implementation_requirements_section(self, generator, sample_parsed_examples):
        """Test implementation requirements section."""
        prompt = generator.generate_prompt(sample_parsed_examples)

        req_section = next(
            (s for s in prompt.sections if "Requirements" in s.title),
            None
        )

        assert req_section is not None
        assert "def transform" in req_section.content
        assert "type hints" in req_section.content.lower()

    def test_warnings_section_created(self, generator):
        """Test warnings section creation when warnings present."""
        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=[],
            num_examples=1,
            warnings=["Warning 1", "Warning 2"]
        )

        prompt = generator.generate_prompt(parsed)

        warning_section = next(
            (s for s in prompt.sections if "Warning" in s.title),
            None
        )

        assert warning_section is not None
        assert "Warning 1" in warning_section.content

    def test_no_warnings_section_when_none(self, generator, sample_parsed_examples):
        """Test no warnings section when no warnings."""
        prompt = generator.generate_prompt(sample_parsed_examples)

        warning_sections = [s for s in prompt.sections if "Warning" in s.title]
        assert len(warning_sections) == 0

    def test_high_confidence_patterns_highlighted(self, generator):
        """Test that high confidence patterns are highlighted."""
        patterns = [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=0.95,
                source_path="src",
                target_path="dest",
                transformation="Map field",
                examples=[("a", "a")],
                source_type=FieldTypeEnum.STRING,
                target_type=FieldTypeEnum.STRING
            )
        ]

        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=patterns,
            num_examples=1
        )

        prompt = generator.generate_prompt(parsed)
        text = prompt.to_text()

        # Should mention high confidence
        assert "95%" in text or "high" in text.lower()

    def test_implementation_guidance_provided(self, generator):
        """Test that implementation guidance is provided for patterns."""
        pattern = Pattern(
            type=PatternType.ARRAY_FIRST,
            confidence=1.0,
            source_path="items[0]",
            target_path="first_item",
            transformation="Extract first element",
            examples=[([1, 2, 3], 1)],
            source_type=FieldTypeEnum.LIST,
            target_type=FieldTypeEnum.INTEGER
        )

        guidance = generator._get_implementation_guidance(pattern)

        assert len(guidance) > 0
        assert any("array" in g.lower() for g in guidance)

    def test_type_safety_indication(self, generator):
        """Test that type safety is indicated for patterns."""
        # Safe conversion
        safe_pattern = Pattern(
            type=PatternType.TYPE_CONVERSION,
            confidence=1.0,
            source_path="num",
            target_path="num",
            transformation="int to str",
            examples=[(42, "42")],
            source_type=FieldTypeEnum.INTEGER,
            target_type=FieldTypeEnum.STRING
        )

        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=[safe_pattern],
            num_examples=1
        )

        prompt = generator.generate_prompt(parsed)
        text = prompt.to_text()

        # Should mention type conversion
        assert "Type Conversion" in text or "int" in text

    def test_project_name_included(self, generator, sample_parsed_examples):
        """Test that project name is included in prompt."""
        prompt = generator.generate_prompt(sample_parsed_examples, project_name="weather_api")

        assert prompt.metadata["project_name"] == "weather_api"
        text = prompt.to_text()
        assert "weather_api" in text

    def test_section_ordering(self, generator, sample_parsed_examples):
        """Test that sections are properly ordered."""
        prompt = generator.generate_prompt(sample_parsed_examples)

        # Get section orders
        orders = [s.order for s in prompt.sections]

        # Should be in ascending order
        assert orders == sorted(orders)

    def test_nested_schema_indication(self, generator):
        """Test that nested schemas are indicated."""
        schema = Schema(
            fields=[
                SchemaField(
                    path="nested.field",
                    field_type=FieldTypeEnum.STRING,
                    nested_level=1,
                    sample_values=["value"]
                )
            ],
            is_nested=True
        )

        section = generator._create_input_schema_section(schema)

        # Should indicate nesting
        assert "nested" in section.content.lower() or "." in section.content

    def test_array_schema_indication(self, generator):
        """Test that array schemas are indicated."""
        schema = Schema(
            fields=[
                SchemaField(
                    path="items[0]",
                    field_type=FieldTypeEnum.STRING,
                    is_array=True,
                    array_item_type=FieldTypeEnum.STRING,
                    sample_values=["value"]
                )
            ],
            has_arrays=True
        )

        section = generator._create_input_schema_section(schema)

        # Should indicate arrays
        assert "List" in section.content or "[" in section.content


class TestPromptGeneration:
    """Integration-style tests for complete prompt generation."""

    @pytest.fixture
    def generator(self):
        """Create PromptGenerator instance."""
        return PromptGenerator()

    def test_complete_weather_api_prompt(self, generator):
        """Test generating complete prompt for weather API example."""
        # Simulate weather API transformation
        input_schema = Schema(
            fields=[
                SchemaField(path="name", field_type=FieldTypeEnum.STRING, nested_level=0),
                SchemaField(path="main.temp", field_type=FieldTypeEnum.FLOAT, nested_level=1),
                SchemaField(path="weather[0].description", field_type=FieldTypeEnum.STRING, nested_level=1, is_array=True)
            ],
            is_nested=True,
            has_arrays=True
        )

        output_schema = Schema(
            fields=[
                SchemaField(path="city", field_type=FieldTypeEnum.STRING, nested_level=0),
                SchemaField(path="temperature_c", field_type=FieldTypeEnum.FLOAT, nested_level=0),
                SchemaField(path="conditions", field_type=FieldTypeEnum.STRING, nested_level=0)
            ]
        )

        patterns = [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="name",
                target_path="city",
                transformation="Direct copy",
                examples=[("London", "London")]
            ),
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=1.0,
                source_path="main.temp",
                target_path="temperature_c",
                transformation="Extract nested temp",
                examples=[({"temp": 15.5}, 15.5)]
            ),
            Pattern(
                type=PatternType.ARRAY_FIRST,
                confidence=1.0,
                source_path="weather[0].description",
                target_path="conditions",
                transformation="First array element",
                examples=[([{"description": "rain"}], "rain")]
            )
        ]

        parsed = ParsedExamples(
            input_schema=input_schema,
            output_schema=output_schema,
            patterns=patterns,
            num_examples=3
        )

        prompt = generator.generate_prompt(parsed, project_name="weather_api")

        # Verify complete prompt structure
        assert len(prompt.sections) >= 5
        assert prompt.metadata["num_patterns"] == 3

        # Verify text output is comprehensive
        text = prompt.to_text()
        assert len(text) > 500  # Should be substantial
        assert "weather_api" in text
        assert "city" in text
        assert "temperature_c" in text
        assert "conditions" in text
