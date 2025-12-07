"""Integration tests for fiscal year mapping fix in data extraction.

Tests that the XBRL extraction correctly uses period end dates instead of
the 'fy' field to determine fiscal years.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from edgar_analyzer.models.company import TaxExpense
from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.fiscal_year_mapper import FiscalYearMapper


@pytest.fixture
def fiscal_year_mapper():
    """Create a FiscalYearMapper instance."""
    return FiscalYearMapper()


@pytest.fixture
def mock_edgar_api():
    """Create a mock EDGAR API service."""
    return AsyncMock()


@pytest.fixture
def mock_company_service():
    """Create a mock company service."""
    return AsyncMock()


@pytest.fixture
def data_extraction_service(mock_edgar_api, mock_company_service, fiscal_year_mapper):
    """Create a DataExtractionService with FiscalYearMapper."""
    return DataExtractionService(
        edgar_api_service=mock_edgar_api,
        company_service=mock_company_service,
        fiscal_year_mapper=fiscal_year_mapper,
    )


class TestFiscalYearFixIntegration:
    """Integration tests for fiscal year mapping in XBRL extraction."""

    @pytest.mark.asyncio
    async def test_walmart_fy2024_extraction(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test Walmart FY2024 extraction uses period end date, not fy field.

        Walmart FY2024: Feb 1, 2023 → Jan 31, 2024
        XBRL data will have:
        - 'fy': 2024 (filing year)
        - 'end': '2024-01-31' (period end)
        - Expected result: FY2024 (from period end)
        """
        # Mock XBRL response with realistic Walmart data
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2024,  # Filing year
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2024-01-31",  # Period end - source of truth
                                        "val": 5123000000,  # ~$5.1B tax expense
                                        "filed": "2024-03-15",
                                        "accn": "0000104169-24-000010",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        # Extract tax expense for Walmart FY2024
        result = await data_extraction_service.extract_tax_expense("0000104169", 2024)

        # Verify extraction succeeded
        assert result is not None, "Walmart FY2024 tax data should be extracted"
        assert isinstance(result, TaxExpense)
        assert result.company_cik == "0000104169"
        assert result.fiscal_year == 2024
        assert result.total_tax_expense == Decimal("5123000000")
        assert result.form_type == "10-K"

    @pytest.mark.asyncio
    async def test_walmart_fy2023_extraction(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test Walmart FY2023 extraction.

        Walmart FY2023: Feb 1, 2022 → Jan 31, 2023
        """
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2023,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2023-01-31",
                                        "val": 4756000000,
                                        "filed": "2023-03-17",
                                        "accn": "0000104169-23-000008",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        result = await data_extraction_service.extract_tax_expense("0000104169", 2023)

        assert result is not None
        assert result.fiscal_year == 2023
        assert result.total_tax_expense == Decimal("4756000000")

    @pytest.mark.asyncio
    async def test_apple_fy2023_extraction(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test Apple FY2023 extraction (Sep 30 FYE).

        Apple FY2023: Oct 1, 2022 → Sep 30, 2023
        """
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2023,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2023-09-30",
                                        "val": 16741000000,
                                        "filed": "2023-11-03",
                                        "accn": "0000320193-23-000077",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        result = await data_extraction_service.extract_tax_expense("0000320193", 2023)

        assert result is not None
        assert result.fiscal_year == 2023
        assert result.total_tax_expense == Decimal("16741000000")

    @pytest.mark.asyncio
    async def test_microsoft_fy2023_extraction(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test Microsoft FY2023 extraction (Jun 30 FYE).

        Microsoft FY2023: Jul 1, 2022 → Jun 30, 2023
        """
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2023,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2023-06-30",
                                        "val": 16950000000,
                                        "filed": "2023-07-27",
                                        "accn": "0000789019-23-000076",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        result = await data_extraction_service.extract_tax_expense("0000789019", 2023)

        assert result is not None
        assert result.fiscal_year == 2023
        assert result.total_tax_expense == Decimal("16950000000")

    @pytest.mark.asyncio
    async def test_rejects_wrong_fiscal_year(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test that extraction correctly rejects data from wrong fiscal year.

        Request: Walmart FY2024
        XBRL data: FY2023 (period end 2023-01-31)
        Expected: None (no match)
        """
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2023,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2023-01-31",  # FY2023, not FY2024
                                        "val": 4756000000,
                                        "filed": "2023-03-17",
                                        "accn": "0000104169-23-000008",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        # Request FY2024, but only FY2023 data available
        result = await data_extraction_service.extract_tax_expense("0000104169", 2024)

        # Should return None (no match)
        assert result is None, "Should not extract data from wrong fiscal year"

    @pytest.mark.asyncio
    async def test_handles_missing_period_end(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test that extraction handles missing period end date gracefully."""
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2024,
                                        "fp": "FY",
                                        "form": "10-K",
                                        # Missing 'end' field
                                        "val": 5123000000,
                                        "filed": "2024-03-15",
                                        "accn": "0000104169-24-000010",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        result = await data_extraction_service.extract_tax_expense("0000104169", 2024)

        # Should skip fact without period end and return None
        assert result is None

    @pytest.mark.asyncio
    async def test_amazon_calendar_year_extraction(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test Amazon (calendar year) extraction works correctly.

        Amazon FY2023: Jan 1, 2023 → Dec 31, 2023
        """
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    {
                                        "fy": 2024,  # Filed in 2024
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2023-12-31",  # FY2023 data
                                        "val": 1243000000,
                                        "filed": "2024-02-02",
                                        "accn": "0001018724-24-000004",
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )

        result = await data_extraction_service.extract_tax_expense("0001018724", 2023)

        assert result is not None
        assert result.fiscal_year == 2023
        assert result.total_tax_expense == Decimal("1243000000")

    @pytest.mark.asyncio
    async def test_multiple_years_in_response(
        self, data_extraction_service, mock_edgar_api
    ):
        """Test extraction finds correct year when multiple years in response."""
        mock_edgar_api.get_company_facts = AsyncMock(
            return_value={
                "facts": {
                    "us-gaap": {
                        "IncomeTaxExpenseBenefit": {
                            "units": {
                                "USD": [
                                    # FY2022
                                    {
                                        "fy": 2022,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2022-01-31",
                                        "val": 4281000000,
                                        "filed": "2022-03-18",
                                        "accn": "0000104169-22-000007",
                                    },
                                    # FY2023
                                    {
                                        "fy": 2023,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2023-01-31",
                                        "val": 4756000000,
                                        "filed": "2023-03-17",
                                        "accn": "0000104169-23-000008",
                                    },
                                    # FY2024
                                    {
                                        "fy": 2024,
                                        "fp": "FY",
                                        "form": "10-K",
                                        "end": "2024-01-31",
                                        "val": 5123000000,
                                        "filed": "2024-03-15",
                                        "accn": "0000104169-24-000010",
                                    },
                                ]
                            }
                        }
                    }
                }
            }
        )

        # Request FY2023 specifically
        result = await data_extraction_service.extract_tax_expense("0000104169", 2023)

        assert result is not None
        assert result.fiscal_year == 2023
        # Should extract the FY2023 amount, not FY2022 or FY2024
        assert result.total_tax_expense == Decimal("4756000000")
        assert (
            "2023-01-31" in result.source_filing
            or result.source_filing == "0000104169-23-000008"
        )
