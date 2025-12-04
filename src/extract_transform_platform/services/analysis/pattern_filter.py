"""Pattern filtering service for confidence-based selection.

This service filters transformation patterns based on user-selected confidence
thresholds, supporting the interactive threshold selection UX (1M-362).

Design Decisions:
- **Single Responsibility**: Only handles filtering logic, not UI concerns
- **Immutable Operations**: Returns new FilteredParsedExamples, doesn't modify input
- **Validation**: Strict threshold validation with clear error messages
- **Warning Generation**: Provides helpful warnings for excluded patterns

Usage:
    >>> from extract_transform_platform.services.analysis import PatternFilterService
    >>> from extract_transform_platform.models.patterns import ParsedExamples
    >>>
    >>> # After pattern detection
    >>> parser = ExampleParser(SchemaAnalyzer())
    >>> parsed = parser.parse_examples(examples)
    >>>
    >>> # Filter by threshold
    >>> filter_service = PatternFilterService()
    >>> filtered = filter_service.filter_patterns(parsed, threshold=0.7)
    >>>
    >>> print(f"Included: {len(filtered.included_patterns)}")
    >>> print(f"Excluded: {len(filtered.excluded_patterns)}")

Migration Note:
    New service for Phase 2 platform (1M-362: Interactive Confidence Threshold UX)
"""

from typing import Dict, List, Tuple

from extract_transform_platform.models.patterns import (
    FilteredParsedExamples,
    ParsedExamples,
    Pattern,
    PatternType,
)


class PatternFilterService:
    """Service for filtering patterns based on confidence threshold.

    This service separates transformation patterns into included (meeting
    threshold) and excluded (below threshold) groups, with helpful warnings
    for users about the impact of their threshold selection.
    """

    def __init__(self) -> None:
        """Initialize pattern filter service."""
        pass

    def filter_patterns(
        self, parsed_examples: ParsedExamples, threshold: float
    ) -> FilteredParsedExamples:
        """Filter patterns by confidence threshold.

        Args:
            parsed_examples: Original parsed examples with all patterns
            threshold: Minimum confidence (0.0-1.0)

        Returns:
            FilteredParsedExamples with patterns split into included/excluded

        Raises:
            ValueError: If threshold not in [0.0, 1.0]

        Example:
            >>> service = PatternFilterService()
            >>> filtered = service.filter_patterns(parsed, 0.7)
            >>> assert all(p.confidence >= 0.7 for p in filtered.included_patterns)
            >>> assert all(p.confidence < 0.7 for p in filtered.excluded_patterns)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0.0, 1.0], got {threshold}")

        all_patterns = parsed_examples.all_patterns
        included = [p for p in all_patterns if p.confidence >= threshold]
        excluded = [p for p in all_patterns if p.confidence < threshold]

        # Generate warnings for excluded patterns
        warnings = list(parsed_examples.warnings)
        warnings.extend(self._generate_exclusion_warnings(excluded, threshold))

        return FilteredParsedExamples(
            input_schema=parsed_examples.input_schema,
            output_schema=parsed_examples.output_schema,
            all_patterns=all_patterns,
            included_patterns=included,
            excluded_patterns=excluded,
            confidence_threshold=threshold,
            schema_differences=parsed_examples.schema_differences,
            num_examples=parsed_examples.num_examples,
            warnings=warnings,
        )

    def get_threshold_presets(self) -> Dict[str, Tuple[float, str]]:
        """Get preset threshold options.

        Returns:
            Dict of preset name -> (threshold, description)

        Example:
            >>> service = PatternFilterService()
            >>> presets = service.get_threshold_presets()
            >>> presets["balanced"]
            (0.7, "Balance quality and coverage (0.7+) [RECOMMENDED]")
        """
        return {
            "conservative": (0.8, "Only high confidence patterns (0.8+)"),
            "balanced": (0.7, "Balance quality and coverage (0.7+) [RECOMMENDED]"),
            "aggressive": (0.6, "All patterns including lower confidence (0.6+)"),
        }

    def format_confidence_summary(self, parsed_examples: ParsedExamples) -> str:
        """Format confidence summary for display.

        Args:
            parsed_examples: Parsed examples to summarize

        Returns:
            Formatted string with confidence breakdown

        Example:
            >>> service = PatternFilterService()
            >>> summary = service.format_confidence_summary(parsed)
            >>> print(summary)
            Detected 5 patterns:
              • 3 high confidence (≥ 0.9) - 60%
              • 1 medium confidence (0.7-0.89) - 20%
              • 1 low confidence (< 0.7) - 20%
        """
        high = len([p for p in parsed_examples.all_patterns if p.confidence >= 0.9])
        medium = len(
            [p for p in parsed_examples.all_patterns if 0.7 <= p.confidence < 0.9]
        )
        low = len([p for p in parsed_examples.all_patterns if p.confidence < 0.7])
        total = len(parsed_examples.all_patterns)

        if total == 0:
            return "No patterns detected."

        lines = [
            f"Detected {total} patterns:",
            f"  • {high} high confidence (≥ 0.9) - {100*high/total:.0f}%",
            f"  • {medium} medium confidence (0.7-0.89) - {100*medium/total:.0f}%",
            f"  • {low} low confidence (< 0.7) - {100*low/total:.0f}%",
        ]
        return "\n".join(lines)

    def _generate_exclusion_warnings(
        self, excluded: List[Pattern], threshold: float
    ) -> List[str]:
        """Generate warnings for excluded patterns.

        Args:
            excluded: Patterns excluded by threshold
            threshold: Threshold value used

        Returns:
            List of warning messages

        Example:
            >>> warnings = service._generate_exclusion_warnings(excluded, 0.8)
            >>> # May include warnings like:
            >>> # "2 patterns excluded (below 0.8 threshold)"
            >>> # "1 field mapping pattern excluded (typically reliable)"
        """
        warnings: List[str] = []

        if not excluded:
            return warnings

        # Warn if many patterns excluded
        if len(excluded) > 3:
            warnings.append(
                f"{len(excluded)} patterns excluded (below {threshold:.1f} threshold). "
                f"Consider lowering threshold for better coverage."
            )

        # Warn if field mappings excluded (usually reliable even at medium confidence)
        field_mappings = [
            p
            for p in excluded
            if p.type in (PatternType.FIELD_MAPPING, PatternType.FIELD_RENAME)
        ]
        if field_mappings:
            warnings.append(
                f"{len(field_mappings)} field mapping pattern(s) excluded. "
                f"Field mappings are typically reliable even at medium confidence."
            )

        # Warn if excluding medium confidence patterns (0.7-0.89)
        medium_excluded = [p for p in excluded if 0.7 <= p.confidence < 0.9]
        if medium_excluded and threshold > 0.7:
            warnings.append(
                f"{len(medium_excluded)} medium confidence pattern(s) excluded. "
                f"These patterns may be valuable - consider threshold 0.7 (Balanced)."
            )

        return warnings
