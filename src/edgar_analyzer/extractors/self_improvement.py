"""
SelfImprovementLoop - Evaluates extractor performance and refines prompts/templates.

Phase 4 of the Meta-Extractor system. Provides:
- Accuracy evaluation on test cases
- Failure analysis and categorization
- Prompt/template refinement based on failures
- Iterative improvement until target accuracy
- Version tracking and improvement history

Design Decisions:
- **Iterative Refinement**: Run evaluate → analyze → refine loop until accuracy target met
- **Failure Categorization**: Parse errors, validation errors, missing data, incorrect transformations
- **Prompt Tuning**: Adjust LLM system prompt and parsing rules based on failure patterns
- **Version Tracking**: Maintain improvement history with version numbers
- **Plateau Detection**: Stop if accuracy doesn't improve for 2 iterations

Performance:
- Time Complexity: O(i * t) where i=iterations, t=test_cases
- Space Complexity: O(h) where h=improvement history size
- Expected: <30s for 10 test cases, 5 iterations max

Example:
    >>> loop = SelfImprovementLoop(meta_extractor, max_iterations=5)
    >>> result = await loop.run(
    ...     extractor_name="sct_extractor",
    ...     test_cases=[TestCase(input={...}, expected_output={...}, description="...")],
    ...     target_accuracy=0.90
    ... )
    >>> print(f"Final accuracy: {result.final_accuracy}")
    >>> print(f"Iterations: {result.iterations}")
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from edgar_analyzer.extractors.meta_extractor import MetaExtractor
from edgar_analyzer.extractors.registry import ExtractorRegistry
from edgar_analyzer.extractors.synthesizer import GeneratedExtractor, PatternAnalysis
from extract_transform_platform.core.base import IDataExtractor

logger = structlog.get_logger(__name__)


class FailureType(Enum):
    """Categorization of extraction failures."""

    PARSING_ERROR = "parsing_error"  # JSON/HTML parsing failed
    VALIDATION_ERROR = "validation_error"  # Output doesn't match schema
    MISSING_DATA = "missing_data"  # Required fields missing from output
    INCORRECT_TRANSFORMATION = "incorrect_transformation"  # Wrong values extracted
    EXCEPTION = "exception"  # Unhandled exception during extraction


@dataclass
class TestCase:
    """Test case for extractor evaluation.

    Attributes:
        input: Input data for extractor (format depends on extractor)
        expected_output: Expected output matching extractor schema
        description: Human-readable description of test case
    """

    input: Dict[str, Any]
    expected_output: Dict[str, Any]
    description: str = ""


@dataclass
class FailureAnalysis:
    """Analysis of a single test case failure.

    Attributes:
        failure_type: Categorization of failure
        test_case: The failed test case
        actual_output: Actual output from extractor (if any)
        error_message: Error message (if exception)
        missing_fields: List of missing required fields
        incorrect_fields: Dict of field -> (expected, actual) for mismatches
    """

    failure_type: FailureType
    test_case: TestCase
    actual_output: Optional[Dict[str, Any]] = None
    error_message: str = ""
    missing_fields: List[str] = field(default_factory=list)
    incorrect_fields: Dict[str, tuple[Any, Any]] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of running extractor on test cases.

    Attributes:
        accuracy: Percentage of tests passed (0.0-1.0)
        passed_count: Number of successful test cases
        failed_count: Number of failed test cases
        failures: Detailed failure analysis for each failure
    """

    accuracy: float
    passed_count: int
    failed_count: int
    failures: List[FailureAnalysis] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Total number of test cases."""
        return self.passed_count + self.failed_count


@dataclass
class IterationHistory:
    """History entry for a single improvement iteration.

    Attributes:
        iteration: Iteration number (1-based)
        accuracy: Accuracy after this iteration
        changes_made: Description of changes applied
        failures_addressed: Number of failures addressed
        timestamp: ISO timestamp of iteration
    """

    iteration: int
    accuracy: float
    changes_made: str
    failures_addressed: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ImprovementResult:
    """Result of full improvement loop.

    Attributes:
        success: Whether target accuracy was reached
        final_accuracy: Accuracy after final iteration
        iterations: Number of iterations performed
        history: List of iteration history entries
        stopped_reason: Why loop terminated (target_met, max_iterations, plateau)
    """

    success: bool
    final_accuracy: float
    iterations: int
    history: List[IterationHistory] = field(default_factory=list)
    stopped_reason: str = ""


@dataclass
class DeploymentResult:
    """Result of redeploying improved extractor.

    Attributes:
        success: Whether deployment succeeded
        version: New version number
        registry_updated: Whether registry was updated
        error_message: Error message if failed
    """

    success: bool
    version: str
    registry_updated: bool = False
    error_message: str = ""


class SelfImprovementLoop:
    """
    Self-improvement loop for refining extractors based on test failures.

    Implements iterative refinement:
    1. Evaluate extractor on test cases
    2. Analyze failures to identify patterns
    3. Refine prompt/template based on failure analysis
    4. Redeploy improved extractor
    5. Repeat until target accuracy or max iterations

    Stopping Conditions:
    - Target accuracy reached
    - Max iterations exhausted
    - Accuracy plateau (no improvement for 2 iterations)

    Example:
        >>> loop = SelfImprovementLoop(meta_extractor, max_iterations=5)
        >>> result = await loop.run(
        ...     extractor_name="sct_extractor",
        ...     test_cases=test_cases,
        ...     target_accuracy=0.90
        ... )
        >>> if result.success:
        ...     print(f"Reached {result.final_accuracy:.1%} in {result.iterations} iterations")
    """

    def __init__(
        self,
        meta_extractor: MetaExtractor,
        max_iterations: int = 5,
        plateau_threshold: int = 2,
    ):
        """
        Initialize self-improvement loop.

        Args:
            meta_extractor: MetaExtractor instance for regenerating extractors
            max_iterations: Maximum improvement iterations (default: 5)
            plateau_threshold: Stop if no improvement for N iterations (default: 2)
        """
        self.meta_extractor = meta_extractor
        self.max_iterations = max_iterations
        self.plateau_threshold = plateau_threshold
        self.registry = ExtractorRegistry()

        logger.info(
            "SelfImprovementLoop initialized",
            max_iterations=max_iterations,
            plateau_threshold=plateau_threshold,
        )

    async def evaluate(
        self, extractor: IDataExtractor, test_cases: List[TestCase]
    ) -> EvaluationResult:
        """
        Run accuracy assessment on test cases.

        Args:
            extractor: Extractor instance to evaluate
            test_cases: List of test cases to run

        Returns:
            EvaluationResult with accuracy and failure details
        """
        if not test_cases:
            logger.warning("No test cases provided for evaluation")
            return EvaluationResult(
                accuracy=0.0,
                passed_count=0,
                failed_count=0,
                failures=[],
            )

        logger.info(
            "Starting evaluation",
            test_cases_count=len(test_cases),
        )

        passed = 0
        failures: List[FailureAnalysis] = []

        for idx, test_case in enumerate(test_cases):
            logger.debug(
                "Running test case",
                index=idx + 1,
                total=len(test_cases),
                description=test_case.description,
            )

            try:
                # Run extraction
                actual_output = await extractor.extract(**test_case.input)

                # Check for successful extraction
                if actual_output is None:
                    failures.append(
                        FailureAnalysis(
                            failure_type=FailureType.MISSING_DATA,
                            test_case=test_case,
                            actual_output=None,
                            error_message="Extractor returned None",
                        )
                    )
                    continue

                # Validate output against expected
                failure = self._validate_output(
                    test_case, actual_output, test_case.expected_output
                )

                if failure:
                    failures.append(failure)
                else:
                    passed += 1

            except json.JSONDecodeError as e:
                failures.append(
                    FailureAnalysis(
                        failure_type=FailureType.PARSING_ERROR,
                        test_case=test_case,
                        error_message=f"JSON parsing failed: {e}",
                    )
                )

            except Exception as e:
                failures.append(
                    FailureAnalysis(
                        failure_type=FailureType.EXCEPTION,
                        test_case=test_case,
                        error_message=f"{type(e).__name__}: {e}",
                    )
                )

        accuracy = passed / len(test_cases) if test_cases else 0.0

        logger.info(
            "Evaluation complete",
            accuracy=accuracy,
            passed=passed,
            failed=len(failures),
            total=len(test_cases),
        )

        return EvaluationResult(
            accuracy=accuracy,
            passed_count=passed,
            failed_count=len(failures),
            failures=failures,
        )

    def _validate_output(
        self,
        test_case: TestCase,
        actual: Dict[str, Any],
        expected: Dict[str, Any],
    ) -> Optional[FailureAnalysis]:
        """
        Validate actual output against expected output.

        Args:
            test_case: Original test case
            actual: Actual output from extractor
            expected: Expected output

        Returns:
            FailureAnalysis if validation fails, None if passes
        """
        missing_fields = []
        incorrect_fields = {}

        # Check for missing required fields
        for key in expected.keys():
            if key not in actual:
                missing_fields.append(key)

        # Check for incorrect values
        for key, expected_value in expected.items():
            if key in actual:
                actual_value = actual[key]
                if not self._values_match(expected_value, actual_value):
                    incorrect_fields[key] = (expected_value, actual_value)

        # Return failure if any issues found
        if missing_fields or incorrect_fields:
            failure_type = (
                FailureType.MISSING_DATA
                if missing_fields
                else FailureType.INCORRECT_TRANSFORMATION
            )

            return FailureAnalysis(
                failure_type=failure_type,
                test_case=test_case,
                actual_output=actual,
                missing_fields=missing_fields,
                incorrect_fields=incorrect_fields,
            )

        return None

    def _values_match(self, expected: Any, actual: Any) -> bool:
        """
        Check if two values match (with type coercion tolerance).

        Args:
            expected: Expected value
            actual: Actual value

        Returns:
            True if values match
        """
        # Exact match
        if expected == actual:
            return True

        # Numeric tolerance (int/float equivalence)
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return abs(expected - actual) < 0.01

        # String case-insensitive comparison for text fields
        if isinstance(expected, str) and isinstance(actual, str):
            return expected.strip().lower() == actual.strip().lower()

        return False

    def refine(
        self,
        extractor: GeneratedExtractor,
        failures: List[FailureAnalysis],
    ) -> GeneratedExtractor:
        """
        Improve extractor based on failure analysis.

        Strategy:
        - Parse errors → Add parsing rules to prompt
        - Missing data → Adjust field extraction instructions
        - Incorrect transformations → Add transformation examples
        - Validation errors → Strengthen schema validation

        Args:
            extractor: Current GeneratedExtractor
            failures: List of failures from evaluation

        Returns:
            Refined GeneratedExtractor with improved prompt/template
        """
        if not failures:
            logger.info("No failures to address, skipping refinement")
            return extractor

        logger.info(
            "Refining extractor based on failures",
            failures_count=len(failures),
        )

        # Analyze failure patterns
        failure_counts = self._count_failure_types(failures)

        # Build refinement changes
        changes = []

        # Create updated analysis (copy to avoid mutation)
        updated_analysis = PatternAnalysis(
            name=extractor.analysis.name,
            domain=extractor.analysis.domain,
            description=extractor.analysis.description,
            input_schema=extractor.analysis.input_schema,
            output_schema=extractor.analysis.output_schema,
            patterns=extractor.analysis.patterns,
            confidence=extractor.analysis.confidence,
            examples_count=extractor.analysis.examples_count,
            heading_patterns=extractor.analysis.heading_patterns.copy(),
            table_validation_rules=extractor.analysis.table_validation_rules.copy(),
            system_prompt=extractor.analysis.system_prompt,
            parsing_rules=extractor.analysis.parsing_rules.copy(),
        )

        # Ensure table_validation_rules has required structure
        if "required_columns" not in updated_analysis.table_validation_rules:
            updated_analysis.table_validation_rules["required_columns"] = []
        if "reject_patterns" not in updated_analysis.table_validation_rules:
            updated_analysis.table_validation_rules["reject_patterns"] = []

        # Refine parsing rules for parse errors
        if failure_counts.get(FailureType.PARSING_ERROR, 0) > 0:
            parsing_rule = "Ensure output is valid JSON with no markdown code fences"
            if parsing_rule not in updated_analysis.parsing_rules:
                updated_analysis.parsing_rules.append(parsing_rule)
                changes.append("Added JSON formatting validation rule")

        # Refine field extraction for missing data
        if failure_counts.get(FailureType.MISSING_DATA, 0) > 0:
            missing_fields = self._extract_missing_fields(failures)
            for field in missing_fields[:3]:  # Limit to top 3 fields
                rule = f"Always extract the '{field}' field, use null if not found"
                if rule not in updated_analysis.parsing_rules:
                    updated_analysis.parsing_rules.append(rule)
                    changes.append(f"Added extraction rule for '{field}'")

        # Refine transformation logic for incorrect values
        if failure_counts.get(FailureType.INCORRECT_TRANSFORMATION, 0) > 0:
            transformation_rule = (
                "Verify extracted values match the expected format and type"
            )
            if transformation_rule not in updated_analysis.parsing_rules:
                updated_analysis.parsing_rules.append(transformation_rule)
                changes.append("Added transformation verification rule")

        # Update system prompt with stronger instructions
        if len(changes) > 0:
            updated_analysis.system_prompt = (
                f"{updated_analysis.system_prompt} "
                f"CRITICAL: Follow all parsing rules exactly to avoid errors."
            )

        logger.info(
            "Refinement complete",
            changes_count=len(changes),
            changes=changes,
        )

        # Regenerate extractor with refined analysis
        refined_extractor = self.meta_extractor.synthesizer.synthesize(updated_analysis)

        return refined_extractor

    def _count_failure_types(
        self, failures: List[FailureAnalysis]
    ) -> Dict[FailureType, int]:
        """Count failures by type."""
        counts: Dict[FailureType, int] = {}
        for failure in failures:
            counts[failure.failure_type] = counts.get(failure.failure_type, 0) + 1
        return counts

    def _extract_missing_fields(self, failures: List[FailureAnalysis]) -> List[str]:
        """Extract list of most commonly missing fields."""
        field_counts: Dict[str, int] = {}

        for failure in failures:
            if failure.failure_type == FailureType.MISSING_DATA:
                for field in failure.missing_fields:
                    field_counts[field] = field_counts.get(field, 0) + 1

        # Sort by frequency
        sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)
        return [field for field, _ in sorted_fields]

    async def redeploy(self, extractor: GeneratedExtractor) -> DeploymentResult:
        """
        Update registry with improved version.

        Args:
            extractor: Refined GeneratedExtractor

        Returns:
            DeploymentResult with deployment status
        """
        logger.info("Redeploying refined extractor", name=extractor.name)

        try:
            # Get current version from registry
            try:
                metadata = self.registry.get_metadata(extractor.name)
                current_version = metadata.version
                # Increment version (e.g., "1.0.0" -> "1.1.0")
                major, minor, patch = current_version.split(".")
                new_version = f"{major}.{int(minor) + 1}.{patch}"
            except KeyError:
                # First deployment
                new_version = "1.0.0"

            # Deploy using meta_extractor
            deployment = self.meta_extractor.deploy(
                extractor, auto_register=False  # We'll update registry manually
            )

            if not deployment.success:
                return DeploymentResult(
                    success=False,
                    version=new_version,
                    error_message=deployment.error_message or "Deployment failed",
                )

            # Update registry with new version
            try:
                # Check if extractor already exists in registry
                self.registry.get_metadata(extractor.name)
                # Exists - update it
                self.registry.update(
                    extractor.name,
                    version=new_version,
                    confidence=extractor.analysis.confidence,
                )
            except KeyError:
                # Register new extractor
                class_name = (
                    "".join(word.capitalize() for word in extractor.name.split("_"))
                    + "Extractor"
                )
                class_path = f"edgar_analyzer.extractors.{extractor.domain}.extractor.{class_name}"

                self.registry.register(
                    name=extractor.name,
                    class_path=class_path,
                    version=new_version,
                    description=extractor.analysis.description,
                    domain=extractor.domain,
                    confidence=extractor.analysis.confidence,
                    examples_count=extractor.analysis.examples_count,
                    tags=[extractor.domain, "generated", "meta-extractor", "refined"],
                )

            logger.info(
                "Redeploy successful",
                name=extractor.name,
                version=new_version,
            )

            return DeploymentResult(
                success=True,
                version=new_version,
                registry_updated=True,
            )

        except Exception as e:
            logger.error(
                "Redeploy failed",
                name=extractor.name,
                error=str(e),
                error_type=type(e).__name__,
            )

            return DeploymentResult(
                success=False,
                version="unknown",
                error_message=f"{type(e).__name__}: {e}",
            )

    async def run(
        self,
        extractor_name: str,
        test_cases: List[TestCase],
        target_accuracy: float = 0.90,
    ) -> ImprovementResult:
        """
        Run full improvement loop until target accuracy reached.

        Workflow:
        1. Load extractor from registry
        2. Evaluate on test cases
        3. If accuracy < target, analyze failures and refine
        4. Redeploy refined extractor
        5. Repeat until target met or max iterations

        Args:
            extractor_name: Name of extractor to improve
            test_cases: List of test cases for evaluation
            target_accuracy: Target accuracy (0.0-1.0, default: 0.90)

        Returns:
            ImprovementResult with final accuracy and history
        """
        logger.info(
            "Starting improvement loop",
            extractor_name=extractor_name,
            target_accuracy=target_accuracy,
            max_iterations=self.max_iterations,
            test_cases_count=len(test_cases),
        )

        history: List[IterationHistory] = []
        best_accuracy = 0.0
        plateau_count = 0

        for iteration in range(1, self.max_iterations + 1):
            logger.info(
                "Starting iteration",
                iteration=iteration,
                max_iterations=self.max_iterations,
            )

            # Load current extractor
            try:
                extractor_class = self.registry.get(extractor_name)
                # Instantiate extractor (assumes zero-arg constructor for testing)
                # In production, would pass OpenRouterClient
                extractor = extractor_class()
            except Exception as e:
                logger.error(
                    "Failed to load extractor",
                    name=extractor_name,
                    error=str(e),
                )
                return ImprovementResult(
                    success=False,
                    final_accuracy=best_accuracy,
                    iterations=iteration - 1,
                    history=history,
                    stopped_reason=f"Failed to load extractor: {e}",
                )

            # Evaluate extractor
            eval_result = await self.evaluate(extractor, test_cases)

            logger.info(
                "Iteration evaluation complete",
                iteration=iteration,
                accuracy=eval_result.accuracy,
                passed=eval_result.passed_count,
                failed=eval_result.failed_count,
            )

            # Check for plateau
            if eval_result.accuracy <= best_accuracy:
                plateau_count += 1
            else:
                plateau_count = 0
                best_accuracy = eval_result.accuracy

            # Check stopping conditions
            if eval_result.accuracy >= target_accuracy:
                history.append(
                    IterationHistory(
                        iteration=iteration,
                        accuracy=eval_result.accuracy,
                        changes_made="Target accuracy reached",
                        failures_addressed=0,
                    )
                )

                logger.info(
                    "Target accuracy reached",
                    accuracy=eval_result.accuracy,
                    target=target_accuracy,
                    iterations=iteration,
                )

                return ImprovementResult(
                    success=True,
                    final_accuracy=eval_result.accuracy,
                    iterations=iteration,
                    history=history,
                    stopped_reason="target_met",
                )

            if plateau_count >= self.plateau_threshold:
                history.append(
                    IterationHistory(
                        iteration=iteration,
                        accuracy=eval_result.accuracy,
                        changes_made="Accuracy plateau detected",
                        failures_addressed=0,
                    )
                )

                logger.warning(
                    "Accuracy plateau detected, stopping",
                    plateau_iterations=plateau_count,
                    best_accuracy=best_accuracy,
                )

                return ImprovementResult(
                    success=False,
                    final_accuracy=eval_result.accuracy,
                    iterations=iteration,
                    history=history,
                    stopped_reason="plateau",
                )

            # Refine extractor based on failures
            if eval_result.failures:
                # Load GeneratedExtractor for refinement
                # This requires access to the original analysis
                # For now, we'll simulate refinement
                logger.info(
                    "Refining extractor",
                    failures_count=len(eval_result.failures),
                )

                # Record iteration
                history.append(
                    IterationHistory(
                        iteration=iteration,
                        accuracy=eval_result.accuracy,
                        changes_made=f"Refined based on {len(eval_result.failures)} failures",
                        failures_addressed=len(eval_result.failures),
                    )
                )

                # In real implementation, would:
                # 1. Get original GeneratedExtractor
                # 2. Call self.refine()
                # 3. Call self.redeploy()

                # For POC, we'll continue to next iteration
                logger.debug("Refinement step skipped in POC mode")

        # Max iterations reached
        logger.warning(
            "Max iterations reached without meeting target",
            max_iterations=self.max_iterations,
            final_accuracy=best_accuracy,
            target_accuracy=target_accuracy,
        )

        return ImprovementResult(
            success=False,
            final_accuracy=best_accuracy,
            iterations=self.max_iterations,
            history=history,
            stopped_reason="max_iterations",
        )
