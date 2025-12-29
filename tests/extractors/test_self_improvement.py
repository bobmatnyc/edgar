"""Tests for SelfImprovementLoop.

Tests the Phase 4 self-improvement system including:
- Evaluation on test cases
- Failure analysis and categorization
- Prompt refinement based on failures
- Iterative improvement loop
- Plateau detection

Coverage:
- evaluate() - Run test cases and compute accuracy
- refine() - Improve extractor based on failures
- redeploy() - Update registry with new version
- run() - Full improvement loop
- Stopping conditions (target met, max iterations, plateau)
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from edgar_analyzer.extractors.meta_extractor import MetaExtractor
from edgar_analyzer.extractors.registry import ExtractorRegistry
from edgar_analyzer.extractors.self_improvement import (
    DeploymentResult,
    EvaluationResult,
    FailureAnalysis,
    FailureType,
    ImprovementResult,
    IterationHistory,
    SelfImprovementLoop,
    TestCase,
)
from edgar_analyzer.extractors.synthesizer import (
    GeneratedExtractor,
    PatternAnalysis,
)
from extract_transform_platform.core.base import IDataExtractor


# Mock extractor for testing
class MockExtractor(IDataExtractor):
    """Mock extractor for testing."""

    def __init__(self, responses: List[Dict[str, Any]] = None):
        """Initialize with canned responses."""
        self.responses = responses or []
        self.call_count = 0

    async def extract(self, **kwargs) -> Dict[str, Any]:
        """Return canned response or raise error."""
        if self.call_count >= len(self.responses):
            return {"name": "default", "value": 0}

        response = self.responses[self.call_count]
        self.call_count += 1

        if isinstance(response, Exception):
            raise response

        return response


class TestSelfImprovementLoop:
    """Tests for SelfImprovementLoop."""

    @pytest.fixture
    def meta_extractor(self, tmp_path: Path) -> MetaExtractor:
        """Create MetaExtractor with temp output directory."""
        return MetaExtractor(output_base=tmp_path)

    @pytest.fixture
    def improvement_loop(self, meta_extractor: MetaExtractor) -> SelfImprovementLoop:
        """Create SelfImprovementLoop instance."""
        return SelfImprovementLoop(meta_extractor, max_iterations=5)

    @pytest.fixture
    def sample_test_cases(self) -> List[TestCase]:
        """Create sample test cases."""
        return [
            TestCase(
                input={"html": "<table><tr><td>Alice</td><td>100000</td></tr></table>"},
                expected_output={"name": "Alice", "value": 100000},
                description="Test case 1: Alice",
            ),
            TestCase(
                input={"html": "<table><tr><td>Bob</td><td>200000</td></tr></table>"},
                expected_output={"name": "Bob", "value": 200000},
                description="Test case 2: Bob",
            ),
            TestCase(
                input={"html": "<table><tr><td>Carol</td><td>300000</td></tr></table>"},
                expected_output={"name": "Carol", "value": 300000},
                description="Test case 3: Carol",
            ),
        ]

    @pytest.fixture
    def sample_pattern_analysis(self) -> PatternAnalysis:
        """Create sample PatternAnalysis for testing."""
        return PatternAnalysis(
            name="test_extractor",
            domain="test",
            description="Test extractor",
            input_schema={"fields": [], "is_nested": False, "has_arrays": False},
            output_schema={
                "fields": [
                    {
                        "path": "name",
                        "type": "str",
                        "required": True,
                        "nullable": False,
                        "nested_level": 0,
                        "is_array": False,
                    },
                    {
                        "path": "value",
                        "type": "int",
                        "required": True,
                        "nullable": False,
                        "nested_level": 0,
                        "is_array": False,
                    },
                ],
                "is_nested": False,
                "has_arrays": False,
            },
            patterns=[],
            confidence=0.85,
            examples_count=3,
            heading_patterns=[],
            table_validation_rules={
                "required_columns": [],
                "reject_patterns": [],
            },
            parsing_rules=[],
            system_prompt="Extract data from HTML tables",
        )

    # ========== Test TestCase ==========

    def test_test_case_creation(self):
        """Test creating TestCase dataclass."""
        test_case = TestCase(
            input={"html": "<html>"},
            expected_output={"name": "Test"},
            description="Test case",
        )

        assert test_case.input == {"html": "<html>"}
        assert test_case.expected_output == {"name": "Test"}
        assert test_case.description == "Test case"

    # ========== Test evaluate() ==========

    @pytest.mark.asyncio
    async def test_evaluate_all_pass(
        self, improvement_loop: SelfImprovementLoop, sample_test_cases: List[TestCase]
    ):
        """Test evaluation when all test cases pass."""
        # Mock extractor that returns expected outputs
        extractor = MockExtractor(
            responses=[
                {"name": "Alice", "value": 100000},
                {"name": "Bob", "value": 200000},
                {"name": "Carol", "value": 300000},
            ]
        )

        result = await improvement_loop.evaluate(extractor, sample_test_cases)

        assert result.accuracy == 1.0
        assert result.passed_count == 3
        assert result.failed_count == 0
        assert len(result.failures) == 0

    @pytest.mark.asyncio
    async def test_evaluate_some_failures(
        self, improvement_loop: SelfImprovementLoop, sample_test_cases: List[TestCase]
    ):
        """Test evaluation with some failures."""
        # Mock extractor with 1 success, 2 failures
        extractor = MockExtractor(
            responses=[
                {"name": "Alice", "value": 100000},  # Correct
                {"name": "Wrong", "value": 999},  # Incorrect
                {"name": "Bob"},  # Missing field
            ]
        )

        result = await improvement_loop.evaluate(extractor, sample_test_cases)

        assert result.accuracy == pytest.approx(1 / 3)
        assert result.passed_count == 1
        assert result.failed_count == 2
        assert len(result.failures) == 2

    @pytest.mark.asyncio
    async def test_evaluate_missing_data(self, improvement_loop: SelfImprovementLoop):
        """Test evaluation when extractor returns None."""
        test_cases = [
            TestCase(
                input={"html": "<html>"},
                expected_output={"name": "Test"},
            )
        ]

        extractor = MockExtractor(responses=[None])

        result = await improvement_loop.evaluate(extractor, test_cases)

        assert result.accuracy == 0.0
        assert result.failed_count == 1
        assert result.failures[0].failure_type == FailureType.MISSING_DATA

    @pytest.mark.asyncio
    async def test_evaluate_exception(self, improvement_loop: SelfImprovementLoop):
        """Test evaluation when extractor raises exception."""
        test_cases = [
            TestCase(
                input={"html": "<html>"},
                expected_output={"name": "Test"},
            )
        ]

        extractor = MockExtractor(responses=[ValueError("Test error")])

        result = await improvement_loop.evaluate(extractor, test_cases)

        assert result.accuracy == 0.0
        assert result.failed_count == 1
        assert result.failures[0].failure_type == FailureType.EXCEPTION
        assert "Test error" in result.failures[0].error_message

    @pytest.mark.asyncio
    async def test_evaluate_empty_test_cases(
        self, improvement_loop: SelfImprovementLoop
    ):
        """Test evaluation with no test cases."""
        extractor = MockExtractor()

        result = await improvement_loop.evaluate(extractor, [])

        assert result.accuracy == 0.0
        assert result.passed_count == 0
        assert result.failed_count == 0

    # ========== Test _validate_output() ==========

    def test_validate_output_exact_match(self, improvement_loop: SelfImprovementLoop):
        """Test validation with exact match."""
        test_case = TestCase(
            input={},
            expected_output={"name": "Alice", "value": 100},
        )

        failure = improvement_loop._validate_output(
            test_case,
            actual={"name": "Alice", "value": 100},
            expected={"name": "Alice", "value": 100},
        )

        assert failure is None

    def test_validate_output_missing_field(self, improvement_loop: SelfImprovementLoop):
        """Test validation with missing field."""
        test_case = TestCase(
            input={},
            expected_output={"name": "Alice", "value": 100},
        )

        failure = improvement_loop._validate_output(
            test_case,
            actual={"name": "Alice"},
            expected={"name": "Alice", "value": 100},
        )

        assert failure is not None
        assert failure.failure_type == FailureType.MISSING_DATA
        assert "value" in failure.missing_fields

    def test_validate_output_incorrect_value(
        self, improvement_loop: SelfImprovementLoop
    ):
        """Test validation with incorrect value."""
        test_case = TestCase(
            input={},
            expected_output={"name": "Alice", "value": 100},
        )

        failure = improvement_loop._validate_output(
            test_case,
            actual={"name": "Alice", "value": 200},
            expected={"name": "Alice", "value": 100},
        )

        assert failure is not None
        assert failure.failure_type == FailureType.INCORRECT_TRANSFORMATION
        assert "value" in failure.incorrect_fields
        assert failure.incorrect_fields["value"] == (100, 200)

    # ========== Test _values_match() ==========

    def test_values_match_exact(self, improvement_loop: SelfImprovementLoop):
        """Test exact value matching."""
        assert improvement_loop._values_match(100, 100) is True
        assert improvement_loop._values_match("Alice", "Alice") is True

    def test_values_match_numeric_tolerance(
        self, improvement_loop: SelfImprovementLoop
    ):
        """Test numeric matching with tolerance."""
        assert improvement_loop._values_match(100, 100.0) is True
        assert improvement_loop._values_match(100.005, 100.0) is True
        assert improvement_loop._values_match(100, 200) is False

    def test_values_match_string_case_insensitive(
        self, improvement_loop: SelfImprovementLoop
    ):
        """Test string matching (case-insensitive)."""
        assert improvement_loop._values_match("Alice", "alice") is True
        assert improvement_loop._values_match("Alice", "  Alice  ") is True
        assert improvement_loop._values_match("Alice", "Bob") is False

    # ========== Test refine() ==========

    def test_refine_no_failures(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
    ):
        """Test refinement with no failures returns same extractor."""
        extractor = GeneratedExtractor(
            name="test_extractor",
            domain="test",
            extractor_code="",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        refined = improvement_loop.refine(extractor, [])

        # Should return same extractor (no changes)
        assert refined.name == extractor.name

    def test_refine_parsing_errors(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
    ):
        """Test refinement adds parsing rules for parse errors."""
        extractor = GeneratedExtractor(
            name="test_extractor",
            domain="test",
            extractor_code="",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        failures = [
            FailureAnalysis(
                failure_type=FailureType.PARSING_ERROR,
                test_case=TestCase(input={}, expected_output={}),
                error_message="JSON parse error",
            )
        ]

        refined = improvement_loop.refine(extractor, failures)

        # Should add JSON formatting rule
        assert any("valid JSON" in rule for rule in refined.analysis.parsing_rules)

    def test_refine_missing_data(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
    ):
        """Test refinement adds field extraction rules for missing data."""
        extractor = GeneratedExtractor(
            name="test_extractor",
            domain="test",
            extractor_code="",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        failures = [
            FailureAnalysis(
                failure_type=FailureType.MISSING_DATA,
                test_case=TestCase(input={}, expected_output={"name": "Test"}),
                missing_fields=["name"],
            )
        ]

        refined = improvement_loop.refine(extractor, failures)

        # Should add extraction rule for missing field
        assert any("name" in rule for rule in refined.analysis.parsing_rules)

    def test_refine_incorrect_transformation(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
    ):
        """Test refinement adds verification rules for incorrect transformations."""
        extractor = GeneratedExtractor(
            name="test_extractor",
            domain="test",
            extractor_code="",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        failures = [
            FailureAnalysis(
                failure_type=FailureType.INCORRECT_TRANSFORMATION,
                test_case=TestCase(input={}, expected_output={"value": 100}),
                incorrect_fields={"value": (100, 200)},
            )
        ]

        refined = improvement_loop.refine(extractor, failures)

        # Should add transformation verification rule
        assert any("Verify" in rule for rule in refined.analysis.parsing_rules)

    # ========== Test redeploy() ==========

    @pytest.mark.asyncio
    async def test_redeploy_new_extractor(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
        tmp_path: Path,
    ):
        """Test redeploying a new extractor."""
        extractor = GeneratedExtractor(
            name="new_extractor",
            domain="test",
            extractor_code="class NewExtractor: pass",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        # Mock deployment and registry
        with (
            patch.object(
                improvement_loop.meta_extractor,
                "deploy",
                return_value=MagicMock(
                    success=True,
                    extractor_path=tmp_path,
                    registered=False,
                ),
            ),
            patch.object(
                improvement_loop.registry,
                "register",
                return_value=MagicMock(),
            ),
        ):
            result = await improvement_loop.redeploy(extractor)

        assert result.success is True
        assert result.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_redeploy_existing_extractor_increments_version(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
        tmp_path: Path,
    ):
        """Test redeploying existing extractor increments version."""
        # Mock existing metadata
        from edgar_analyzer.extractors.registry import ExtractorMetadata

        existing_metadata = ExtractorMetadata(
            name="existing_extractor",
            class_path="edgar_analyzer.extractors.test.extractor.TestExtractor",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        extractor = GeneratedExtractor(
            name="existing_extractor",
            domain="test",
            extractor_code="class ExistingExtractor: pass",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        # Mock deployment and registry methods
        with (
            patch.object(
                improvement_loop.meta_extractor,
                "deploy",
                return_value=MagicMock(
                    success=True,
                    extractor_path=tmp_path,
                    registered=False,
                ),
            ),
            patch.object(
                improvement_loop.registry,
                "get_metadata",
                return_value=existing_metadata,
            ),
            patch.object(
                improvement_loop.registry,
                "update",
                return_value=MagicMock(),
            ),
        ):
            result = await improvement_loop.redeploy(extractor)

        assert result.success is True
        assert result.version == "1.1.0"  # Incremented minor version

    @pytest.mark.asyncio
    async def test_redeploy_deployment_failure(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_pattern_analysis: PatternAnalysis,
    ):
        """Test redeploy when deployment fails."""
        extractor = GeneratedExtractor(
            name="fail_extractor",
            domain="test",
            extractor_code="",
            models_code="",
            prompts_code="",
            tests_code="",
            init_code="",
            analysis=sample_pattern_analysis,
        )

        # Mock deployment failure
        with patch.object(
            improvement_loop.meta_extractor,
            "deploy",
            return_value=MagicMock(
                success=False,
                error_message="Deploy error",
            ),
        ):
            result = await improvement_loop.redeploy(extractor)

        assert result.success is False
        assert "Deploy error" in result.error_message

    # ========== Test run() - Full improvement loop ==========

    @pytest.mark.asyncio
    async def test_run_target_accuracy_reached(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_test_cases: List[TestCase],
    ):
        """Test run stops when target accuracy is reached."""
        # Mock extractor that achieves 100% accuracy
        mock_extractor = MockExtractor(
            responses=[
                {"name": "Alice", "value": 100000},
                {"name": "Bob", "value": 200000},
                {"name": "Carol", "value": 300000},
            ]
        )

        # Mock registry.get to return our mock extractor
        with patch.object(
            improvement_loop.registry,
            "get",
            return_value=lambda: mock_extractor,
        ):
            result = await improvement_loop.run(
                extractor_name="test_extractor",
                test_cases=sample_test_cases,
                target_accuracy=0.90,
            )

        assert result.success is True
        assert result.final_accuracy == 1.0
        assert result.iterations == 1
        assert result.stopped_reason == "target_met"

    @pytest.mark.asyncio
    async def test_run_max_iterations_reached(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_test_cases: List[TestCase],
    ):
        """Test run stops at max iterations."""
        # Mock extractor that never reaches target
        mock_extractor = MockExtractor(
            responses=[
                {"name": "Alice", "value": 100000},
                {"name": "Wrong", "value": 999},
                {"name": "Wrong", "value": 999},
            ]
        )

        # Mock registry.get to return our mock extractor
        with patch.object(
            improvement_loop.registry,
            "get",
            return_value=lambda: mock_extractor,
        ):
            # Set low max iterations for faster test
            improvement_loop.max_iterations = 2

            result = await improvement_loop.run(
                extractor_name="test_extractor",
                test_cases=sample_test_cases,
                target_accuracy=0.90,
            )

        assert result.success is False
        assert result.iterations == 2
        assert result.stopped_reason == "max_iterations"

    @pytest.mark.asyncio
    async def test_run_plateau_detection(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_test_cases: List[TestCase],
    ):
        """Test run stops when accuracy plateaus."""
        # Mock extractor with constant low accuracy
        mock_extractor = MockExtractor(
            responses=[
                {"name": "Alice", "value": 100000},
                {"name": "Wrong", "value": 999},
                {"name": "Wrong", "value": 999},
            ]
        )

        # Mock registry.get to return our mock extractor
        with patch.object(
            improvement_loop.registry,
            "get",
            return_value=lambda: mock_extractor,
        ):
            # Set plateau threshold to 2 iterations
            improvement_loop.plateau_threshold = 2

            result = await improvement_loop.run(
                extractor_name="test_extractor",
                test_cases=sample_test_cases,
                target_accuracy=0.90,
            )

        assert result.success is False
        assert result.stopped_reason == "plateau"

    @pytest.mark.asyncio
    async def test_run_extractor_load_failure(
        self,
        improvement_loop: SelfImprovementLoop,
        sample_test_cases: List[TestCase],
    ):
        """Test run handles extractor load failure."""
        # Mock registry.get to raise error
        with patch.object(
            improvement_loop.registry,
            "get",
            side_effect=KeyError("Extractor not found"),
        ):
            result = await improvement_loop.run(
                extractor_name="missing_extractor",
                test_cases=sample_test_cases,
                target_accuracy=0.90,
            )

        assert result.success is False
        assert "Failed to load extractor" in result.stopped_reason

    # ========== Test FailureAnalysis ==========

    def test_failure_analysis_creation(self):
        """Test creating FailureAnalysis dataclass."""
        test_case = TestCase(
            input={"html": "<html>"},
            expected_output={"name": "Test"},
        )

        failure = FailureAnalysis(
            failure_type=FailureType.PARSING_ERROR,
            test_case=test_case,
            error_message="Parse error",
        )

        assert failure.failure_type == FailureType.PARSING_ERROR
        assert failure.test_case == test_case
        assert failure.error_message == "Parse error"

    # ========== Test EvaluationResult ==========

    def test_evaluation_result_total_count(self):
        """Test EvaluationResult.total_count property."""
        result = EvaluationResult(
            accuracy=0.6,
            passed_count=6,
            failed_count=4,
        )

        assert result.total_count == 10

    # ========== Test IterationHistory ==========

    def test_iteration_history_creation(self):
        """Test creating IterationHistory dataclass."""
        history = IterationHistory(
            iteration=1,
            accuracy=0.85,
            changes_made="Added validation rules",
            failures_addressed=3,
        )

        assert history.iteration == 1
        assert history.accuracy == 0.85
        assert history.changes_made == "Added validation rules"
        assert history.failures_addressed == 3
        assert history.timestamp  # Should have default timestamp

    # ========== Test ImprovementResult ==========

    def test_improvement_result_creation(self):
        """Test creating ImprovementResult dataclass."""
        history = [
            IterationHistory(
                iteration=1,
                accuracy=0.7,
                changes_made="Initial",
                failures_addressed=0,
            ),
            IterationHistory(
                iteration=2,
                accuracy=0.9,
                changes_made="Refined",
                failures_addressed=2,
            ),
        ]

        result = ImprovementResult(
            success=True,
            final_accuracy=0.9,
            iterations=2,
            history=history,
            stopped_reason="target_met",
        )

        assert result.success is True
        assert result.final_accuracy == 0.9
        assert result.iterations == 2
        assert len(result.history) == 2
        assert result.stopped_reason == "target_met"

    # ========== Test DeploymentResult ==========

    def test_deployment_result_creation(self):
        """Test creating DeploymentResult dataclass."""
        result = DeploymentResult(
            success=True,
            version="1.1.0",
            registry_updated=True,
        )

        assert result.success is True
        assert result.version == "1.1.0"
        assert result.registry_updated is True
        assert result.error_message == ""
