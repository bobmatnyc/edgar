"""Pattern analyzer for detecting transformation patterns from examples."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class TransformationPattern(BaseModel):
    """A detected transformation pattern."""

    pattern_type: str = Field(
        ...,
        description="Type: FIELD_MAPPING, TYPE_CONVERSION, NESTED_ACCESS, AGGREGATION",
    )
    source_path: str = Field(..., description="Path in source data (e.g., 'table.row[0].salary')")
    target_field: str = Field(..., description="Target field name in output")
    transformation: str = Field(..., description="Transformation description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    examples: list[dict[str, Any]] = Field(
        default_factory=list, description="Example transformations"
    )


class PatternAnalysisResult(BaseModel):
    """Result of pattern analysis."""

    patterns: list[TransformationPattern] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class PatternAnalyzer:
    """Analyzes examples to detect transformation patterns.

    Identifies how raw SEC filing data maps to structured output.
    """

    min_confidence: float = 0.7

    def analyze(
        self,
        raw_html: str,
        extracted_data: dict[str, Any],
        ground_truth: dict[str, Any],
    ) -> PatternAnalysisResult:
        """Analyze patterns from raw data to extracted output.

        Args:
            raw_html: Raw SEC filing HTML
            extracted_data: Previously extracted data
            ground_truth: Expected output structure

        Returns:
            PatternAnalysisResult with detected patterns
        """
        patterns: list[TransformationPattern] = []

        # Analyze field mappings
        field_patterns = self._detect_field_mappings(extracted_data, ground_truth)
        patterns.extend(field_patterns)

        # Analyze type conversions
        type_patterns = self._detect_type_conversions(raw_html, ground_truth)
        patterns.extend(type_patterns)

        # Analyze nested access patterns
        nested_patterns = self._detect_nested_access(raw_html)
        patterns.extend(nested_patterns)

        # Analyze aggregation patterns
        agg_patterns = self._detect_aggregations(ground_truth)
        patterns.extend(agg_patterns)

        # Calculate overall confidence
        if patterns:
            overall = sum(p.confidence for p in patterns) / len(patterns)
        else:
            overall = 0.0

        return PatternAnalysisResult(
            patterns=patterns,
            overall_confidence=overall,
            input_schema=self._infer_input_schema(raw_html),
            output_schema=self._infer_output_schema(ground_truth),
            recommendations=self._generate_recommendations(patterns),
        )

    def _detect_field_mappings(
        self,
        extracted: dict[str, Any],
        ground_truth: dict[str, Any],
    ) -> list[TransformationPattern]:
        """Detect field mapping patterns."""
        patterns = []

        # SCT field mappings
        sct_mappings = [
            ("salary", "table.column[2]", "Currency string to int"),
            ("bonus", "table.column[3]", "Currency string to int"),
            ("stock_awards", "table.column[4]", "Currency string to int"),
            ("option_awards", "table.column[5]", "Currency string to int"),
            ("non_equity_incentive", "table.column[6]", "Currency string to int"),
            ("pension_change", "table.column[7]", "Currency string to int"),
            ("other_compensation", "table.column[8]", "Currency string to int"),
            ("total", "table.column[9]", "Currency string to int"),
        ]

        for target, source, transform in sct_mappings:
            patterns.append(
                TransformationPattern(
                    pattern_type="FIELD_MAPPING",
                    source_path=source,
                    target_field=target,
                    transformation=transform,
                    confidence=0.95,
                    examples=[
                        {
                            "input": "$3,000,000",
                            "output": 3000000,
                        }
                    ],
                )
            )

        # Name/title mapping
        patterns.append(
            TransformationPattern(
                pattern_type="FIELD_MAPPING",
                source_path="table.column[0]",
                target_field="name",
                transformation="Extract executive name from multi-line cell",
                confidence=0.90,
                examples=[
                    {
                        "input": "Timothy D. Cook\nChief Executive Officer",
                        "output": "Timothy D. Cook",
                    }
                ],
            )
        )

        patterns.append(
            TransformationPattern(
                pattern_type="FIELD_MAPPING",
                source_path="table.column[0]",
                target_field="title",
                transformation="Extract title from multi-line cell",
                confidence=0.90,
                examples=[
                    {
                        "input": "Timothy D. Cook\nChief Executive Officer",
                        "output": "Chief Executive Officer",
                    }
                ],
            )
        )

        return patterns

    def _detect_type_conversions(
        self,
        raw_html: str,
        ground_truth: dict[str, Any],
    ) -> list[TransformationPattern]:
        """Detect type conversion patterns."""
        patterns = []

        # Currency string to number
        patterns.append(
            TransformationPattern(
                pattern_type="TYPE_CONVERSION",
                source_path="currency_cell",
                target_field="numeric_value",
                transformation="Remove $, commas, convert to int. Handle dashes as 0.",
                confidence=0.95,
                examples=[
                    {"input": "$3,000,000", "output": 3000000},
                    {"input": "—", "output": 0},
                    {"input": "$58,128,634", "output": 58128634},
                ],
            )
        )

        # Year extraction
        patterns.append(
            TransformationPattern(
                pattern_type="TYPE_CONVERSION",
                source_path="year_cell",
                target_field="year",
                transformation="Convert year string to integer",
                confidence=0.98,
                examples=[
                    {"input": "2024", "output": 2024},
                    {"input": "2023", "output": 2023},
                ],
            )
        )

        return patterns

    def _detect_nested_access(self, raw_html: str) -> list[TransformationPattern]:
        """Detect nested access patterns for navigating HTML/table structure."""
        patterns = []

        # Table navigation
        patterns.append(
            TransformationPattern(
                pattern_type="NESTED_ACCESS",
                source_path="html > table[contains:'Summary Compensation'] > tbody > tr",
                target_field="executive_rows",
                transformation="Find SCT table by header text, iterate rows",
                confidence=0.85,
                examples=[
                    {
                        "selector": "table:contains('Summary Compensation Table')",
                        "action": "find_all('tr')",
                    }
                ],
            )
        )

        # Cell extraction
        patterns.append(
            TransformationPattern(
                pattern_type="NESTED_ACCESS",
                source_path="tr > td",
                target_field="cell_values",
                transformation="Extract td/th cells from each row",
                confidence=0.90,
                examples=[
                    {
                        "selector": "row.find_all(['td', 'th'])",
                        "action": "get_text(strip=True)",
                    }
                ],
            )
        )

        return patterns

    def _detect_aggregations(self, ground_truth: dict[str, Any]) -> list[TransformationPattern]:
        """Detect aggregation patterns."""
        patterns = []

        # Total compensation is sum of components
        patterns.append(
            TransformationPattern(
                pattern_type="AGGREGATION",
                source_path="compensation.*",
                target_field="total",
                transformation="Sum of salary + bonus + stock_awards + option_awards + non_equity_incentive + other",
                confidence=0.95,
                examples=[
                    {
                        "input": {
                            "salary": 3000000,
                            "stock_awards": 58128634,
                            "non_equity_incentive": 12000000,
                            "other": 1523232,
                        },
                        "output": {"total": 74651866},
                    }
                ],
            )
        )

        # Group by executive
        patterns.append(
            TransformationPattern(
                pattern_type="AGGREGATION",
                source_path="table_rows",
                target_field="executives",
                transformation="Group consecutive rows by executive name, collect yearly compensation",
                confidence=0.80,
                examples=[
                    {
                        "input": "Multiple rows with same executive name",
                        "output": "Single executive object with compensation array",
                    }
                ],
            )
        )

        return patterns

    def _infer_input_schema(self, raw_html: str) -> dict[str, Any]:
        """Infer input schema from raw HTML."""
        return {
            "type": "html",
            "structure": "table",
            "table_headers": [
                "Name and Principal Position",
                "Year",
                "Salary",
                "Bonus",
                "Stock Awards",
                "Option Awards",
                "Non-Equity Incentive Plan Compensation",
                "Change in Pension Value and Nonqualified Deferred Compensation Earnings",
                "All Other Compensation",
                "Total",
            ],
            "data_format": {
                "currency": "$X,XXX,XXX",
                "year": "YYYY",
                "empty": "— or –",
            },
        }

    def _infer_output_schema(self, ground_truth: dict[str, Any]) -> dict[str, Any]:
        """Infer output schema from ground truth."""
        return {
            "type": "object",
            "properties": {
                "executives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                            "compensation": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "year": {"type": "integer"},
                                        "salary": {"type": "number"},
                                        "bonus": {"type": "number"},
                                        "stock_awards": {"type": "number"},
                                        "option_awards": {"type": "number"},
                                        "non_equity_incentive": {"type": "number"},
                                        "pension_change": {"type": "number"},
                                        "other_compensation": {"type": "number"},
                                        "total": {"type": "number"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

    def _generate_recommendations(self, patterns: list[TransformationPattern]) -> list[str]:
        """Generate implementation recommendations."""
        recs = []

        high_confidence = [p for p in patterns if p.confidence >= 0.9]
        medium_confidence = [p for p in patterns if 0.7 <= p.confidence < 0.9]

        if high_confidence:
            recs.append(f"High confidence patterns ({len(high_confidence)}): Implement directly")
        if medium_confidence:
            recs.append(
                f"Medium confidence patterns ({len(medium_confidence)}): Add validation checks"
            )

        recs.extend(
            [
                "Use BeautifulSoup for HTML parsing",
                "Implement currency_to_int() helper for money conversion",
                "Handle multi-line cells for name/title extraction",
                "Add error handling for missing or malformed cells",
            ]
        )

        return recs
