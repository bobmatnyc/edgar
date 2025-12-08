"""
FailureAnalyzer - Deep analysis of extraction failures for prompt refinement.

Part of Phase 4 Meta-Extractor system. Analyzes failure patterns to generate
targeted refinement suggestions for improving extractor accuracy.

Design Decisions:
- **Pattern Detection**: Identify systematic failures vs. one-off errors
- **Frequency Tracking**: Prioritize common failures over rare edge cases
- **Actionable Suggestions**: Map patterns to concrete prompt/template changes
- **Field-Level Analysis**: Track which fields fail most often
- **Integration**: Works with SelfImprovementLoop for iterative refinement

Performance:
- Time Complexity: O(f * n) where f=failures, n=fields per failure
- Space Complexity: O(p) where p=unique patterns detected
- Expected: <100ms for 50 failures with 20 fields each

Example:
    >>> analyzer = FailureAnalyzer()
    >>> failures = [
    ...     ExtractionFailure(
    ...         input={"html": "<table>..."},
    ...         expected={"name": "John", "salary": 95000.0},
    ...         actual={"name": "John"},
    ...         error_message="Missing field: salary",
    ...         failure_type=FailureType.MISSING_DATA
    ...     )
    ... ]
    >>> analysis = analyzer.analyze(failures)
    >>> print(f"Total failures: {analysis.total_failures}")
    >>> print(f"Patterns found: {len(analysis.patterns)}")
    >>> refinements = analyzer.suggest_refinements(analysis)
    >>> for ref in refinements:
    ...     print(f"[{ref.priority}] {ref.suggestion}")
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

from edgar_analyzer.extractors.self_improvement import (
    FailureAnalysis,
    FailureType,
)

logger = structlog.get_logger(__name__)


class RefinementType(Enum):
    """Types of refinements that can be applied to extractors."""

    PROMPT_ENHANCEMENT = "prompt_enhancement"  # Improve system prompt
    PARSING_RULE = "parsing_rule"  # Add parsing instruction
    EXTRACTION_RULE = "extraction_rule"  # Field-specific extraction rule
    VALIDATION_RULE = "validation_rule"  # Output validation rule
    EXAMPLE_ADDITION = "example_addition"  # Add example to prompt
    TEMPLATE_CHANGE = "template_change"  # Modify code template


class RefinementPriority(Enum):
    """Priority levels for applying refinements."""

    CRITICAL = "critical"  # >80% failure rate
    HIGH = "high"  # 50-80% failure rate
    MEDIUM = "medium"  # 20-50% failure rate
    LOW = "low"  # <20% failure rate


@dataclass
class ExtractionFailure:
    """Detailed information about a single extraction failure.

    Attributes:
        input: Input data that was processed
        expected: Expected output from test case
        actual: Actual output from extractor (None if exception)
        error_message: Error message or description of failure
        failure_type: Category of failure (from FailureType enum)
        test_case_description: Optional description of test case
    """

    input: Dict[str, Any]
    expected: Dict[str, Any]
    actual: Optional[Dict[str, Any]]
    error_message: str
    failure_type: FailureType
    test_case_description: str = ""


@dataclass
class FailurePattern:
    """A detected pattern in extraction failures.

    Attributes:
        name: Human-readable pattern name (e.g., "nested_object_parsing")
        frequency: How often this pattern occurs (0.0-1.0)
        affected_fields: Fields commonly affected by this pattern
        failure_types: Types of failures associated with pattern
        suggestion: Recommended fix for this pattern
        examples: Example failures demonstrating this pattern
    """

    name: str
    frequency: float
    affected_fields: List[str]
    failure_types: Set[FailureType]
    suggestion: str
    examples: List[ExtractionFailure] = field(default_factory=list)

    def __post_init__(self):
        """Convert failure_types to set if needed."""
        if not isinstance(self.failure_types, set):
            self.failure_types = set(self.failure_types)


@dataclass
class FailureAnalysisResult:
    """Complete analysis of extraction failures.

    Attributes:
        total_failures: Total number of failures analyzed
        categories: Count of failures by type
        patterns: Detected failure patterns sorted by frequency
        field_statistics: Per-field failure statistics
        confidence: Confidence in pattern detection (0.0-1.0)
    """

    total_failures: int
    categories: Dict[FailureType, int]
    patterns: List[FailurePattern]
    field_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class Refinement:
    """A suggested refinement to improve extractor.

    Attributes:
        type: Type of refinement (prompt, parsing rule, etc.)
        target: What to modify (field name, prompt section, etc.)
        suggestion: Specific suggestion text
        priority: Priority level for applying this refinement
        rationale: Why this refinement is suggested
        affected_patterns: Patterns this refinement addresses
    """

    type: RefinementType
    target: str
    suggestion: str
    priority: RefinementPriority
    rationale: str
    affected_patterns: List[str] = field(default_factory=list)


class FailureAnalyzer:
    """
    Analyzes extraction failures to identify systematic issues.

    Detects patterns in failures, categorizes them, and generates
    actionable refinement suggestions for improving extractor accuracy.

    Features:
    - Pattern detection across multiple failure types
    - Field-level failure tracking
    - Frequency-based prioritization
    - Integration with SelfImprovementLoop

    Example:
        >>> analyzer = FailureAnalyzer(min_pattern_frequency=0.3)
        >>> analysis = analyzer.analyze(failures)
        >>> refinements = analyzer.suggest_refinements(analysis)
        >>> for ref in refinements[:3]:  # Top 3 refinements
        ...     print(f"[{ref.priority.value}] {ref.suggestion}")
    """

    def __init__(
        self,
        min_pattern_frequency: float = 0.2,
        min_field_failures: int = 2,
    ):
        """
        Initialize failure analyzer.

        Args:
            min_pattern_frequency: Minimum frequency (0.0-1.0) to consider a pattern
            min_field_failures: Minimum failures per field to track
        """
        self.min_pattern_frequency = min_pattern_frequency
        self.min_field_failures = min_field_failures

        logger.info(
            "FailureAnalyzer initialized",
            min_pattern_frequency=min_pattern_frequency,
            min_field_failures=min_field_failures,
        )

    def analyze(self, failures: List[FailureAnalysis]) -> FailureAnalysisResult:
        """
        Categorize and analyze extraction failures.

        Workflow:
        1. Categorize failures by type
        2. Extract field-level statistics
        3. Detect common patterns
        4. Calculate confidence in analysis

        Args:
            failures: List of FailureAnalysis from evaluation

        Returns:
            FailureAnalysisResult with categorized failures and patterns
        """
        if not failures:
            logger.warning("No failures to analyze")
            return FailureAnalysisResult(
                total_failures=0,
                categories={},
                patterns=[],
                confidence=1.0,  # High confidence in "no failures"
            )

        logger.info("Starting failure analysis", failures_count=len(failures))

        # Convert FailureAnalysis to ExtractionFailure for consistency
        extraction_failures = self._convert_failures(failures)

        # Categorize failures by type
        categories = self._categorize_failures(extraction_failures)

        # Extract field-level statistics
        field_stats = self._analyze_field_failures(extraction_failures)

        # Detect patterns
        patterns = self._detect_patterns(extraction_failures, categories)

        # Calculate confidence based on sample size and pattern clarity
        confidence = self._calculate_confidence(len(extraction_failures), patterns)

        logger.info(
            "Failure analysis complete",
            total_failures=len(extraction_failures),
            categories_count=len(categories),
            patterns_detected=len(patterns),
            confidence=confidence,
        )

        return FailureAnalysisResult(
            total_failures=len(extraction_failures),
            categories=categories,
            patterns=patterns,
            field_statistics=field_stats,
            confidence=confidence,
        )

    def suggest_refinements(self, analysis: FailureAnalysisResult) -> List[Refinement]:
        """
        Generate refinement suggestions based on failure patterns.

        Strategy:
        - High-frequency patterns → High priority refinements
        - Field-specific failures → Extraction rule refinements
        - Parse errors → Parsing rule refinements
        - Validation errors → Validation rule refinements

        Args:
            analysis: FailureAnalysisResult from analyze()

        Returns:
            List of Refinement objects sorted by priority
        """
        if analysis.total_failures == 0:
            logger.info("No failures, no refinements needed")
            return []

        logger.info(
            "Generating refinement suggestions",
            patterns_count=len(analysis.patterns),
        )

        refinements: List[Refinement] = []

        # Generate refinements for each pattern
        for pattern in analysis.patterns:
            pattern_refinements = self._pattern_to_refinements(pattern, analysis)
            refinements.extend(pattern_refinements)

        # Generate category-specific refinements
        category_refinements = self._category_to_refinements(
            analysis.categories, analysis.total_failures
        )
        refinements.extend(category_refinements)

        # Sort by priority (critical first)
        priority_order = {
            RefinementPriority.CRITICAL: 0,
            RefinementPriority.HIGH: 1,
            RefinementPriority.MEDIUM: 2,
            RefinementPriority.LOW: 3,
        }
        refinements.sort(key=lambda r: priority_order[r.priority])

        logger.info(
            "Refinement generation complete",
            refinements_count=len(refinements),
            critical=sum(
                1 for r in refinements if r.priority == RefinementPriority.CRITICAL
            ),
            high=sum(1 for r in refinements if r.priority == RefinementPriority.HIGH),
            medium=sum(
                1 for r in refinements if r.priority == RefinementPriority.MEDIUM
            ),
            low=sum(1 for r in refinements if r.priority == RefinementPriority.LOW),
        )

        return refinements

    def _convert_failures(
        self, failures: List[FailureAnalysis]
    ) -> List[ExtractionFailure]:
        """Convert FailureAnalysis to ExtractionFailure format."""
        extraction_failures = []

        for failure in failures:
            extraction_failures.append(
                ExtractionFailure(
                    input=failure.test_case.input,
                    expected=failure.test_case.expected_output,
                    actual=failure.actual_output,
                    error_message=failure.error_message,
                    failure_type=failure.failure_type,
                    test_case_description=failure.test_case.description,
                )
            )

        return extraction_failures

    def _categorize_failures(
        self, failures: List[ExtractionFailure]
    ) -> Dict[FailureType, int]:
        """Count failures by type."""
        categories: Dict[FailureType, int] = {}

        for failure in failures:
            categories[failure.failure_type] = (
                categories.get(failure.failure_type, 0) + 1
            )

        return categories

    def _analyze_field_failures(
        self, failures: List[ExtractionFailure]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze failures at field level.

        Returns:
            Dict mapping field_name to statistics (failure_count, failure_rate, etc.)
        """
        field_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"missing_count": 0, "incorrect_count": 0, "total_failures": 0}
        )

        for failure in failures:
            # Track missing fields
            if failure.failure_type == FailureType.MISSING_DATA:
                for field_name in failure.expected.keys():
                    if failure.actual is None or field_name not in failure.actual:
                        field_stats[field_name]["missing_count"] += 1
                        field_stats[field_name]["total_failures"] += 1

            # Track incorrect fields
            elif failure.failure_type == FailureType.INCORRECT_TRANSFORMATION:
                for field_name, expected_value in failure.expected.items():
                    if failure.actual and field_name in failure.actual:
                        actual_value = failure.actual[field_name]
                        if expected_value != actual_value:
                            field_stats[field_name]["incorrect_count"] += 1
                            field_stats[field_name]["total_failures"] += 1

        # Calculate failure rates
        total_test_cases = len(failures)
        for field_key, stats in field_stats.items():
            stats["failure_rate"] = stats["total_failures"] / total_test_cases

        return dict(field_stats)

    def _detect_patterns(
        self,
        failures: List[ExtractionFailure],
        categories: Dict[FailureType, int],
    ) -> List[FailurePattern]:
        """
        Detect common patterns in failures.

        Patterns detected:
        - Nested object parsing issues
        - Currency/numeric parsing issues
        - Date parsing issues
        - Boolean conversion issues
        - Specific field extraction issues
        """
        patterns: List[FailurePattern] = []
        total_failures = len(failures)

        # Pattern 1: Nested object parsing (common in HTML tables)
        nested_failures = self._detect_nested_parsing_failures(failures)
        if len(nested_failures) >= self.min_field_failures:
            frequency = len(nested_failures) / total_failures
            if frequency >= self.min_pattern_frequency:
                patterns.append(
                    FailurePattern(
                        name="nested_object_parsing",
                        frequency=frequency,
                        affected_fields=self._extract_affected_fields(nested_failures),
                        failure_types={f.failure_type for f in nested_failures},
                        suggestion="Add explicit nested object handling to prompt with examples",
                        examples=nested_failures[:3],  # Keep top 3 examples
                    )
                )

        # Pattern 2: Currency parsing
        currency_failures = self._detect_currency_failures(failures)
        if len(currency_failures) >= self.min_field_failures:
            frequency = len(currency_failures) / total_failures
            if frequency >= self.min_pattern_frequency:
                patterns.append(
                    FailurePattern(
                        name="currency_parsing",
                        frequency=frequency,
                        affected_fields=self._extract_affected_fields(
                            currency_failures
                        ),
                        failure_types={f.failure_type for f in currency_failures},
                        suggestion="Add currency parsing examples (e.g., '$95,000' → 95000.0)",
                        examples=currency_failures[:3],
                    )
                )

        # Pattern 3: Field consistently missing
        missing_field_patterns = self._detect_missing_field_patterns(failures)
        for field_name, field_failures in missing_field_patterns.items():
            frequency = len(field_failures) / total_failures
            if frequency >= self.min_pattern_frequency:
                patterns.append(
                    FailurePattern(
                        name=f"missing_field_{field_name}",
                        frequency=frequency,
                        affected_fields=[field_name],
                        failure_types={FailureType.MISSING_DATA},
                        suggestion=f"Add explicit extraction rule for '{field_name}' field",
                        examples=field_failures[:3],
                    )
                )

        # Pattern 4: Type conversion issues
        type_failures = self._detect_type_conversion_failures(failures)
        if len(type_failures) >= self.min_field_failures:
            frequency = len(type_failures) / total_failures
            if frequency >= self.min_pattern_frequency:
                patterns.append(
                    FailurePattern(
                        name="type_conversion",
                        frequency=frequency,
                        affected_fields=self._extract_affected_fields(type_failures),
                        failure_types={f.failure_type for f in type_failures},
                        suggestion="Add type conversion examples to prompt (string → int, etc.)",
                        examples=type_failures[:3],
                    )
                )

        # Sort patterns by frequency (highest first)
        patterns.sort(key=lambda p: p.frequency, reverse=True)

        logger.debug(
            "Pattern detection complete",
            patterns_detected=len(patterns),
            pattern_names=[p.name for p in patterns],
        )

        return patterns

    def _detect_nested_parsing_failures(
        self, failures: List[ExtractionFailure]
    ) -> List[ExtractionFailure]:
        """Detect failures related to nested object parsing."""
        nested_failures = []

        for failure in failures:
            # Check if expected output has nested structures
            has_nested = any(
                isinstance(v, dict) or isinstance(v, list)
                for v in failure.expected.values()
            )

            # Check if error message indicates parsing issues
            is_parsing_error = (
                failure.failure_type == FailureType.PARSING_ERROR
                or "parse" in failure.error_message.lower()
                or "json" in failure.error_message.lower()
            )

            if has_nested and is_parsing_error:
                nested_failures.append(failure)

        return nested_failures

    def _detect_currency_failures(
        self, failures: List[ExtractionFailure]
    ) -> List[ExtractionFailure]:
        """Detect failures related to currency parsing."""
        currency_failures = []

        for failure in failures:
            # Check if expected values contain numeric data (likely currency)
            has_currency = any(
                isinstance(v, (int, float))
                and v > 1000  # Heuristic for salary/currency
                for v in failure.expected.values()
            )

            # Check if actual output is missing or incorrect for these fields
            if has_currency and failure.failure_type in (
                FailureType.MISSING_DATA,
                FailureType.INCORRECT_TRANSFORMATION,
            ):
                currency_failures.append(failure)

        return currency_failures

    def _detect_missing_field_patterns(
        self, failures: List[ExtractionFailure]
    ) -> Dict[str, List[ExtractionFailure]]:
        """Group failures by missing field names."""
        missing_by_field: Dict[str, List[ExtractionFailure]] = defaultdict(list)

        for failure in failures:
            if failure.failure_type == FailureType.MISSING_DATA:
                for field_name in failure.expected.keys():
                    if failure.actual is None or field_name not in failure.actual:
                        missing_by_field[field_name].append(failure)

        # Filter to fields that fail at least min_field_failures times
        return {
            field: field_failures
            for field, field_failures in missing_by_field.items()
            if len(field_failures) >= self.min_field_failures
        }

    def _detect_type_conversion_failures(
        self, failures: List[ExtractionFailure]
    ) -> List[ExtractionFailure]:
        """Detect failures related to type conversion."""
        type_failures = []

        for failure in failures:
            if (
                failure.failure_type == FailureType.INCORRECT_TRANSFORMATION
                and failure.actual
            ):
                # Check if types don't match between expected and actual
                for field_name, expected_value in failure.expected.items():
                    if field_name in failure.actual:
                        actual_value = failure.actual[field_name]
                        if not isinstance(actual_value, type(expected_value)):
                            type_failures.append(failure)
                            break  # Count failure once

        return type_failures

    def _extract_affected_fields(self, failures: List[ExtractionFailure]) -> List[str]:
        """Extract list of fields affected by these failures."""
        field_counter: Counter = Counter()

        for failure in failures:
            # Count fields that are missing or incorrect
            for field_name in failure.expected.keys():
                if failure.actual is None or field_name not in failure.actual:
                    field_counter[field_name] += 1
                elif failure.actual.get(field_name) != failure.expected.get(field_name):
                    field_counter[field_name] += 1

        # Return top 5 most affected fields
        return [field for field, _ in field_counter.most_common(5)]

    def _calculate_confidence(
        self, failure_count: int, patterns: List[FailurePattern]
    ) -> float:
        """
        Calculate confidence in pattern detection.

        High confidence when:
        - Large sample size (more failures analyzed)
        - Clear patterns detected (high frequency)
        - Consistent pattern distribution
        """
        # Base confidence on sample size (log scale)
        if failure_count < 5:
            size_confidence = 0.5
        elif failure_count < 10:
            size_confidence = 0.7
        elif failure_count < 20:
            size_confidence = 0.85
        else:
            size_confidence = 0.95

        # Boost confidence if clear patterns detected
        if patterns:
            avg_frequency = sum(p.frequency for p in patterns) / len(patterns)
            pattern_confidence = avg_frequency
        else:
            pattern_confidence = 0.5  # Neutral if no patterns

        # Weighted average (60% sample size, 40% pattern clarity)
        confidence = 0.6 * size_confidence + 0.4 * pattern_confidence

        return round(confidence, 2)

    def _pattern_to_refinements(
        self, pattern: FailurePattern, analysis: FailureAnalysisResult
    ) -> List[Refinement]:
        """Convert a failure pattern to refinement suggestions."""
        refinements: List[Refinement] = []

        # Determine priority based on frequency
        priority = self._frequency_to_priority(pattern.frequency)

        # Map pattern name to specific refinement types
        if "nested_object" in pattern.name:
            rationale = (
                f"Affects {len(pattern.affected_fields)} fields "
                f"with {pattern.frequency:.1%} frequency"
            )
            refinements.append(
                Refinement(
                    type=RefinementType.PARSING_RULE,
                    target="system_prompt",
                    suggestion=pattern.suggestion,
                    priority=priority,
                    rationale=rationale,
                    affected_patterns=[pattern.name],
                )
            )

        elif "currency" in pattern.name:
            refinements.append(
                Refinement(
                    type=RefinementType.EXAMPLE_ADDITION,
                    target="prompt_examples",
                    suggestion=pattern.suggestion,
                    priority=priority,
                    rationale=f"Currency parsing fails {pattern.frequency:.1%} of the time",
                    affected_patterns=[pattern.name],
                )
            )

        elif "missing_field" in pattern.name:
            field_name = (
                pattern.affected_fields[0] if pattern.affected_fields else "unknown"
            )
            refinements.append(
                Refinement(
                    type=RefinementType.EXTRACTION_RULE,
                    target=field_name,
                    suggestion=pattern.suggestion,
                    priority=priority,
                    rationale=f"Field '{field_name}' missing in {pattern.frequency:.1%} of cases",
                    affected_patterns=[pattern.name],
                )
            )

        elif "type_conversion" in pattern.name:
            refinements.append(
                Refinement(
                    type=RefinementType.VALIDATION_RULE,
                    target="output_schema",
                    suggestion=pattern.suggestion,
                    priority=priority,
                    rationale=f"Type mismatches occur {pattern.frequency:.1%} of the time",
                    affected_patterns=[pattern.name],
                )
            )

        return refinements

    def _category_to_refinements(
        self, categories: Dict[FailureType, int], total_failures: int
    ) -> List[Refinement]:
        """Generate category-level refinements."""
        refinements: List[Refinement] = []

        for failure_type, count in categories.items():
            frequency = count / total_failures
            priority = self._frequency_to_priority(frequency)

            # Only suggest refinements for significant categories
            if frequency < self.min_pattern_frequency:
                continue

            if failure_type == FailureType.PARSING_ERROR:
                refinements.append(
                    Refinement(
                        type=RefinementType.PARSING_RULE,
                        target="output_format",
                        suggestion="Ensure output is valid JSON with no markdown code fences",
                        priority=priority,
                        rationale=f"Parsing errors account for {frequency:.1%} of failures",
                        affected_patterns=["parsing_errors"],
                    )
                )

            elif failure_type == FailureType.VALIDATION_ERROR:
                refinements.append(
                    Refinement(
                        type=RefinementType.VALIDATION_RULE,
                        target="schema_validation",
                        suggestion="Add schema validation examples to prompt",
                        priority=priority,
                        rationale=f"Validation errors account for {frequency:.1%} of failures",
                        affected_patterns=["validation_errors"],
                    )
                )

        return refinements

    def _frequency_to_priority(self, frequency: float) -> RefinementPriority:
        """Convert frequency to priority level."""
        if frequency >= 0.8:
            return RefinementPriority.CRITICAL
        elif frequency >= 0.5:
            return RefinementPriority.HIGH
        elif frequency >= 0.2:
            return RefinementPriority.MEDIUM
        else:
            return RefinementPriority.LOW
