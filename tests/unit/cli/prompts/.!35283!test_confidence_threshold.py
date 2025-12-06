"""Unit tests for ConfidenceThresholdPrompt.

Tests cover:
- Preset selection (options 1, 2, 3)
- Custom threshold input (option 4)
- Invalid custom input handling
- Default behavior
- Edge cases
- Pattern summary display
- Threshold validation
"""

from unittest.mock import MagicMock, patch

import pytest

from edgar_analyzer.cli.prompts.confidence_threshold import (
    ConfidenceThresholdPrompt,
)
from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
    SchemaField,
)


class TestConfidenceThresholdPrompt:
    """Test suite for ConfidenceThresholdPrompt CLI component."""

    @pytest.fixture
    def prompt(self):
        """Create ConfidenceThresholdPrompt instance."""
        return ConfidenceThresholdPrompt()

    @pytest.fixture
    def sample_patterns(self):
        """Create sample patterns with varying confidence levels."""
        return [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="field1",
                target_path="output1",
                transformation="Perfect confidence",
                source_type=FieldTypeEnum.STRING,
                target_type=FieldTypeEnum.STRING,
            ),
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=0.95,
                source_path="main.field2",
                target_path="output2",
                transformation="Very high confidence",
                source_type=FieldTypeEnum.FLOAT,
                target_type=FieldTypeEnum.FLOAT,
            ),
            Pattern(
                type=PatternType.ARRAY_FIRST,
                confidence=0.80,
                source_path="array[0]",
                target_path="output3",
                transformation="Medium-high confidence",
                source_type=FieldTypeEnum.STRING,
                target_type=FieldTypeEnum.STRING,
            ),
            Pattern(
                type=PatternType.CALCULATION,
                confidence=0.65,
                source_path="value",
                target_path="result",
                transformation="Low confidence",
                source_type=FieldTypeEnum.FLOAT,
                target_type=FieldTypeEnum.FLOAT,
            ),
        ]

    @pytest.fixture
    def sample_parsed_examples(self, sample_patterns):
        """Create ParsedExamples with sample patterns."""
        return ParsedExamples(
            input_schema=Schema(
                fields=[
                    SchemaField(path="field1", field_type=FieldTypeEnum.STRING),
                    SchemaField(
                        path="main.field2",
                        field_type=FieldTypeEnum.FLOAT,
                        nested_level=1,
                    ),
                ]
            ),
            output_schema=Schema(
                fields=[
                    SchemaField(path="output1", field_type=FieldTypeEnum.STRING),
                    SchemaField(path="output2", field_type=FieldTypeEnum.FLOAT),
                ]
            ),
            patterns=sample_patterns,
            schema_differences=[],
            num_examples=3,
            warnings=[],
        )

    # ========================================================================
    # PRESET SELECTION TESTS
    # ========================================================================

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_preset_selection_conservative(
        self, mock_ask, prompt, sample_parsed_examples
    ):
        """Test selecting conservative preset (option 1)."""
        mock_ask.return_value = "1"

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.8
        mock_ask.assert_called_once()

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_preset_selection_balanced(self, mock_ask, prompt, sample_parsed_examples):
        """Test selecting balanced preset (option 2, default)."""
        mock_ask.return_value = "2"

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.7
        mock_ask.assert_called_once()

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_preset_selection_aggressive(
        self, mock_ask, prompt, sample_parsed_examples
    ):
        """Test selecting aggressive preset (option 3)."""
        mock_ask.return_value = "3"

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.6
        mock_ask.assert_called_once()

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_default_preset_balanced(self, mock_ask, prompt, sample_parsed_examples):
        """Test default preset is balanced (0.7)."""
        mock_ask.return_value = "2"

        threshold = prompt.prompt_for_threshold(
            sample_parsed_examples, default="balanced"
        )

        assert threshold == 0.7

    # ========================================================================
    # CUSTOM THRESHOLD TESTS
    # ========================================================================

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_custom_threshold_valid(self, mock_ask, prompt, sample_parsed_examples):
        """Test custom threshold with valid input."""
        # First call returns "4" (custom), second returns threshold value
        mock_ask.side_effect = ["4", "0.75"]

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.75
        assert mock_ask.call_count == 2

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_custom_threshold_boundary_low(
        self, mock_ask, prompt, sample_parsed_examples
    ):
        """Test custom threshold at lower boundary (0.0)."""
        mock_ask.side_effect = ["4", "0.0"]

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.0

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_custom_threshold_boundary_high(
        self, mock_ask, prompt, sample_parsed_examples
    ):
        """Test custom threshold at upper boundary (1.0)."""
        mock_ask.side_effect = ["4", "1.0"]

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 1.0

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    @patch("edgar_analyzer.cli.prompts.confidence_threshold.console")
    def test_custom_threshold_invalid_then_valid(
        self, mock_console, mock_ask, prompt, sample_parsed_examples
    ):
        """Test custom threshold with invalid then valid input."""
        # First call: "4" (custom)
        # Second call: "1.5" (invalid, > 1.0)
        # Third call: "0.7" (valid)
        mock_ask.side_effect = ["4", "1.5", "0.7"]

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.7
        assert mock_ask.call_count == 3

        # Should have printed error message
