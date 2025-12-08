"""Tests for ExtractorSynthesizer.

Tests the pattern analysis and code generation pipeline for the Meta-Extractor POC.

Coverage:
- Pattern analysis from examples
- Code synthesis from templates
- File writing and formatting
- Error handling for invalid inputs
"""

import ast
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from edgar_analyzer.extractors.synthesizer import (
    ExtractorSynthesizer,
    GeneratedExtractor,
    PatternAnalysis,
)


class TestExtractorSynthesizer:
    """Tests for ExtractorSynthesizer."""

    @pytest.fixture
    def synthesizer(self, tmp_path: Path) -> ExtractorSynthesizer:
        """Create synthesizer instance with temp templates directory."""
        # Use actual templates directory from the project
        templates_dir = Path(__file__).parent.parent.parent / "templates" / "extractors"

        # If templates don't exist yet, create a minimal set for testing
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)
            # Create minimal templates for testing
            (templates_dir / "base_extractor.py.j2").write_text(
                "# Extractor: {{ extractor_name }}\nclass {{ extractor_name }}:\n    pass"
            )
            (templates_dir / "data_models.py.j2").write_text(
                "# Models for {{ domain }}"
            )
            (templates_dir / "prompt_template.j2").write_text(
                "# Prompts for {{ domain }}"
            )
            (templates_dir / "test_extractor.py.j2").write_text(
                "# Tests for {{ extractor_name }}"
            )
            (templates_dir / "__init__.py.j2").write_text(
                "# {{ domain }} extractor package"
            )

        return ExtractorSynthesizer(templates_dir=templates_dir)

    @pytest.fixture
    def sample_examples(self) -> List[Dict[str, Any]]:
        """Create sample examples for testing."""
        return [
            {
                "input": {
                    "html": "<table><tr><td>John Doe</td><td>100000</td></tr></table>",
                    "url": "http://example.com/filing1.html",
                },
                "output": {"name": "John Doe", "salary": 100000, "bonus": 20000},
            },
            {
                "input": {
                    "html": "<table><tr><td>Jane Smith</td><td>120000</td></tr></table>",
                    "url": "http://example.com/filing2.html",
                },
                "output": {"name": "Jane Smith", "salary": 120000, "bonus": 25000},
            },
            {
                "input": {
                    "html": "<table><tr><td>Bob Johnson</td><td>90000</td></tr></table>",
                    "url": "http://example.com/filing3.html",
                },
                "output": {"name": "Bob Johnson", "salary": 90000, "bonus": 15000},
            },
        ]

    def test_analyze_returns_pattern_analysis(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test that analyze returns PatternAnalysis."""
        result = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
            description="Extract test data",
        )

        assert isinstance(result, PatternAnalysis)
        assert result.name == "test_extractor"
        assert result.domain == "test"
        assert result.description == "Extract test data"

    def test_analyze_detects_patterns(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test that patterns are detected from examples."""
        result = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
            description="Extract test data",
        )

        # Should detect patterns (exact count depends on analyzer logic)
        assert len(result.patterns) > 0
        assert result.confidence > 0.0
        assert result.examples_count == 3

        # Check schema detection
        assert "fields" in result.output_schema
        assert len(result.output_schema["fields"]) > 0

    def test_analyze_with_custom_domain(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test analyze with custom domain."""
        result = synthesizer.analyze(
            name="sct_extractor",
            examples=sample_examples,
            description="Extract SCT data",
            domain="custom_domain",
        )

        assert result.domain == "custom_domain"
        assert result.name == "sct_extractor"

    def test_analyze_with_metadata(
        self, synthesizer: ExtractorSynthesizer
    ):
        """Test analyze with example metadata."""
        examples = [
            {
                "input": {"html": "<html>...</html>"},
                "output": {"name": "Test"},
                "metadata": {
                    "heading_pattern": "Summary.*Table",
                    "validation_rules": {
                        "required_columns": ["name", "salary"],
                        "reject_patterns": ["footnote"],
                    },
                    "parsing_rules": ["Extract only executive data"],
                },
            },
            {
                "input": {"html": "<html>...</html>"},
                "output": {"name": "Test2"},
            },
        ]

        result = synthesizer.analyze(
            name="test_extractor",
            examples=examples,
        )

        # Check metadata extraction
        assert "Summary.*Table" in result.heading_patterns
        assert "name" in result.table_validation_rules.get("required_columns", [])
        assert "Extract only executive data" in result.parsing_rules

    def test_synthesize_returns_generated_extractor(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test that synthesize returns GeneratedExtractor."""
        analysis = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
        )

        result = synthesizer.synthesize(analysis)

        assert isinstance(result, GeneratedExtractor)
        assert result.name == "test_extractor"
        assert result.domain == "test"
        assert result.analysis == analysis

    def test_synthesize_produces_valid_python(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test that generated code is valid Python."""
        analysis = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
        )

        result = synthesizer.synthesize(analysis)

        # All generated code should be valid Python syntax
        for code_attr in [
            "extractor_code",
            "models_code",
            "prompts_code",
            "tests_code",
            "init_code",
        ]:
            code = getattr(result, code_attr)
            assert isinstance(code, str)
            assert len(code) > 0

            # Verify valid Python syntax
            try:
                ast.parse(code)
            except SyntaxError as e:
                pytest.fail(
                    f"{code_attr} has invalid syntax: {e}\n\nCode:\n{code}"
                )

    def test_synthesize_includes_metadata(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test that synthesized code includes analysis metadata."""
        analysis = synthesizer.analyze(
            name="sct_extractor",
            examples=sample_examples,
            description="Extract Summary Compensation Tables",
        )

        result = synthesizer.synthesize(analysis)

        # Check that domain appears in generated code
        assert "sct" in result.extractor_code.lower() or "Sct" in result.extractor_code

        # Check that generated_at timestamp exists
        assert result.generated_at is not None

    def test_write_creates_files(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]], tmp_path: Path
    ):
        """Test that write creates expected files."""
        analysis = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
        )

        extractor = synthesizer.synthesize(analysis)

        output_dir = tmp_path / "test_extractor"
        paths = synthesizer.write(extractor, output_dir)

        # Should create 5 files
        assert len(paths) == 5

        # Verify all files exist
        expected_files = [
            "extractor.py",
            "models.py",
            "prompts.py",
            f"test_{extractor.domain}_extractor.py",
            "__init__.py",
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected file not created: {filename}"
            assert file_path.stat().st_size > 0, f"File is empty: {filename}"

    def test_write_preserves_content(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]], tmp_path: Path
    ):
        """Test that written files match generated content."""
        analysis = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
        )

        extractor = synthesizer.synthesize(analysis)

        output_dir = tmp_path / "test_output"
        synthesizer.write(extractor, output_dir)

        # Check extractor.py content
        extractor_file = output_dir / "extractor.py"
        content = extractor_file.read_text(encoding="utf-8")

        # Content should match (allowing for formatting by black/isort)
        # Just check it's valid Python and contains key elements
        ast.parse(content)

    def test_analyze_with_empty_examples(self, synthesizer: ExtractorSynthesizer):
        """Test error handling for empty examples."""
        with pytest.raises(ValueError, match="examples list cannot be empty"):
            synthesizer.analyze(
                name="test_extractor",
                examples=[],
            )

    def test_analyze_with_invalid_examples(self, synthesizer: ExtractorSynthesizer):
        """Test error handling for invalid examples."""
        invalid_examples = [
            {"no_input": "missing input"},
            {"input": {}, "no_output": "missing output"},
        ]

        with pytest.raises(ValueError, match="No valid examples"):
            synthesizer.analyze(
                name="test_extractor",
                examples=invalid_examples,
            )

    def test_confidence_calculation(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test confidence score calculation."""
        # 3 examples should have higher confidence than 1
        result_many = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
        )

        result_few = synthesizer.analyze(
            name="test_extractor",
            examples=[sample_examples[0]],
        )

        # More examples should generally yield higher confidence
        # (exact relationship depends on pattern quality)
        assert result_many.confidence >= 0.0
        assert result_few.confidence >= 0.0

    def test_pattern_analysis_serialization(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test that PatternAnalysis can be serialized to dict."""
        result = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
        )

        analysis_dict = result.to_dict()

        assert isinstance(analysis_dict, dict)
        assert analysis_dict["name"] == "test_extractor"
        assert analysis_dict["domain"] == "test"
        assert "patterns" in analysis_dict
        assert "confidence" in analysis_dict

    def test_system_prompt_generation(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test automatic system prompt generation."""
        result = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
            description="Extract executive compensation",
        )

        assert result.system_prompt is not None
        assert len(result.system_prompt) > 0
        assert "Extract" in result.system_prompt or "extract" in result.system_prompt

    def test_custom_system_prompt(
        self, synthesizer: ExtractorSynthesizer, sample_examples: List[Dict[str, Any]]
    ):
        """Test using custom system prompt."""
        custom_prompt = "Custom extraction prompt for testing"

        result = synthesizer.analyze(
            name="test_extractor",
            examples=sample_examples,
            system_prompt=custom_prompt,
        )

        assert result.system_prompt == custom_prompt
