"""Tests for extractor refinement module."""

import pytest
from bs4 import BeautifulSoup

from edgar.data.fortune100 import Company
from edgar.refinement import ExtractionFailure, ExtractorRefiner, RefinementSuggestion
from edgar.services.sec_edgar_client import SecEdgarClient


@pytest.fixture
def sec_client():
    """Create SEC client for testing."""
    return SecEdgarClient()


@pytest.fixture
def refiner(sec_client):
    """Create extractor refiner for testing."""
    return ExtractorRefiner(sec_client=sec_client, min_confidence=0.7)


@pytest.fixture
def sample_company():
    """Create sample company for testing."""
    return Company(
        rank=1,
        name="Test Corp",
        ticker="TEST",
        cik="0000000001",
        sector="Technology",
    )


def test_extraction_failure_creation(sample_company):
    """Test creating an extraction failure record."""
    failure = ExtractionFailure(
        company=sample_company,
        form_type="DEF 14A",
        html_sample="<html><body>Test</body></html>",
        error_message="Table not found",
        extractor_type="SCTExtractor",
        filing_url="https://www.sec.gov/test",
    )

    assert failure.company.name == "Test Corp"
    assert failure.form_type == "DEF 14A"
    assert failure.extractor_type == "SCTExtractor"
    assert "Test" in failure.html_sample


def test_refinement_suggestion_creation():
    """Test creating a refinement suggestion."""
    suggestion = RefinementSuggestion(
        pattern_type="table_header",
        current_pattern="summary compensation table",
        suggested_pattern="executive compensation",
        confidence=0.85,
        example_html="<table>...</table>",
        reasoning="Alternative header pattern found",
        company_name="Test Corp",
    )

    assert suggestion.pattern_type == "table_header"
    assert suggestion.confidence == 0.85
    assert suggestion.company_name == "Test Corp"


def test_refinement_suggestion_to_dict():
    """Test converting suggestion to dictionary."""
    suggestion = RefinementSuggestion(
        pattern_type="table_header",
        current_pattern="summary compensation table",
        suggested_pattern="executive compensation",
        confidence=0.85,
        example_html="<table>...</table>",
        reasoning="Alternative header pattern found",
        company_name="Test Corp",
    )

    data = suggestion.to_dict()
    assert data["pattern_type"] == "table_header"
    assert data["confidence"] == 0.85
    assert data["company_name"] == "Test Corp"
    assert "example_html_length" in data


def test_extract_table_headers(refiner):
    """Test extracting headers from HTML table."""
    html = """
    <table>
        <tr>
            <th>Name</th>
            <th>Year</th>
            <th>Salary</th>
            <th>Total</th>
        </tr>
        <tr>
            <td>John Doe</td>
            <td>2024</td>
            <td>$500,000</td>
            <td>$1,000,000</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    headers = refiner._extract_table_headers(table)

    assert len(headers) == 4
    assert "Name" in headers
    assert "Year" in headers
    assert "Salary" in headers
    assert "Total" in headers


def test_analyze_table_structure(refiner):
    """Test analyzing table structure."""
    html = """
    <table>
        <tr>
            <th>Name</th>
            <th>Year</th>
            <th>Salary</th>
        </tr>
        <tr>
            <td>John Doe</td>
            <td>2024</td>
            <td>$500,000</td>
        </tr>
        <tr>
            <td rowspan="2">Jane Smith</td>
            <td>2024</td>
            <td>$600,000</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    structure = refiner._analyze_table_structure(table)

    assert "3 rows" in structure
    assert "3 columns" in structure
    assert "rowspan" in structure


def test_find_year_columns(refiner):
    """Test finding year columns in table."""
    html = """
    <table>
        <tr>
            <th>Description</th>
            <th>2024</th>
            <th>2023</th>
            <th>2022</th>
        </tr>
        <tr>
            <td>Revenue</td>
            <td>$1,000</td>
            <td>$900</td>
            <td>$800</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    year_pattern = refiner._find_year_columns(table)

    assert "Years in columns" in year_pattern
    assert "1" in year_pattern  # Column indices


def test_find_section_headers(refiner):
    """Test finding section headers in tax table."""
    html = """
    <table>
        <tr>
            <td colspan="4">Current:</td>
        </tr>
        <tr>
            <td>Federal</td>
            <td>$100</td>
            <td>$90</td>
            <td>$80</td>
        </tr>
        <tr>
            <td colspan="4">Deferred:</td>
        </tr>
        <tr>
            <td>Federal</td>
            <td>$20</td>
            <td>$15</td>
            <td>$10</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    headers = refiner._find_section_headers(table)

    assert len(headers) > 0
    assert any("current" in h.lower() for h in headers)
    assert any("deferred" in h.lower() for h in headers)


