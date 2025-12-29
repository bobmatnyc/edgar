"""End-to-end integration tests for SCT Extractor."""

import json
from pathlib import Path

import pytest

from edgar.extractors.sct import SCTExtractor


class TestSCTE2E:
    """End-to-end tests using real Apple DEF 14A filing."""

    @pytest.fixture
    def apple_html(self) -> str:
        """Load real Apple DEF 14A HTML."""
        html_file = Path("data/e2e_test/apple_def14a_raw.html")
        return html_file.read_text()

    @pytest.fixture
    def ground_truth(self) -> dict:
        """Load ground truth data."""
        gt_file = Path("data/e2e_test/apple_sct_ground_truth.json")
        with open(gt_file) as f:
            return json.load(f)

    @pytest.fixture
    def extractor(self) -> SCTExtractor:
        return SCTExtractor(company="Apple Inc.", cik="0000320193")

    def test_extract_all_executives(
        self, extractor: SCTExtractor, apple_html: str, ground_truth: dict
    ) -> None:
        """Test that all executives are extracted."""
        result = extractor.extract({"html": apple_html})
        assert len(result.executives) == ground_truth["expected_executives"]

    def test_extract_ceo_compensation(
        self, extractor: SCTExtractor, apple_html: str, ground_truth: dict
    ) -> None:
        """Test CEO compensation extraction accuracy."""
        result = extractor.extract({"html": apple_html})

        # Find CEO
        ceo = next((e for e in result.executives if "Cook" in e.name), None)
        assert ceo is not None

        # Validate against ground truth
        gt_ceo = next((e for e in ground_truth["executives"] if "Cook" in e["name"]), None)
        assert gt_ceo is not None

        # Check 2024 compensation (most recent)
        ceo_2024 = next((c for c in ceo.compensation if c.year == 2024), None)
        gt_2024 = gt_ceo["compensation"][0]

        assert ceo_2024 is not None
        assert ceo_2024.year == gt_2024["year"]
        assert ceo_2024.salary == gt_2024["salary"]
        assert ceo_2024.bonus == gt_2024["bonus"]
        # Stock awards and total may have small rounding differences
        assert abs(ceo_2024.stock_awards - gt_2024["stock_awards"]) < 100000
        assert abs(ceo_2024.total - gt_2024["total"]) < 100000

    def test_extract_multiple_years(self, extractor: SCTExtractor, apple_html: str) -> None:
        """Test that multiple years are extracted for each executive."""
        result = extractor.extract({"html": apple_html})

        # All executives should have multiple years
        for exec in result.executives:
            assert len(exec.compensation) >= 2, f"{exec.name} should have multiple years"
            # Years should be in descending order (most recent first)
            years = [c.year for c in exec.compensation]
            assert years == sorted(years, reverse=True), f"{exec.name} years not in order"

    def test_validation_rules(
        self, extractor: SCTExtractor, apple_html: str, ground_truth: dict
    ) -> None:
        """Test against validation rules from ground truth."""
        result = extractor.extract({"html": apple_html})

        rules = ground_truth["validation_rules"]

        # Min executives
        assert len(result.executives) >= rules["min_executives"]

        # Required fields
        for exec in result.executives:
            assert exec.name
            assert exec.compensation

        # CEO validation
        ceo = next((e for e in result.executives if "Cook" in e.name), None)
        assert ceo is not None
        assert len(ceo.compensation) > 0
        assert ceo.compensation[0].total >= rules["ceo_total_min"]

    def test_total_compensation_property(self, extractor: SCTExtractor, apple_html: str) -> None:
        """Test total compensation calculation."""
        result = extractor.extract({"html": apple_html})

        # Should sum latest year for all executives
        expected_total = sum(e.compensation[0].total for e in result.executives if e.compensation)
        assert result.total_compensation == expected_total
        assert result.total_compensation > 0
