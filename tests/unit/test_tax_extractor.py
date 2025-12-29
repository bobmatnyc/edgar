"""Unit tests for TaxExtractor."""

import pytest
from edgar.extractors.tax import TaxData, TaxExtractor, TaxYear


class TestTaxExtractor:
    """Test suite for TaxExtractor."""

    def test_to_number_basic(self):
        """Test basic number conversion."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        assert extractor._to_number("$1,234,567") == 1234567.0
        assert extractor._to_number("1,234") == 1234.0
        assert extractor._to_number("0") == 0.0

    def test_to_number_negative_parentheses(self):
        """Test negative numbers in parentheses."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        assert extractor._to_number("(1,234)") == -1234.0
        assert extractor._to_number("($500)") == -500.0

    def test_to_number_dashes(self):
        """Test dash handling as zero."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        assert extractor._to_number("—") == 0.0
        assert extractor._to_number("–") == 0.0
        assert extractor._to_number("-") == 0.0
        assert extractor._to_number("N/A") == 0.0

    def test_to_number_billions_millions(self):
        """Test billions and millions abbreviations."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        assert extractor._to_number("1.5B") == 1_500_000_000.0
        assert extractor._to_number("2.3M") == 2_300_000.0
        assert extractor._to_number("500M") == 500_000_000.0

    def test_clean_cell(self):
        """Test cell cleaning."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        assert extractor._clean_cell("Federal(1)") == "Federal"
        assert extractor._clean_cell("State [2]") == "State"
        assert extractor._clean_cell("Foreign***") == "Foreign"
        assert extractor._clean_cell("  Multiple   Spaces  ") == "Multiple Spaces"

    def test_extract_no_html(self):
        """Test extract with no HTML raises ValueError."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        with pytest.raises(ValueError, match="No HTML content"):
            extractor.extract({})

    def test_extract_no_table(self):
        """Test extract with no tax table raises ValueError."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        html = "<html><body><p>No tax table here</p></body></html>"
        with pytest.raises(ValueError, match="Income tax expense table not found"):
            extractor.extract({"html": html})

    def test_looks_like_tax_table_true(self):
        """Test tax table detection with valid table."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        from bs4 import BeautifulSoup

        html = """
        <table>
            <tr><th>Current</th><th>Federal</th><th>State</th></tr>
            <tr><td>Deferred</td><td>Foreign</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")

        assert extractor._looks_like_tax_table(table) is True

    def test_looks_like_tax_table_false(self):
        """Test tax table detection with invalid table."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        from bs4 import BeautifulSoup

        html = """
        <table>
            <tr><th>Name</th><th>Salary</th><th>Bonus</th></tr>
            <tr><td>John Doe</td><td>$100,000</td><td>$10,000</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")

        assert extractor._looks_like_tax_table(table) is False

    def test_extract_with_mock_html(self):
        """Test extraction with mock tax table HTML."""
        extractor = TaxExtractor(company="Test Corp", cik="0001234567")

        html = """
        <html>
        <body>
            <h2>Provision for Income Taxes</h2>
            <table>
                <tr>
                    <th></th>
                    <th>2024</th>
                    <th>2023</th>
                    <th>2022</th>
                </tr>
                <tr>
                    <td>Current:</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td>Federal</td>
                    <td>$1,000,000</td>
                    <td>$900,000</td>
                    <td>$800,000</td>
                </tr>
                <tr>
                    <td>State</td>
                    <td>$200,000</td>
                    <td>$180,000</td>
                    <td>$160,000</td>
                </tr>
                <tr>
                    <td>Foreign</td>
                    <td>$300,000</td>
                    <td>$270,000</td>
                    <td>$240,000</td>
                </tr>
                <tr>
                    <td>Deferred:</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td>Federal</td>
                    <td>($100,000)</td>
                    <td>$50,000</td>
                    <td>$75,000</td>
                </tr>
                <tr>
                    <td>State</td>
                    <td>($20,000)</td>
                    <td>$10,000</td>
                    <td>$15,000</td>
                </tr>
                <tr>
                    <td>Foreign</td>
                    <td>$30,000</td>
                    <td>($25,000)</td>
                    <td>$35,000</td>
                </tr>
            </table>
        </body>
        </html>
        """

        result = extractor.extract({"html": html})

        assert isinstance(result, TaxData)
        assert result.company == "Test Corp"
        assert result.cik == "0001234567"
        assert len(result.tax_years) == 3

        # Check 2024 data (most recent)
        tax_2024 = result.tax_years[0]
        assert tax_2024.year == 2024
        assert tax_2024.current_federal == 1_000_000.0
        assert tax_2024.current_state == 200_000.0
        assert tax_2024.current_foreign == 300_000.0
        assert tax_2024.deferred_federal == -100_000.0
        assert tax_2024.deferred_state == -20_000.0
        assert tax_2024.deferred_foreign == 30_000.0

        # Check totals
        assert tax_2024.total_current == 1_500_000.0
        assert tax_2024.total_deferred == -90_000.0
        assert tax_2024.total_tax_expense == 1_410_000.0

    def test_tax_data_properties(self):
        """Test TaxData property methods."""
        tax_data = TaxData(
            company="Test Corp",
            cik="0001234567",
            tax_years=[
                TaxYear(
                    year=2024,
                    total_tax_expense=1_000_000.0,
                    effective_tax_rate=0.21,
                ),
                TaxYear(
                    year=2023,
                    total_tax_expense=900_000.0,
                    effective_tax_rate=0.22,
                ),
            ],
        )

        assert tax_data.latest_tax_expense == 1_000_000.0
        assert tax_data.latest_effective_rate == 0.21

    def test_tax_data_properties_empty(self):
        """Test TaxData properties with no tax years."""
        tax_data = TaxData(company="Test Corp", cik="0001234567")

        assert tax_data.latest_tax_expense == 0.0
        assert tax_data.latest_effective_rate == 0.0


class TestTaxYear:
    """Test suite for TaxYear model."""

    def test_tax_year_creation(self):
        """Test TaxYear model creation."""
        tax_year = TaxYear(
            year=2024,
            current_federal=1_000_000.0,
            current_state=200_000.0,
            current_foreign=300_000.0,
        )

        assert tax_year.year == 2024
        assert tax_year.current_federal == 1_000_000.0
        assert tax_year.current_state == 200_000.0
        assert tax_year.current_foreign == 300_000.0

    def test_tax_year_defaults(self):
        """Test TaxYear model default values."""
        tax_year = TaxYear(year=2024)

        assert tax_year.year == 2024
        assert tax_year.current_federal == 0.0
        assert tax_year.current_state == 0.0
        assert tax_year.current_foreign == 0.0
        assert tax_year.deferred_federal == 0.0
        assert tax_year.deferred_state == 0.0
        assert tax_year.deferred_foreign == 0.0
        assert tax_year.total_current == 0.0
        assert tax_year.total_deferred == 0.0
        assert tax_year.total_tax_expense == 0.0
        assert tax_year.pretax_income == 0.0
        assert tax_year.effective_tax_rate == 0.0
        assert tax_year.cash_taxes_paid == 0.0
