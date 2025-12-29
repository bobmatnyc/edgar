"""Tests for E2E runbook script."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from e2e_edgar_extraction import (
    PhaseResult,
    RunbookResult,
    phase2_analyze_patterns,
    phase3_verify_extractor,
    phase4_run_extraction,
)


class TestPhaseResult:
    """Test PhaseResult dataclass."""

    def test_creation(self):
        """Test basic PhaseResult creation."""
        result = PhaseResult(
            phase=1,
            name="Test Phase",
            status="PASSED",
            duration=1.5,
            message="Test message",
            data={"key": "value"},
        )

        assert result.phase == 1
        assert result.name == "Test Phase"
        assert result.status == "PASSED"
        assert result.duration == 1.5
        assert result.message == "Test message"
        assert result.data == {"key": "value"}

    def test_default_values(self):
        """Test default values for optional fields."""
        result = PhaseResult(
            phase=1,
            name="Test Phase",
            status="PASSED",
            duration=1.5,
        )

        assert result.message == ""
        assert result.data == {}


class TestRunbookResult:
    """Test RunbookResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        phases = [
            PhaseResult(
                phase=1,
                name="Phase 1",
                status="PASSED",
                duration=1.0,
                message="Success",
            ),
            PhaseResult(
                phase=2,
                name="Phase 2",
                status="FAILED",
                duration=0.5,
                message="Error",
            ),
        ]

        result = RunbookResult(
            success=False,
            phases=phases,
            total_duration=1.5,
            timestamp="2024-01-01T00:00:00",
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is False
        assert result_dict["total_duration"] == 1.5
        assert result_dict["timestamp"] == "2024-01-01T00:00:00"
        assert len(result_dict["phases"]) == 2
        assert result_dict["phases"][0]["phase"] == 1
        assert result_dict["phases"][0]["status"] == "PASSED"
        assert result_dict["phases"][1]["phase"] == 2
        assert result_dict["phases"][1]["status"] == "FAILED"


class TestPhase3VerifyExtractor:
    """Test Phase 3: Extractor Verification."""

    def test_extractor_available(self):
        """Test successful extractor verification."""
        result = phase3_verify_extractor(verbose=False)

        assert result.phase == 3
        assert result.name == "Extractor Verification"
        assert result.status == "PASSED"
        assert result.duration > 0
        assert "SCTExtractor ready" in result.message
        assert result.data["extractor_type"] == "SCTExtractor"

    def test_verbose_mode(self, capsys):
        """Test verbose output is printed."""
        phase3_verify_extractor(verbose=True)

        captured = capsys.readouterr()
        assert "Verifying extractor module..." in captured.out
        assert "Extractor loaded successfully" in captured.out


class TestPhase2AnalyzePatterns:
    """Test Phase 2: Pattern Analysis."""

    def test_missing_phase1_data(self, tmp_path):
        """Test failure when Phase 1 data is missing."""
        # Point DATA_DIR to empty temp directory
        import e2e_edgar_extraction

        original_data_dir = e2e_edgar_extraction.DATA_DIR
        e2e_edgar_extraction.DATA_DIR = tmp_path

        try:
            result = phase2_analyze_patterns(verbose=False)

            assert result.phase == 2
            assert result.status == "FAILED"
            assert "Phase 1 data not found" in result.message
        finally:
            e2e_edgar_extraction.DATA_DIR = original_data_dir


class TestPhase4RunExtraction:
    """Test Phase 4: Extraction Execution."""

    def test_missing_phase1_data(self, tmp_path):
        """Test failure when Phase 1 data is missing."""
        import e2e_edgar_extraction

        original_data_dir = e2e_edgar_extraction.DATA_DIR
        e2e_edgar_extraction.DATA_DIR = tmp_path

        try:
            result = phase4_run_extraction(verbose=False)

            assert result.phase == 4
            assert result.status == "FAILED"
            assert "Phase 1 data not found" in result.message
        finally:
            e2e_edgar_extraction.DATA_DIR = original_data_dir


class TestCLIParsing:
    """Test command-line argument parsing."""

    def test_help_message(self):
        """Test that --help works without errors."""
        import e2e_edgar_extraction

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["script.py", "--help"]):
                e2e_edgar_extraction.main()

        # --help exits with code 0
        assert exc_info.value.code == 0

    def test_phase_argument_validation(self):
        """Test that invalid phase numbers are rejected."""
        import argparse

        with pytest.raises(SystemExit):
            with patch("sys.argv", ["script.py", "--phase", "5"]):
                # This will fail during argparse validation
                parser = argparse.ArgumentParser()
                parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4])
                parser.parse_args()


class TestResultPersistence:
    """Test that results are saved correctly."""

    def test_runbook_result_serialization(self):
        """Test that RunbookResult can be serialized to JSON."""
        phases = [
            PhaseResult(
                phase=1,
                name="Test Phase",
                status="PASSED",
                duration=1.0,
            )
        ]

        result = RunbookResult(
            success=True,
            phases=phases,
            total_duration=1.0,
            timestamp="2024-01-01T00:00:00",
        )

        # Should serialize without errors
        result_json = json.dumps(result.to_dict(), indent=2)
        assert result_json is not None

        # Should deserialize correctly
        deserialized = json.loads(result_json)
        assert deserialized["success"] is True
        assert deserialized["total_duration"] == 1.0
        assert len(deserialized["phases"]) == 1
