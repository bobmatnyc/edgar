"""
Unit tests for FailureAnalyzer.

Tests pattern detection, failure categorization, and refinement generation.
"""

import pytest

from edgar_analyzer.extractors.failure_analyzer import (
    ExtractionFailure,
    FailureAnalyzer,
    FailurePattern,
    Refinement,
    RefinementPriority,
    RefinementType,
)
from edgar_analyzer.extractors.self_improvement import (
    FailureAnalysis,
    FailureType,
    TestCase,
)


@pytest.fixture
def analyzer():
    """Create FailureAnalyzer instance for testing."""
    return FailureAnalyzer(min_pattern_frequency=0.3, min_field_failures=2)


@pytest.fixture
def sample_test_case():
    """Create sample test case."""
    return TestCase(
        input={"html": "<table><tr><td>John Doe</td><td>$95,000</td></tr></table>"},
        expected_output={"name": "John Doe", "salary": 95000.0},
        description="Extract name and salary from HTML table",
    )


@pytest.fixture
def missing_field_failures(sample_test_case):
    """Create failures with missing fields."""
    failures = []

    # 3 failures missing 'salary' field
    for i in range(3):
        failures.append(
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=sample_test_case,
                actual_output={"name": "John Doe"},
                missing_fields=["salary"],
            )
        )

    # 2 failures missing 'name' field
    for i in range(2):
        failures.append(
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=sample_test_case,
                actual_output={"salary": 95000.0},
                missing_fields=["name"],
            )
        )

    return failures


@pytest.fixture
def parsing_failures(sample_test_case):
    """Create parsing failures."""
    failures = []

    for i in range(2):
        failures.append(
            FailureAnalysis(
                failure_type=FailureType.PARSING_ERROR,
                test_case=sample_test_case,
                actual_output=None,
                error_message="JSON parsing failed: Unexpected token",
            )
        )

    return failures


@pytest.fixture
def type_conversion_failures(sample_test_case):
    """Create type conversion failures."""
    failures = []

    # Expected float, got string
    for i in range(2):
        failures.append(
            FailureAnalysis(
                failure_type=FailureType.INCORRECT_TRANSFORMATION,
                test_case=sample_test_case,
                actual_output={
                    "name": "John Doe",
                    "salary": "95000",
                },  # String not float
                incorrect_fields={"salary": (95000.0, "95000")},
            )
        )

    return failures


