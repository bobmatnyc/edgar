"""Regression tests for SCT extraction across multiple companies.

These tests ensure that all three major proxy formats continue to work:
- Apple: Standard format with "Summary Compensation Table" header
- Amazon: Non-standard format with empty first column
- Berkshire: Simplified format with fewer columns

Running these tests prevents regressions when updating the extractor.
"""

import pytest

from edgar.extractors.sct import SCTExtractor
from edgar.services.sec_edgar_client import SecEdgarClient


@pytest.mark.asyncio
class TestSCTExtractionRegression:
    """Regression tests for SCT extraction across different proxy formats."""

    @pytest.fixture
    async def sec_client(self):
        """Provide SEC EDGAR client for fetching filings."""
        return SecEdgarClient()

    async def test_apple_extraction(self, sec_client):
        """Test Apple SCT extraction (standard format).

        Apple uses standard "Summary Compensation Table" header format.
        Should extract 5+ executives with complete compensation data.
        """
        # Fetch latest DEF 14A filing
        filing = await sec_client.get_latest_filing("0000320193", "DEF 14A")
        html = await sec_client.fetch_filing_html(filing["url"])

        # Extract SCT data
        extractor = SCTExtractor(company="Apple", cik="0000320193")
        result = extractor.extract({"html": html})

        # Assertions
        assert len(result.executives) >= 5, "Apple should have at least 5 executives"

        # Check for known executives (CEO should always be present)
        exec_names = [e.name for e in result.executives]
        assert any(
            "Cook" in name for name in exec_names
        ), "Tim Cook should be in executives"

        # Verify compensation data exists
        execs_with_comp = [e for e in result.executives if e.compensation]
        assert (
            len(execs_with_comp) >= 5
        ), "At least 5 executives should have compensation data"

        # Verify no header rows as executives
        bad_names = ["Name and Principal Position", "Salary", "Year"]
        for exec_data in result.executives:
            assert (
                exec_data.name not in bad_names
            ), f"Header row '{exec_data.name}' should not be extracted as executive"

    async def test_amazon_extraction(self, sec_client):
        """Test Amazon SCT extraction (non-standard format with empty first column).

        Amazon has empty first column, requiring column offset detection.
        Should extract 5+ executives.
        """
        # Fetch latest DEF 14A filing
        filing = await sec_client.get_latest_filing("0001018724", "DEF 14A")
        html = await sec_client.fetch_filing_html(filing["url"])

        # Extract SCT data
        extractor = SCTExtractor(company="Amazon", cik="0001018724")
        result = extractor.extract({"html": html})

        # Assertions
        assert len(result.executives) >= 5, "Amazon should have at least 5 executives"

        # Check for known executives (CEO and founder)
        exec_names = [e.name for e in result.executives]
        assert any(
            "Jassy" in name for name in exec_names
        ), "Andrew Jassy (CEO) should be in executives"
        assert any(
            "Bezos" in name for name in exec_names
        ), "Jeff Bezos (Founder) should be in executives"

        # Verify no header rows as executives
        bad_names = ["Name and Principal Position", "Salary", "Year"]
        for exec_data in result.executives:
            assert (
                exec_data.name not in bad_names
            ), f"Header row '{exec_data.name}' should not be extracted as executive"

        # Most executives should have compensation (some may not due to mid-year changes)
        execs_with_comp = [e for e in result.executives if e.compensation]
        assert (
            len(execs_with_comp) >= 4
        ), "At least 4 executives should have compensation data"

    async def test_berkshire_extraction(self, sec_client):
        """Test Berkshire Hathaway SCT extraction (simplified format).

        Berkshire uses simplified table with fewer columns (Salary, Bonus, Other, Total).
        Should extract 5+ executives including Warren Buffett.
        """
        # Fetch latest DEF 14A filing
        filing = await sec_client.get_latest_filing("0001067983", "DEF 14A")
        html = await sec_client.fetch_filing_html(filing["url"])

        # Extract SCT data
        extractor = SCTExtractor(company="Berkshire", cik="0001067983")
        result = extractor.extract({"html": html})

        # Assertions
        assert (
            len(result.executives) >= 5
        ), "Berkshire should have at least 5 executives"

        # Check for Warren Buffett (CEO)
        exec_names = [e.name for e in result.executives]
        assert any(
            "Buffett" in name for name in exec_names
        ), "Warren Buffett should be in executives"

        # Verify no header rows as executives
        bad_names = ["Name and Principal Position", "Salary", "Year"]
        for exec_data in result.executives:
            assert (
                exec_data.name not in bad_names
            ), f"Header row '{exec_data.name}' should not be extracted as executive"

        # Verify compensation data exists
        execs_with_comp = [e for e in result.executives if e.compensation]
        assert (
            len(execs_with_comp) >= 5
        ), "At least 5 executives should have compensation data"

    async def test_all_companies_no_header_rows(self, sec_client):
        """Ensure no header rows are extracted as executives across all companies."""
        companies = [
            ("0000320193", "Apple"),
            ("0001018724", "Amazon"),
            ("0001067983", "Berkshire"),
        ]

        bad_names = [
            "Name and Principal Position",
            "Name",
            "Salary",
            "Year",
            "Total",
            "Compensation",
        ]

        for cik, name in companies:
            filing = await sec_client.get_latest_filing(cik, "DEF 14A")
            html = await sec_client.fetch_filing_html(filing["url"])

            extractor = SCTExtractor(company=name, cik=cik)
            result = extractor.extract({"html": html})

            for exec_data in result.executives:
                assert (
                    exec_data.name not in bad_names
                ), f"{name}: Header row '{exec_data.name}' should not be extracted as executive"

    async def test_all_companies_minimum_executives(self, sec_client):
        """Ensure all companies extract at least 5 valid executives."""
        companies = [
            ("0000320193", "Apple"),
            ("0001018724", "Amazon"),
            ("0001067983", "Berkshire"),
        ]

        for cik, name in companies:
            filing = await sec_client.get_latest_filing(cik, "DEF 14A")
            html = await sec_client.fetch_filing_html(filing["url"])

            extractor = SCTExtractor(company=name, cik=cik)
            result = extractor.extract({"html": html})

            assert (
                len(result.executives) >= 5
            ), f"{name} should have at least 5 executives, got {len(result.executives)}"
