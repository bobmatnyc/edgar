"""Unit tests for PatternFilterService.

Tests cover:
- Pattern filtering by various thresholds (0.5, 0.7, 0.9)
- Preset threshold options validation
- Confidence summary formatting (empty, all high, all low, mixed)
- Edge cases (threshold boundaries 0.0, 1.0, negative, > 1.0)
- Error handling (invalid thresholds)
- FilteredParsedExamples properties (high/medium/low confidence)
- Warning generation for excluded patterns
"""

import pytest

from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
    SchemaField,
)
from extract_transform_platform.services.analysis.pattern_filter import (
    PatternFilterService,
)


class TestPatternFilterService:
    """Test suite for PatternFilterService."""

    @pytest.fixture
    def filter_service(self):
        """Create PatternFilterService instance."""
        return PatternFilterService()

    @pytest.fixture
    def sample_patterns(self):
        """Create sample patterns with varying confidence levels."""
        return [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="field1",
                target_path="output1",
                transformation="Direct copy",
                source_type=FieldTypeEnum.STRING,
                target_type=FieldTypeEnum.STRING,
            ),
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=0.95,
                source_path="main.field2",
                target_path="output2",
                transformation="Extract nested",
                source_type=FieldTypeEnum.FLOAT,
                target_type=FieldTypeEnum.FLOAT,
            ),
            Pattern(
                type=PatternType.ARRAY_FIRST,
                confidence=0.90,
                source_path="array[0]",
                target_path="output3",
                transformation="First element",
                source_type=FieldTypeEnum.STRING,
                target_type=FieldTypeEnum.STRING,
            ),
            Pattern(
                type=PatternType.FIELD_RENAME,
                confidence=0.80,
                source_path="old_name",
                target_path="new_name",
                transformation="Rename field",
                source_type=FieldTypeEnum.INTEGER,
                target_type=FieldTypeEnum.INTEGER,
            ),
            Pattern(
                type=PatternType.CALCULATION,
                confidence=0.65,
                source_path="value",
                target_path="result",
                transformation="Calculate",
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
                    SchemaField(
                        path="array", field_type=FieldTypeEnum.LIST, is_array=True
                    ),
                ]
            ),
            output_schema=Schema(
                fields=[
                    SchemaField(path="output1", field_type=FieldTypeEnum.STRING),
                    SchemaField(path="output2", field_type=FieldTypeEnum.FLOAT),
                    SchemaField(path="output3", field_type=FieldTypeEnum.STRING),
                ]
            ),
            patterns=sample_patterns,
            schema_differences=[],
            num_examples=3,
            warnings=[],
        )

    # ========================================================================
    # BASIC FILTERING TESTS
    # ========================================================================

    def test_filter_threshold_07_balanced(self, filter_service, sample_parsed_examples):
        """Test filtering with 0.7 threshold (balanced preset)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.7)

        assert filtered.confidence_threshold == 0.7
        assert len(filtered.all_patterns) == 5  # All patterns preserved
        assert len(filtered.included_patterns) == 4  # >= 0.7: 1.0, 0.95, 0.90, 0.80
        assert len(filtered.excluded_patterns) == 1  # < 0.7: 0.65

        # Verify included patterns meet threshold
        assert all(p.confidence >= 0.7 for p in filtered.included_patterns)

        # Verify excluded patterns below threshold
        assert all(p.confidence < 0.7 for p in filtered.excluded_patterns)

    def test_filter_threshold_09_strict(self, filter_service, sample_parsed_examples):
        """Test filtering with 0.9 threshold (very strict)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.9)

        assert filtered.confidence_threshold == 0.9
        assert len(filtered.included_patterns) == 3  # >= 0.9: 1.0, 0.95, 0.90
        assert len(filtered.excluded_patterns) == 2  # < 0.9: 0.80, 0.65

    def test_filter_threshold_08_conservative(
        self, filter_service, sample_parsed_examples
    ):
        """Test filtering with 0.8 threshold (conservative preset)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.8)

        assert filtered.confidence_threshold == 0.8
        assert len(filtered.included_patterns) == 4  # >= 0.8: 1.0, 0.95, 0.90, 0.80
        assert len(filtered.excluded_patterns) == 1  # < 0.8: 0.65

    def test_filter_threshold_06_aggressive(
        self, filter_service, sample_parsed_examples
    ):
        """Test filtering with 0.6 threshold (aggressive preset)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.6)

        assert filtered.confidence_threshold == 0.6
        assert len(filtered.included_patterns) == 5  # All patterns >= 0.6
        assert len(filtered.excluded_patterns) == 0

    def test_filter_threshold_05_very_lenient(
        self, filter_service, sample_parsed_examples
    ):
        """Test filtering with 0.5 threshold (very lenient)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.5)

        assert len(filtered.included_patterns) == 5  # All patterns included
        assert len(filtered.excluded_patterns) == 0

    # ========================================================================
    # EDGE CASE TESTS
    # ========================================================================

    def test_filter_threshold_00_minimum(self, filter_service, sample_parsed_examples):
        """Test filtering with 0.0 threshold (include everything)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.0)

        assert filtered.confidence_threshold == 0.0
        assert len(filtered.included_patterns) == 5  # All patterns
        assert len(filtered.excluded_patterns) == 0

    def test_filter_threshold_10_maximum(self, filter_service, sample_parsed_examples):
        """Test filtering with 1.0 threshold (perfect confidence only)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 1.0)

        assert filtered.confidence_threshold == 1.0
        assert len(filtered.included_patterns) == 1  # Only 1.0 confidence
        assert len(filtered.excluded_patterns) == 4

    def test_filter_invalid_threshold_negative(
        self, filter_service, sample_parsed_examples
    ):
        """Test filtering with negative threshold raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be in"):
            filter_service.filter_patterns(sample_parsed_examples, -0.1)

    def test_filter_invalid_threshold_over_one(
        self, filter_service, sample_parsed_examples
    ):
        """Test filtering with threshold > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be in"):
            filter_service.filter_patterns(sample_parsed_examples, 1.5)

    def test_filter_empty_patterns(self, filter_service):
        """Test filtering with no patterns."""
        empty_parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=[],
            schema_differences=[],
            num_examples=0,
            warnings=[],
        )

        filtered = filter_service.filter_patterns(empty_parsed, 0.7)

        assert len(filtered.all_patterns) == 0
        assert len(filtered.included_patterns) == 0
        assert len(filtered.excluded_patterns) == 0

    # ========================================================================
    # FILTERED PARSED EXAMPLES PROPERTIES TESTS
    # ========================================================================

    def test_filtered_high_confidence_patterns(
        self, filter_service, sample_parsed_examples
    ):
        """Test high_confidence_patterns property (>= 0.9)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.7)

        high = filtered.high_confidence_patterns
        assert len(high) == 3  # 1.0, 0.95, 0.90
        assert all(p.confidence >= 0.9 for p in high)

    def test_filtered_medium_confidence_patterns(
        self, filter_service, sample_parsed_examples
    ):
        """Test medium_confidence_patterns property (0.7-0.89)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.6)

        medium = filtered.medium_confidence_patterns
        assert len(medium) == 1  # 0.80
        assert all(0.7 <= p.confidence < 0.9 for p in medium)

    def test_filtered_low_confidence_patterns(
        self, filter_service, sample_parsed_examples
    ):
        """Test low_confidence_patterns property (< 0.7)."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.5)

        low = filtered.low_confidence_patterns
        assert len(low) == 1  # 0.65
        assert all(p.confidence < 0.7 for p in low)

    def test_filtered_patterns_alias(self, filter_service, sample_parsed_examples):
        """Test .patterns property is alias for .included_patterns."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.7)

        assert filtered.patterns == filtered.included_patterns
        assert len(filtered.patterns) == len(filtered.included_patterns)

    # ========================================================================
    # PRESET THRESHOLD OPTIONS TESTS
    # ========================================================================

    def test_get_threshold_presets(self, filter_service):
        """Test get_threshold_presets returns expected options."""
        presets = filter_service.get_threshold_presets()

        assert "conservative" in presets
        assert "balanced" in presets
        assert "aggressive" in presets

        # Validate structure
        assert presets["conservative"] == (0.8, "Only high confidence patterns (0.8+)")
        assert presets["balanced"] == (
            0.7,
            "Balance quality and coverage (0.7+) [RECOMMENDED]",
        )
        assert presets["aggressive"] == (
            0.6,
            "All patterns including lower confidence (0.6+)",
        )

    def test_presets_thresholds_values(self, filter_service):
        """Test preset threshold values are valid."""
        presets = filter_service.get_threshold_presets()

        for name, (threshold, desc) in presets.items():
            assert (
                0.0 <= threshold <= 1.0
            ), f"Preset {name} has invalid threshold {threshold}"
            assert isinstance(desc, str), f"Preset {name} has non-string description"
            assert len(desc) > 0, f"Preset {name} has empty description"

    # ========================================================================
    # CONFIDENCE SUMMARY FORMATTING TESTS
    # ========================================================================

    def test_format_confidence_summary_mixed(
        self, filter_service, sample_parsed_examples
    ):
        """Test format_confidence_summary with mixed confidence levels."""
        summary = filter_service.format_confidence_summary(sample_parsed_examples)

        assert "Detected 5 patterns:" in summary
        assert "3 high confidence" in summary
        assert "60%" in summary  # 3/5 = 60%
        assert "1 medium confidence" in summary
        assert "20%" in summary  # 1/5 = 20%, appears twice
        assert "1 low confidence" in summary

    def test_format_confidence_summary_empty(self, filter_service):
        """Test format_confidence_summary with no patterns."""
        empty_parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=[],
            schema_differences=[],
            num_examples=0,
            warnings=[],
        )

        summary = filter_service.format_confidence_summary(empty_parsed)
        assert summary == "No patterns detected."

    def test_format_confidence_summary_all_high(self, filter_service):
        """Test format_confidence_summary with all high confidence patterns."""
        high_patterns = [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=0.95,
                source_path="field1",
                target_path="output1",
                transformation="High confidence",
            ),
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=1.0,
                source_path="field2",
                target_path="output2",
                transformation="Perfect confidence",
            ),
        ]

        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=high_patterns,
            schema_differences=[],
            num_examples=2,
            warnings=[],
        )

        summary = filter_service.format_confidence_summary(parsed)
        assert "2 high confidence" in summary
        assert "100%" in summary
        assert "0 medium confidence" in summary
        assert "0 low confidence" in summary

    def test_format_confidence_summary_all_low(self, filter_service):
        """Test format_confidence_summary with all low confidence patterns."""
        low_patterns = [
            Pattern(
                type=PatternType.CALCULATION,
                confidence=0.55,
                source_path="field1",
                target_path="output1",
                transformation="Low confidence",
            ),
            Pattern(
                type=PatternType.COMPLEX,
                confidence=0.60,
                source_path="field2",
                target_path="output2",
                transformation="Low-medium confidence",
            ),
        ]

        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=low_patterns,
            schema_differences=[],
            num_examples=2,
            warnings=[],
        )

        summary = filter_service.format_confidence_summary(parsed)
        assert "0 high confidence" in summary
        assert "0 medium confidence" in summary
        assert "2 low confidence" in summary
        assert "100%" in summary

    # ========================================================================
    # WARNING GENERATION TESTS
    # ========================================================================

    def test_warnings_for_many_excluded(self, filter_service, sample_parsed_examples):
        """Test warning generated when many patterns excluded."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.9)

        # Should have warning about excluding patterns
        assert len(filtered.excluded_patterns) == 2
        assert any("excluded" in w.lower() for w in filtered.warnings)

    def test_warnings_for_field_mapping_excluded(self, filter_service):
        """Test warning generated when field mapping patterns excluded."""
        patterns = [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=0.75,
                source_path="field1",
                target_path="output1",
                transformation="Field mapping",
            ),
            Pattern(
                type=PatternType.CALCULATION,
                confidence=0.95,
                source_path="field2",
                target_path="output2",
                transformation="Calculation",
            ),
        ]

        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=patterns,
            schema_differences=[],
            num_examples=2,
            warnings=[],
        )

        # Use high threshold to exclude field mapping
        filtered = filter_service.filter_patterns(parsed, 0.8)

        # Should warn about field mapping exclusion
        assert any("field mapping" in w.lower() for w in filtered.warnings)

    def test_warnings_for_medium_confidence_excluded(self, filter_service):
        """Test warning for excluding medium confidence patterns."""
        patterns = [
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=0.78,
                source_path="field1",
                target_path="output1",
                transformation="Medium confidence",
            ),
            Pattern(
                type=PatternType.ARRAY_FIRST,
                confidence=0.95,
                source_path="field2",
                target_path="output2",
                transformation="High confidence",
            ),
        ]

        parsed = ParsedExamples(
            input_schema=Schema(fields=[]),
            output_schema=Schema(fields=[]),
            patterns=patterns,
            schema_differences=[],
            num_examples=2,
            warnings=[],
        )

        # Use 0.8 threshold to exclude 0.78 pattern
        filtered = filter_service.filter_patterns(parsed, 0.8)

        # Should warn about medium confidence exclusion
        assert any("medium confidence" in w.lower() for w in filtered.warnings)

    def test_no_warnings_when_all_included(
        self, filter_service, sample_parsed_examples
    ):
        """Test no exclusion warnings when all patterns included."""
        filtered = filter_service.filter_patterns(sample_parsed_examples, 0.5)

        # Original warnings preserved, but no new exclusion warnings
        assert len(filtered.excluded_patterns) == 0
        # Should not have exclusion-related warnings
        exclusion_warnings = [w for w in filtered.warnings if "excluded" in w.lower()]
        assert len(exclusion_warnings) == 0