class TestFailureAnalyzer:
    """Test suite for FailureAnalyzer class."""

    def test_init(self):
        """Test FailureAnalyzer initialization."""
        analyzer = FailureAnalyzer(min_pattern_frequency=0.5, min_field_failures=3)

        assert analyzer.min_pattern_frequency == 0.5
        assert analyzer.min_field_failures == 3

    def test_analyze_empty_failures(self, analyzer):
        """Test analysis with no failures."""
        result = analyzer.analyze([])

        assert result.total_failures == 0
        assert len(result.categories) == 0
        assert len(result.patterns) == 0
        assert result.confidence == 1.0  # High confidence in "no failures"

    def test_analyze_categorizes_failures(self, analyzer, missing_field_failures):
        """Test that analyze() correctly categorizes failures."""
        result = analyzer.analyze(missing_field_failures)

        assert result.total_failures == 5
        assert FailureType.MISSING_DATA in result.categories
        assert result.categories[FailureType.MISSING_DATA] == 5

    def test_analyze_detects_missing_field_pattern(
        self, analyzer, missing_field_failures
    ):
        """Test detection of missing field patterns."""
        result = analyzer.analyze(missing_field_failures)

        # Should detect 'salary' missing pattern (3/5 = 60% frequency)
        pattern_names = [p.name for p in result.patterns]
        assert "missing_field_salary" in pattern_names

        # Find the salary pattern
        salary_pattern = next(p for p in result.patterns if "salary" in p.name)
        assert salary_pattern.frequency == 3 / 5  # 60%
        assert "salary" in salary_pattern.affected_fields
        assert FailureType.MISSING_DATA in salary_pattern.failure_types

    def test_analyze_field_statistics(self, analyzer, missing_field_failures):
        """Test field-level failure statistics."""
        result = analyzer.analyze(missing_field_failures)

        # Check field statistics
        assert "salary" in result.field_statistics
        assert "name" in result.field_statistics

        # Salary missing in 3/5 cases
        assert result.field_statistics["salary"]["missing_count"] == 3
        assert result.field_statistics["salary"]["failure_rate"] == 3 / 5

        # Name missing in 2/5 cases
        assert result.field_statistics["name"]["missing_count"] == 2
        assert result.field_statistics["name"]["failure_rate"] == 2 / 5

    def test_analyze_parsing_pattern(self, analyzer, parsing_failures):
        """Test detection of parsing error patterns."""
        result = analyzer.analyze(parsing_failures)

        assert result.total_failures == 2
        assert FailureType.PARSING_ERROR in result.categories
        assert result.categories[FailureType.PARSING_ERROR] == 2

    def test_analyze_type_conversion_pattern(self, analyzer, type_conversion_failures):
        """Test detection of type conversion patterns."""
        result = analyzer.analyze(type_conversion_failures)

        assert result.total_failures == 2
        assert FailureType.INCORRECT_TRANSFORMATION in result.categories

        # Should detect type_conversion pattern
        pattern_names = [p.name for p in result.patterns]
        assert "type_conversion" in pattern_names

    def test_analyze_mixed_failures(
        self,
        analyzer,
        missing_field_failures,
        parsing_failures,
        type_conversion_failures,
    ):
        """Test analysis with mixed failure types."""
        all_failures = (
            missing_field_failures + parsing_failures + type_conversion_failures
        )
        result = analyzer.analyze(all_failures)

        assert result.total_failures == 9
        assert len(result.categories) == 3  # 3 different failure types
        assert len(result.patterns) > 0  # Should detect multiple patterns

    def test_confidence_calculation(self, analyzer):
        """Test confidence calculation based on sample size."""
        # Small sample (< 5 failures) → low confidence
        small_failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=TestCase(input={}, expected_output={}, description=""),
                actual_output=None,
            )
            for _ in range(3)
        ]
        small_result = analyzer.analyze(small_failures)
        assert small_result.confidence < 0.7

        # Large sample (> 20 failures) → high confidence
        large_failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=TestCase(input={}, expected_output={}, description=""),
                actual_output=None,
            )
            for _ in range(25)
        ]
        large_result = analyzer.analyze(large_failures)
        assert large_result.confidence > 0.7

    def test_suggest_refinements_no_failures(self, analyzer):
        """Test refinement suggestions with no failures."""
        analysis_result = analyzer.analyze([])
        refinements = analyzer.suggest_refinements(analysis_result)

        assert len(refinements) == 0

    def test_suggest_refinements_missing_field(self, analyzer, missing_field_failures):
        """Test refinement suggestions for missing field pattern."""
        analysis_result = analyzer.analyze(missing_field_failures)
        refinements = analyzer.suggest_refinements(analysis_result)

        # Should suggest extraction rule for missing field
        extraction_refinements = [
            r for r in refinements if r.type == RefinementType.EXTRACTION_RULE
        ]
        assert len(extraction_refinements) > 0

        # Should target 'salary' field (highest frequency)
        salary_refinements = [r for r in extraction_refinements if r.target == "salary"]
        assert len(salary_refinements) > 0

        # Should have appropriate priority
        assert salary_refinements[0].priority in [
            RefinementPriority.HIGH,
            RefinementPriority.MEDIUM,
        ]

    def test_suggest_refinements_parsing_errors(self, analyzer, parsing_failures):
        """Test refinement suggestions for parsing errors."""
        # Create enough parsing failures to trigger category-level refinement
        many_parsing_failures = parsing_failures * 3  # 6 failures

        analysis_result = analyzer.analyze(many_parsing_failures)
        refinements = analyzer.suggest_refinements(analysis_result)

        # Should suggest parsing rule refinement
        parsing_refinements = [
            r for r in refinements if r.type == RefinementType.PARSING_RULE
        ]
        assert len(parsing_refinements) > 0

        # Should mention JSON/parsing in suggestion
        assert any("json" in r.suggestion.lower() for r in parsing_refinements)

    def test_suggest_refinements_sorted_by_priority(
        self, analyzer, missing_field_failures, parsing_failures
    ):
        """Test that refinements are sorted by priority."""
        all_failures = missing_field_failures + parsing_failures
        analysis_result = analyzer.analyze(all_failures)
        refinements = analyzer.suggest_refinements(analysis_result)

        # Check that refinements are sorted (critical/high first)
        priority_order = {
            RefinementPriority.CRITICAL: 0,
            RefinementPriority.HIGH: 1,
            RefinementPriority.MEDIUM: 2,
            RefinementPriority.LOW: 3,
        }

        for i in range(len(refinements) - 1):
            current_priority = priority_order[refinements[i].priority]
            next_priority = priority_order[refinements[i + 1].priority]
            assert current_priority <= next_priority

    def test_frequency_to_priority_mapping(self, analyzer):
        """Test that frequency correctly maps to priority levels."""
        # Critical: >= 80%
        assert analyzer._frequency_to_priority(0.9) == RefinementPriority.CRITICAL
        assert analyzer._frequency_to_priority(0.8) == RefinementPriority.CRITICAL

        # High: 50-80%
        assert analyzer._frequency_to_priority(0.7) == RefinementPriority.HIGH
        assert analyzer._frequency_to_priority(0.5) == RefinementPriority.HIGH

        # Medium: 20-50%
        assert analyzer._frequency_to_priority(0.4) == RefinementPriority.MEDIUM
        assert analyzer._frequency_to_priority(0.2) == RefinementPriority.MEDIUM

        # Low: < 20%
        assert analyzer._frequency_to_priority(0.1) == RefinementPriority.LOW

    def test_pattern_examples_limited(self, analyzer, missing_field_failures):
        """Test that patterns keep limited examples (top 3)."""
        # Create many failures
        many_failures = missing_field_failures * 3  # 15 failures

        analysis_result = analyzer.analyze(many_failures)

        # Check that examples are limited
        for pattern in analysis_result.patterns:
            assert len(pattern.examples) <= 3

    def test_min_pattern_frequency_threshold(self):
        """Test that patterns below min_frequency are filtered."""
        # Analyzer with high threshold (50%)
        strict_analyzer = FailureAnalyzer(min_pattern_frequency=0.5)

        # Create failures where pattern is only 30% frequency
        failures = []
        for _ in range(3):  # 30% will have pattern
            failures.append(
                FailureAnalysis(
                    failure_type=FailureType.MISSING_DATA,
                    test_case=TestCase(input={}, expected_output={"field": 1}),
                    actual_output=None,
                    missing_fields=["field"],
                )
            )
        for _ in range(7):  # 70% different pattern
            failures.append(
                FailureAnalysis(
                    failure_type=FailureType.PARSING_ERROR,
                    test_case=TestCase(input={}, expected_output={}),
                    actual_output=None,
                )
            )

        result = strict_analyzer.analyze(failures)

        # Should not detect 'field' pattern (30% < 50% threshold)
        pattern_names = [p.name for p in result.patterns]
        assert "missing_field_field" not in pattern_names

    def test_min_field_failures_threshold(self):
        """Test that fields with too few failures are filtered."""
        # Analyzer requiring at least 3 failures per field
        strict_analyzer = FailureAnalyzer(min_field_failures=3)

        # Create only 2 failures for a field
        failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=TestCase(input={}, expected_output={"rare_field": 1}),
                actual_output=None,
                missing_fields=["rare_field"],
            )
            for _ in range(2)
        ]

        result = strict_analyzer.analyze(failures)

        # Should not create pattern for rare_field (2 < 3 threshold)
        pattern_names = [p.name for p in result.patterns]
        assert "missing_field_rare_field" not in pattern_names

    def test_currency_parsing_detection(self, analyzer, sample_test_case):
        """Test detection of currency parsing issues."""
        # Create failures with currency-related fields
        failures = []
        for _ in range(3):
            failures.append(
                FailureAnalysis(
                    failure_type=FailureType.MISSING_DATA,
                    test_case=TestCase(
                        input={"html": "<td>$95,000</td>"},
                        expected_output={"salary": 95000.0},  # Large number (currency)
                    ),
                    actual_output=None,
                )
            )

        result = analyzer.analyze(failures)

        # Should detect currency parsing pattern
        pattern_names = [p.name for p in result.patterns]
        assert "currency_parsing" in pattern_names

        # Find currency pattern
        currency_pattern = next(p for p in result.patterns if "currency" in p.name)
        assert currency_pattern.frequency == 1.0  # All failures related
        assert "currency" in currency_pattern.suggestion.lower()

    def test_nested_parsing_detection(self, analyzer):
        """Test detection of nested object parsing issues."""
        # Create failures with nested structures
        failures = []
        for _ in range(3):
            failures.append(
                FailureAnalysis(
                    failure_type=FailureType.PARSING_ERROR,
                    test_case=TestCase(
                        input={"html": "<table>..."},
                        expected_output={
                            "person": {"name": "John", "age": 30},  # Nested dict
                            "skills": ["Python", "Java"],  # Nested list
                        },
                    ),
                    actual_output=None,
                    error_message="JSON parsing failed",
                )
            )

        result = analyzer.analyze(failures)

        # Should detect nested parsing pattern
        pattern_names = [p.name for p in result.patterns]
        assert "nested_object_parsing" in pattern_names

        # Find nested pattern
        nested_pattern = next(p for p in result.patterns if "nested" in p.name)
        assert "nested" in nested_pattern.suggestion.lower()

    def test_refinement_rationale(self, analyzer, missing_field_failures):
        """Test that refinements include clear rationale."""
        analysis_result = analyzer.analyze(missing_field_failures)
        refinements = analyzer.suggest_refinements(analysis_result)

        # All refinements should have non-empty rationale
        for refinement in refinements:
            assert len(refinement.rationale) > 0
            assert "%" in refinement.rationale  # Should mention frequency

    def test_refinement_affected_patterns(self, analyzer, missing_field_failures):
        """Test that refinements track affected patterns."""
        analysis_result = analyzer.analyze(missing_field_failures)
        refinements = analyzer.suggest_refinements(analysis_result)

        # All refinements should track which patterns they address
        for refinement in refinements:
            assert len(refinement.affected_patterns) > 0

    def test_integration_with_self_improvement_loop(self, analyzer, sample_test_case):
        """Test integration with SelfImprovementLoop data structures."""
        # Create FailureAnalysis objects (from SelfImprovementLoop.evaluate)
        failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=sample_test_case,
                actual_output={"name": "John Doe"},
                missing_fields=["salary"],
            ),
            FailureAnalysis(
                failure_type=FailureType.PARSING_ERROR,
                test_case=sample_test_case,
                actual_output=None,
                error_message="JSON decode error",
            ),
        ]

        # Should work seamlessly with FailureAnalysis input
        result = analyzer.analyze(failures)

        assert result.total_failures == 2
        assert len(result.categories) == 2

        # Should generate refinements
        refinements = analyzer.suggest_refinements(result)
        assert len(refinements) > 0


