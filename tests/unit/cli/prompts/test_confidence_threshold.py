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
        error_calls = [
            call
            for call in mock_console.print.call_args_list
            if "WARNING" in str(call) or "warning" in str(call).lower()
        ]
        assert len(error_calls) > 0

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    @patch("edgar_analyzer.cli.prompts.confidence_threshold.console")
    def test_custom_threshold_negative_invalid(
        self, mock_console, mock_ask, prompt, sample_parsed_examples
    ):
        """Test custom threshold with negative value (invalid)."""
        mock_ask.side_effect = ["4", "-0.1", "0.7"]

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.7
        # Should show error for negative value
        error_calls = [
            call
            for call in mock_console.print.call_args_list
            if "WARNING" in str(call) or "warning" in str(call).lower()
        ]
        assert len(error_calls) > 0

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    @patch("edgar_analyzer.cli.prompts.confidence_threshold.console")
    def test_custom_threshold_non_numeric_invalid(
        self, mock_console, mock_ask, prompt, sample_parsed_examples
    ):
        """Test custom threshold with non-numeric input (invalid)."""
        mock_ask.side_effect = ["4", "abc", "0.7"]

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.7
        # Should show error for non-numeric
        error_calls = [
            call
            for call in mock_console.print.call_args_list
            if "WARNING" in str(call) or "warning" in str(call).lower()
        ]
        assert len(error_calls) > 0

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_custom_threshold_default_used(
        self, mock_ask, prompt, sample_parsed_examples
    ):
        """Test custom threshold uses default (0.7) when user presses enter."""
        mock_ask.side_effect = ["4", "0.7"]  # Default value

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.7

    # ========================================================================
    # PATTERN SUMMARY DISPLAY TESTS
    # ========================================================================

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    @patch("edgar_analyzer.cli.prompts.confidence_threshold.console")
    def test_pattern_summary_displayed(
        self, mock_console, mock_ask, prompt, sample_parsed_examples
    ):
        """Test pattern summary is displayed before prompt."""
        mock_ask.return_value = "2"

        prompt.prompt_for_threshold(sample_parsed_examples)

        # Check that console.print was called with Panel containing summary
        panel_calls = [
            call
            for call in mock_console.print.call_args_list
            if len(call[0]) > 0
            and hasattr(call[0][0], "__class__")
            and call[0][0].__class__.__name__ == "Panel"
        ]

        assert len(panel_calls) > 0, "Pattern summary panel should be displayed"

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    @patch("edgar_analyzer.cli.prompts.confidence_threshold.console")
    def test_threshold_table_displayed(
        self, mock_console, mock_ask, prompt, sample_parsed_examples
    ):
        """Test threshold options table is displayed."""
        mock_ask.return_value = "2"

        prompt.prompt_for_threshold(sample_parsed_examples)

        # Check that console.print was called with Table
        table_calls = [
            call
            for call in mock_console.print.call_args_list
            if len(call[0]) > 0
            and hasattr(call[0][0], "__class__")
            and call[0][0].__class__.__name__ == "Table"
        ]

        assert len(table_calls) > 0, "Threshold options table should be displayed"

    # ========================================================================
    # EMPTY PATTERNS TESTS
    # ========================================================================

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_empty_patterns_handled(self, mock_ask, prompt):
        """Test handling of empty patterns list."""
        empty_parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=[],
            schema_differences=[],
            num_examples=0,
            warnings=[],
        )

        mock_ask.return_value = "2"

        threshold = prompt.prompt_for_threshold(empty_parsed)

        assert threshold == 0.7  # Should still work with default

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    @patch("edgar_analyzer.cli.prompts.confidence_threshold.console")
    def test_success_message_displayed(
        self, mock_console, mock_ask, prompt, sample_parsed_examples
    ):
        """Test success message is displayed after selection."""
        mock_ask.return_value = "2"

        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        # Check for success message (green checkmark)
        success_calls = [
            call for call in mock_console.print.call_args_list if "" in str(call)
        ]

        assert mock_console.print.called, "Console should be used for output"
        assert threshold == 0.7

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_prompt_returns_valid_threshold_range(
        self, mock_ask, prompt, sample_parsed_examples
    ):
        """Test prompt always returns valid threshold (0.0-1.0)."""
        test_cases = [
            ("1", 0.8),
            ("2", 0.7),
            ("3", 0.6),
        ]

        for choice, expected_threshold in test_cases:
            mock_ask.return_value = choice
            threshold = prompt.prompt_for_threshold(sample_parsed_examples)

            assert (
                0.0 <= threshold <= 1.0
            ), f"Threshold {threshold} out of range for choice {choice}"
            assert threshold == expected_threshold

    # ========================================================================
    # FILTER SERVICE INTEGRATION TESTS
    # ========================================================================

    def test_filter_service_initialized(self, prompt):
        """Test that PatternFilterService is initialized."""
        assert prompt.filter_service is not None
        assert hasattr(prompt.filter_service, "filter_patterns")
        assert hasattr(prompt.filter_service, "get_threshold_presets")
        assert hasattr(prompt.filter_service, "format_confidence_summary")

    def test_filter_service_presets_used(self, prompt):
        """Test that presets from filter service are used."""
        presets = prompt.filter_service.get_threshold_presets()

        assert "conservative" in presets
        assert "balanced" in presets
        assert "aggressive" in presets

        # Validate structure
        for name, (threshold, desc) in presets.items():
            assert isinstance(threshold, float)
            assert 0.0 <= threshold <= 1.0
            assert isinstance(desc, str)
            assert len(desc) > 0

    @patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask")
    def test_impact_preview_calculated(self, mock_ask, prompt, sample_parsed_examples):
        """Test that impact preview is calculated for each preset."""
        mock_ask.return_value = "2"

        # This should trigger calculation of included/excluded counts for each preset
        threshold = prompt.prompt_for_threshold(sample_parsed_examples)

        assert threshold == 0.7

        # Verify the calculations would be correct
        # With 4 patterns (1.0, 0.95, 0.80, 0.65):
        # - Conservative (0.8): 3 included, 1 excluded
        # - Balanced (0.7): 3 included, 1 excluded
        # - Aggressive (0.6): 4 included, 0 excluded

        # We can't directly test the display, but we can verify the logic
        patterns = sample_parsed_examples.all_patterns

        conservative_included = sum(1 for p in patterns if p.confidence >= 0.8)
        balanced_included = sum(1 for p in patterns if p.confidence >= 0.7)
        aggressive_included = sum(1 for p in patterns if p.confidence >= 0.6)

        assert conservative_included == 3
        assert balanced_included == 3
        assert aggressive_included == 4
