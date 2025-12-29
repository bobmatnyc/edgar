"""Tests for SCT Extractor."""

import pytest

from edgar.extractors.sct import ExecutiveCompensation, SCTData, SCTExtractor


class TestSCTExtractor:
    """Test suite for SCTExtractor."""

    @pytest.fixture
    def extractor(self) -> SCTExtractor:
        return SCTExtractor(company="Apple Inc.", cik="0000320193")

    @pytest.fixture
    def sample_html(self) -> str:
        return """
        <html>
        <body>
        <h2>Summary Compensation Table</h2>
        <table>
            <tr>
                <th>Name and Principal Position</th>
                <th>Year</th>
                <th>Salary</th>
                <th>Bonus</th>
                <th>Stock Awards</th>
                <th>Option Awards</th>
                <th>Non-Equity Incentive</th>
                <th>Pension Change</th>
                <th>Other</th>
                <th>Total</th>
            </tr>
            <tr>
                <td>Timothy D. Cook<br/>Chief Executive Officer</td>
                <td>2024</td>
                <td>$3,000,000</td>
                <td>—</td>
                <td>$58,128,634</td>
                <td>—</td>
                <td>$12,000,000</td>
                <td>—</td>
                <td>$1,523,232</td>
                <td>$74,651,866</td>
            </tr>
            <tr>
                <td>Luca Maestri<br/>CFO</td>
                <td>2024</td>
                <td>$1,000,000</td>
                <td>—</td>
                <td>$21,938,298</td>
                <td>—</td>
                <td>$4,000,000</td>
                <td>—</td>
                <td>$261,702</td>
                <td>$27,200,000</td>
            </tr>
        </table>
        </body>
        </html>
        """

    def test_extract_basic(self, extractor: SCTExtractor, sample_html: str) -> None:
        """Test basic extraction from sample HTML."""
        result = extractor.extract({"html": sample_html})

        assert isinstance(result, SCTData)
        assert result.company == "Apple Inc."
        assert len(result.executives) >= 1

    def test_extract_ceo_data(self, extractor: SCTExtractor, sample_html: str) -> None:
        """Test CEO compensation extraction."""
        result = extractor.extract({"html": sample_html})

        ceo = next((e for e in result.executives if "Cook" in e.name), None)
        assert ceo is not None
        assert ceo.name == "Timothy D. Cook"
        assert len(ceo.compensation) >= 1

        comp = ceo.compensation[0]
        assert comp.year == 2024
        assert comp.salary == 3000000
        assert comp.total == 74651866

    def test_extract_multiple_executives(self, extractor: SCTExtractor, sample_html: str) -> None:
        """Test extraction of multiple executives."""
        result = extractor.extract({"html": sample_html})
        assert len(result.executives) == 2

    def test_currency_conversion(self, extractor: SCTExtractor) -> None:
        """Test currency string to number conversion."""
        assert extractor._to_number("$3,000,000") == 3000000
        assert extractor._to_number("—") == 0.0
        assert extractor._to_number("$58,128,634") == 58128634
        assert extractor._to_number("") == 0.0

    def test_missing_html_raises(self, extractor: SCTExtractor) -> None:
        """Test error when HTML is missing."""
        with pytest.raises(ValueError, match="No HTML content"):
            extractor.extract({})

    def test_no_table_raises(self, extractor: SCTExtractor) -> None:
        """Test error when SCT table not found."""
        with pytest.raises(ValueError, match="Summary Compensation Table not found"):
            extractor.extract({"html": "<html><body>No table here</body></html>"})

    def test_total_compensation_property(self, extractor: SCTExtractor, sample_html: str) -> None:
        """Test total compensation calculation."""
        result = extractor.extract({"html": sample_html})
        total = result.total_compensation
        # Should be sum of all executives' latest year total
        assert total > 0


class TestExecutiveCompensation:
    """Test suite for ExecutiveCompensation model."""

    def test_create_executive(self) -> None:
        """Test creating executive compensation model."""
        exec_comp = ExecutiveCompensation(
            name="John Doe",
            title="CEO",
            compensation=[],
        )
        assert exec_comp.name == "John Doe"
        assert exec_comp.title == "CEO"
        assert len(exec_comp.compensation) == 0


class TestSCTData:
    """Test suite for SCTData model."""

    def test_create_sct_data(self) -> None:
        """Test creating SCT data model."""
        sct_data = SCTData(
            company="Test Corp",
            cik="0000123456",
            filing_date="2024-01-15",
            executives=[],
        )
        assert sct_data.company == "Test Corp"
        assert sct_data.cik == "0000123456"
        assert sct_data.filing_date == "2024-01-15"

    def test_total_compensation_empty(self) -> None:
        """Test total compensation with no executives."""
        sct_data = SCTData(executives=[])
        assert sct_data.total_compensation == 0.0
