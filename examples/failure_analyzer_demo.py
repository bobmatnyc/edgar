"""
Demo of FailureAnalyzer integration with SelfImprovementLoop.

Shows how to use FailureAnalyzer to analyze extraction failures
and generate actionable refinement suggestions.
"""

from edgar_analyzer.extractors.failure_analyzer import (
    FailureAnalyzer,
    RefinementPriority,
)
from edgar_analyzer.extractors.self_improvement import (
    FailureAnalysis,
    FailureType,
    TestCase,
)


def demo_failure_analysis():
    """Demonstrate failure analysis workflow."""
    print("=" * 80)
    print("FailureAnalyzer Demo - Pattern Detection & Refinement Suggestions")
    print("=" * 80)

    # Create sample test cases and failures
    print("\n1. Creating sample test cases and failures...")

    test_case_1 = TestCase(
        input={"html": "<table><tr><td>John Doe</td><td>$95,000</td></tr></table>"},
        expected_output={"name": "John Doe", "salary": 95000.0},
        description="Extract name and salary from HTML table",
    )

    test_case_2 = TestCase(
        input={"html": "<table><tr><td>Jane Smith</td><td>$120,000</td></tr></table>"},
        expected_output={"name": "Jane Smith", "salary": 120000.0},
        description="Extract name and salary (case 2)",
    )

    # Simulate extraction failures
    failures = [
        # Missing 'salary' field (3 failures)
        FailureAnalysis(
            failure_type=FailureType.MISSING_DATA,
            test_case=test_case_1,
            actual_output={"name": "John Doe"},
            missing_fields=["salary"],
        ),
        FailureAnalysis(
            failure_type=FailureType.MISSING_DATA,
            test_case=test_case_2,
            actual_output={"name": "Jane Smith"},
            missing_fields=["salary"],
        ),
        FailureAnalysis(
            failure_type=FailureType.MISSING_DATA,
            test_case=test_case_1,
            actual_output={"name": "John Doe"},
            missing_fields=["salary"],
        ),
        # Type conversion failures (2 failures)
        FailureAnalysis(
            failure_type=FailureType.INCORRECT_TRANSFORMATION,
            test_case=test_case_1,
            actual_output={"name": "John Doe", "salary": "95000"},  # String not float
            incorrect_fields={"salary": (95000.0, "95000")},
        ),
        FailureAnalysis(
            failure_type=FailureType.INCORRECT_TRANSFORMATION,
            test_case=test_case_2,
            actual_output={"name": "Jane Smith", "salary": "120000"},
            incorrect_fields={"salary": (120000.0, "120000")},
        ),
        # Parsing error (1 failure)
        FailureAnalysis(
            failure_type=FailureType.PARSING_ERROR,
            test_case=test_case_1,
            actual_output=None,
            error_message="JSON parsing failed: Unexpected token",
        ),
    ]

    print(f"   Created {len(failures)} sample failures")
    print(
        f"   - {sum(1 for f in failures if f.failure_type == FailureType.MISSING_DATA)} MISSING_DATA"
    )
    print(
        f"   - {sum(1 for f in failures if f.failure_type == FailureType.INCORRECT_TRANSFORMATION)} INCORRECT_TRANSFORMATION"
    )
    print(
        f"   - {sum(1 for f in failures if f.failure_type == FailureType.PARSING_ERROR)} PARSING_ERROR"
    )

    # Initialize FailureAnalyzer
    print("\n2. Initializing FailureAnalyzer...")
    analyzer = FailureAnalyzer(
        min_pattern_frequency=0.3,  # Detect patterns occurring in 30%+ of failures
        min_field_failures=2,  # Track fields that fail at least 2 times
    )

    # Analyze failures
    print("\n3. Analyzing failures for patterns...")
    analysis = analyzer.analyze(failures)

    print(f"\n   Analysis Results:")
    print(f"   - Total failures: {analysis.total_failures}")
    print(f"   - Confidence: {analysis.confidence:.1%}")
    print(f"   - Patterns detected: {len(analysis.patterns)}")
    print(f"\n   Failure Categories:")
    for failure_type, count in analysis.categories.items():
        percentage = (count / analysis.total_failures) * 100
        print(f"   - {failure_type.value}: {count} ({percentage:.1f}%)")

    # Display detected patterns
    print(f"\n4. Detected Patterns (sorted by frequency):")
    for i, pattern in enumerate(analysis.patterns, 1):
        print(f"\n   Pattern {i}: {pattern.name}")
        print(f"   - Frequency: {pattern.frequency:.1%}")
        print(f"   - Affected fields: {', '.join(pattern.affected_fields[:3])}")
        print(
            f"   - Failure types: {', '.join(ft.value for ft in pattern.failure_types)}"
        )
        print(f"   - Suggestion: {pattern.suggestion}")

    # Display field statistics
    if analysis.field_statistics:
        print(f"\n5. Field-Level Statistics:")
        for field, stats in sorted(
            analysis.field_statistics.items(),
            key=lambda x: x[1]["total_failures"],
            reverse=True,
        ):
            print(f"\n   Field: '{field}'")
            print(f"   - Missing count: {stats['missing_count']}")
            print(f"   - Incorrect count: {stats['incorrect_count']}")
            print(f"   - Failure rate: {stats['failure_rate']:.1%}")

    # Generate refinement suggestions
    print("\n6. Generating refinement suggestions...")
    refinements = analyzer.suggest_refinements(analysis)

    print(f"\n   Generated {len(refinements)} refinements:")
    print(
        f"   - {sum(1 for r in refinements if r.priority == RefinementPriority.CRITICAL)} CRITICAL priority"
    )
    print(
        f"   - {sum(1 for r in refinements if r.priority == RefinementPriority.HIGH)} HIGH priority"
    )
    print(
        f"   - {sum(1 for r in refinements if r.priority == RefinementPriority.MEDIUM)} MEDIUM priority"
    )
    print(
        f"   - {sum(1 for r in refinements if r.priority == RefinementPriority.LOW)} LOW priority"
    )

    # Display refinements
    print(f"\n7. Refinement Suggestions (sorted by priority):")
    for i, refinement in enumerate(refinements[:5], 1):  # Show top 5
        print(f"\n   Refinement {i} [{refinement.priority.value.upper()}]:")
        print(f"   - Type: {refinement.type.value}")
        print(f"   - Target: {refinement.target}")
        print(f"   - Suggestion: {refinement.suggestion}")
        print(f"   - Rationale: {refinement.rationale}")
        if refinement.affected_patterns:
            print(f"   - Addresses patterns: {', '.join(refinement.affected_patterns)}")

    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(
        f"✅ Analyzed {analysis.total_failures} failures with {analysis.confidence:.1%} confidence"
    )
    print(f"✅ Detected {len(analysis.patterns)} systematic failure patterns")
    print(f"✅ Generated {len(refinements)} actionable refinement suggestions")
    print(f"✅ Top priority: {refinements[0].suggestion if refinements else 'N/A'}")
    print("=" * 80)


if __name__ == "__main__":
    demo_failure_analysis()