class TestDataModels:
    """Test data model classes."""

    def test_extraction_failure_creation(self):
        """Test ExtractionFailure dataclass creation."""
        failure = ExtractionFailure(
            input={"html": "<table>..."},
            expected={"name": "John"},
            actual=None,
            error_message="Parsing failed",
            failure_type=FailureType.PARSING_ERROR,
            test_case_description="Test nested tables",
        )

        assert failure.input == {"html": "<table>..."}
        assert failure.expected == {"name": "John"}
        assert failure.actual is None
        assert failure.error_message == "Parsing failed"
        assert failure.failure_type == FailureType.PARSING_ERROR
        assert failure.test_case_description == "Test nested tables"

    def test_failure_pattern_creation(self):
        """Test FailurePattern dataclass creation."""
        pattern = FailurePattern(
            name="nested_parsing",
            frequency=0.75,
            affected_fields=["person", "address"],
            failure_types={FailureType.PARSING_ERROR},
            suggestion="Add nested object examples",
            examples=[],
        )

        assert pattern.name == "nested_parsing"
        assert pattern.frequency == 0.75
        assert pattern.affected_fields == ["person", "address"]
        assert FailureType.PARSING_ERROR in pattern.failure_types
        assert pattern.suggestion == "Add nested object examples"

    def test_refinement_creation(self):
        """Test Refinement dataclass creation."""
        refinement = Refinement(
            type=RefinementType.PARSING_RULE,
            target="system_prompt",
            suggestion="Add JSON validation",
            priority=RefinementPriority.HIGH,
            rationale="60% of failures are parsing errors",
            affected_patterns=["nested_parsing", "json_errors"],
        )

        assert refinement.type == RefinementType.PARSING_RULE
        assert refinement.target == "system_prompt"
        assert refinement.suggestion == "Add JSON validation"
        assert refinement.priority == RefinementPriority.HIGH
        assert refinement.rationale == "60% of failures are parsing errors"
        assert len(refinement.affected_patterns) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_all_same_failure_type(self, analyzer):
        """Test analysis when all failures are same type."""
        failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=TestCase(input={}, expected_output={"field": 1}),
                actual_output=None,
            )
            for _ in range(10)
        ]

        result = analyzer.analyze(failures)

        assert len(result.categories) == 1
        assert result.categories[FailureType.MISSING_DATA] == 10

    def test_all_different_failure_types(self, analyzer):
        """Test analysis when all failures are different types."""
        failure_types = [
            FailureType.PARSING_ERROR,
            FailureType.VALIDATION_ERROR,
            FailureType.MISSING_DATA,
            FailureType.INCORRECT_TRANSFORMATION,
            FailureType.EXCEPTION,
        ]

        failures = [
            FailureAnalysis(
                failure_type=ft,
                test_case=TestCase(input={}, expected_output={}),
                actual_output=None,
            )
            for ft in failure_types
        ]

        result = analyzer.analyze(failures)

        assert len(result.categories) == 5  # All types present

    def test_actual_output_none(self, analyzer):
        """Test handling when actual_output is None."""
        failures = [
            FailureAnalysis(
                failure_type=FailureType.EXCEPTION,
                test_case=TestCase(input={}, expected_output={"field": 1}),
                actual_output=None,  # Exception case
                error_message="NullPointerException",
            )
        ]

        result = analyzer.analyze(failures)

        # Should handle gracefully without crashing
        assert result.total_failures == 1

    def test_empty_expected_output(self, analyzer):
        """Test handling when expected output is empty."""
        failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=TestCase(input={}, expected_output={}),  # Empty expected
                actual_output=None,
            )
        ]

        result = analyzer.analyze(failures)

        # Should handle gracefully
        assert result.total_failures == 1