def test_clean_text(refiner):
    """Test text cleaning functionality."""
    # Test footnote removal
    assert refiner._clean_text("Revenue (1)") == "Revenue"
    assert refiner._clean_text("Total [2]") == "Total"
    assert refiner._clean_text("Salary***") == "Salary"

    # Test whitespace normalization
    assert refiner._clean_text("Multiple   spaces") == "Multiple spaces"
    assert refiner._clean_text("  Leading  trailing  ") == "Leading trailing"


def test_generate_refinement_report(refiner):
    """Test generating refinement report."""
    suggestions = [
        RefinementSuggestion(
            pattern_type="table_header",
            current_pattern="summary compensation table",
            suggested_pattern="executive compensation",
            confidence=0.85,
            example_html="<table>...</table>",
            reasoning="Alternative header found",
            company_name="Company A",
        ),
        RefinementSuggestion(
            pattern_type="table_header",
            current_pattern="summary compensation table",
            suggested_pattern="named executive officers",
            confidence=0.80,
            example_html="<table>...</table>",
            reasoning="Another header pattern",
            company_name="Company B",
        ),
        RefinementSuggestion(
            pattern_type="tax_section_headers",
            current_pattern="Current:",
            suggested_pattern="Current Tax Expense",
            confidence=0.75,
            example_html="<table>...</table>",
            reasoning="Different section header format",
            company_name="Company C",
        ),
    ]

    report = refiner.generate_refinement_report(suggestions)

    assert "EXTRACTOR REFINEMENT REPORT" in report
    assert "Total Suggestions: 3" in report
    assert "Table Header" in report
    assert "Tax Section Headers" in report
    assert "Company A" in report
    assert "Company C" in report


@pytest.mark.asyncio
async def test_analyze_failures_empty_list(refiner):
    """Test analyzing empty failure list."""
    suggestions = await refiner.analyze_failures([])
    assert suggestions == []


@pytest.mark.asyncio
async def test_analyze_sct_failure(refiner, sample_company):
    """Test analyzing SCT extraction failure."""
    # Create HTML with compensation table but non-standard header
    html = """
    <html>
    <body>
        <h2>Named Executive Officers Compensation</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Year</th>
                <th>Salary</th>
                <th>Bonus</th>
                <th>Stock Awards</th>
                <th>Total Compensation</th>
            </tr>
            <tr>
                <td>John Doe</td>
                <td>2024</td>
                <td>$500,000</td>
                <td>$100,000</td>
                <td>$200,000</td>
                <td>$800,000</td>
            </tr>
        </table>
    </body>
    </html>
    """

    failure = ExtractionFailure(
        company=sample_company,
        form_type="DEF 14A",
        html_sample=html,
        error_message="Summary Compensation Table not found",
        extractor_type="SCTExtractor",
    )

    suggestions = await refiner.analyze_failures([failure])

    # Should suggest the alternative header pattern
    assert len(suggestions) > 0
    assert any(s.pattern_type == "table_header" for s in suggestions)


@pytest.mark.asyncio
async def test_analyze_tax_failure(refiner, sample_company):
    """Test analyzing tax extraction failure."""
    # Create HTML with tax table
    html = """
    <html>
    <body>
        <h3>Income Tax Expense</h3>
        <table>
            <tr>
                <td></td>
                <th>2024</th>
                <th>2023</th>
                <th>2022</th>
            </tr>
            <tr>
                <td colspan="4">Current Tax:</td>
            </tr>
            <tr>
                <td>Federal</td>
                <td>$1,000</td>
                <td>$900</td>
                <td>$800</td>
            </tr>
            <tr>
                <td>State and Local</td>
                <td>$200</td>
                <td>$180</td>
                <td>$150</td>
            </tr>
            <tr>
                <td>Foreign</td>
                <td>$300</td>
                <td>$250</td>
                <td>$200</td>
            </tr>
            <tr>
                <td colspan="4">Deferred Tax:</td>
            </tr>
            <tr>
                <td>Federal</td>
                <td>$100</td>
                <td>$80</td>
                <td>$70</td>
            </tr>
        </table>
    </body>
    </html>
    """

    failure = ExtractionFailure(
        company=sample_company,
        form_type="10-K",
        html_sample=html,
        error_message="Tax expense is $0",
        extractor_type="TaxExtractor",
    )

    suggestions = await refiner.analyze_failures([failure])

    # Should suggest tax table structure improvements
    assert len(suggestions) > 0
    assert any("tax" in s.pattern_type.lower() for s in suggestions)
