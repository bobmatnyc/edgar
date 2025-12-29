"""Unit tests for FiscalYearMapper service.

Tests fiscal year mapping logic for calendar and non-calendar companies,
validating the fix for the XBRL fiscal year alignment bug.
"""

from datetime import datetime

import pytest

from edgar_analyzer.services.fiscal_year_mapper import FiscalYearMapper


class TestFiscalYearMapper:
    """Test suite for FiscalYearMapper service."""

    def test_initialization(self):
        """Test FiscalYearMapper initializes with FYE database."""
        mapper = FiscalYearMapper()

        # Verify key companies are tracked
        assert mapper.get_fye_month("0000104169") == 1  # Walmart - Jan 31
        assert mapper.get_fye_month("0000320193") == 9  # Apple - Sep 30
        assert mapper.get_fye_month("0000789019") == 6  # Microsoft - Jun 30
        assert mapper.get_fye_month("0000909832") == 9  # Costco - Sep 01

    def test_walmart_fiscal_year_mapping(self):
        """Test Walmart (Jan 31 FYE) fiscal year mapping.

        Walmart FY2024: Feb 1, 2023 → Jan 31, 2024
        Period end: 2024-01-31 → Should map to FY2024
        """
        mapper = FiscalYearMapper()

        # Walmart FY2024 ends Jan 31, 2024
        fy = mapper.get_fiscal_year("0000104169", "2024-01-31")
        assert fy == 2024, "Walmart FY2024 should map to 2024"

        # Walmart FY2023 ends Jan 31, 2023
        fy = mapper.get_fiscal_year("0000104169", "2023-01-31")
        assert fy == 2023, "Walmart FY2023 should map to 2023"

        # Walmart FY2022 ends Jan 31, 2022
        fy = mapper.get_fiscal_year("0000104169", "2022-01-31")
        assert fy == 2022, "Walmart FY2022 should map to 2022"

    def test_apple_fiscal_year_mapping(self):
        """Test Apple (Sep 30 FYE) fiscal year mapping.

        Apple FY2023: Oct 1, 2022 → Sep 30, 2023
        Period end: 2023-09-30 → Should map to FY2023
        """
        mapper = FiscalYearMapper()

        # Apple FY2023 ends Sep 30, 2023
        fy = mapper.get_fiscal_year("0000320193", "2023-09-30")
        assert fy == 2023, "Apple FY2023 should map to 2023"

        # Apple FY2022 ends Sep 24, 2022 (last Saturday in Sep)
        fy = mapper.get_fiscal_year("0000320193", "2022-09-24")
        assert fy == 2022, "Apple FY2022 should map to 2022"

        # Apple FY2021 ends Sep 25, 2021
        fy = mapper.get_fiscal_year("0000320193", "2021-09-25")
        assert fy == 2021, "Apple FY2021 should map to 2021"

    def test_microsoft_fiscal_year_mapping(self):
        """Test Microsoft (Jun 30 FYE) fiscal year mapping.

        Microsoft FY2023: Jul 1, 2022 → Jun 30, 2023
        Period end: 2023-06-30 → Should map to FY2023
        """
        mapper = FiscalYearMapper()

        # Microsoft FY2023 ends Jun 30, 2023
        fy = mapper.get_fiscal_year("0000789019", "2023-06-30")
        assert fy == 2023, "Microsoft FY2023 should map to 2023"

        # Microsoft FY2022 ends Jun 30, 2022
        fy = mapper.get_fiscal_year("0000789019", "2022-06-30")
        assert fy == 2022, "Microsoft FY2022 should map to 2022"

        # Microsoft FY2021 ends Jun 30, 2021
        fy = mapper.get_fiscal_year("0000789019", "2021-06-30")
        assert fy == 2021, "Microsoft FY2021 should map to 2021"

    def test_amazon_calendar_year_company(self):
        """Test Amazon (Dec 31 FYE) calendar year mapping.

        Amazon FY2023: Jan 1, 2023 → Dec 31, 2023
        Period end: 2023-12-31 → Should map to FY2023
        """
        mapper = FiscalYearMapper()

        # Amazon CIK (calendar year company, not in FYE database)
        amazon_cik = "0001018724"

        # Amazon FY2023 ends Dec 31, 2023
        fy = mapper.get_fiscal_year(amazon_cik, "2023-12-31")
        assert fy == 2023, "Amazon FY2023 should map to 2023"

        # Amazon FY2022 ends Dec 31, 2022
        fy = mapper.get_fiscal_year(amazon_cik, "2022-12-31")
        assert fy == 2022, "Amazon FY2022 should map to 2022"

        # Amazon FY2021 ends Dec 31, 2021
        fy = mapper.get_fiscal_year(amazon_cik, "2021-12-31")
        assert fy == 2021, "Amazon FY2021 should map to 2021"

    def test_costco_fiscal_year_mapping(self):
        """Test Costco (Sep 01 FYE) fiscal year mapping.

        Costco FY2023: Sep 2, 2022 → Sep 1, 2023
        Period end: 2023-09-03 → Should map to FY2023
        """
        mapper = FiscalYearMapper()

        # Costco FY2023 ends Sep 3, 2023 (Sunday before Labor Day)
        fy = mapper.get_fiscal_year("0000909832", "2023-09-03")
        assert fy == 2023, "Costco FY2023 should map to 2023"

        # Costco FY2022 ends Aug 28, 2022
        fy = mapper.get_fiscal_year("0000909832", "2022-08-28")
        assert fy == 2022, "Costco FY2022 should map to 2022"

    def test_unknown_company_defaults_to_calendar_year(self):
        """Test unknown company defaults to Dec 31 FYE (calendar year)."""
        mapper = FiscalYearMapper()

        unknown_cik = "0000999999"

        # Should default to calendar year convention
        fye_month = mapper.get_fye_month(unknown_cik)
        assert fye_month == 12, "Unknown company should default to Dec 31 FYE"

        # Should map to calendar year
        fy = mapper.get_fiscal_year(unknown_cik, "2023-12-31")
        assert fy == 2023

    def test_invalid_date_format_raises_error(self):
        """Test invalid period end date format raises ValueError."""
        mapper = FiscalYearMapper()

        with pytest.raises(ValueError, match="Invalid period end date"):
            mapper.get_fiscal_year("0000104169", "invalid-date")

        with pytest.raises(ValueError, match="Invalid period end date"):
            mapper.get_fiscal_year("0000104169", "2024/01/31")  # Wrong format

        with pytest.raises(ValueError, match="Invalid period end date"):
            mapper.get_fiscal_year("0000104169", "2024-13-01")  # Invalid month

    def test_is_calendar_year_company(self):
        """Test calendar year company detection."""
        mapper = FiscalYearMapper()

        # Calendar year companies (Dec 31 FYE)
        assert mapper.is_calendar_year_company("0001018724")  # Amazon
        assert mapper.is_calendar_year_company("0000999999")  # Unknown (default)

        # Non-calendar year companies
        assert not mapper.is_calendar_year_company("0000104169")  # Walmart (Jan)
        assert not mapper.is_calendar_year_company("0000320193")  # Apple (Sep)
        assert not mapper.is_calendar_year_company("0000789019")  # Microsoft (Jun)

    def test_add_company_fye(self):
        """Test adding new company to FYE database."""
        mapper = FiscalYearMapper()

        new_cik = "0000012345"

        # Initially defaults to Dec 31
        assert mapper.get_fye_month(new_cik) == 12

        # Add company with Mar 31 FYE
        mapper.add_company_fye(new_cik, 3)
        assert mapper.get_fye_month(new_cik) == 3

        # Verify fiscal year mapping uses new FYE
        fy = mapper.get_fiscal_year(new_cik, "2023-03-31")
        assert fy == 2023

    def test_add_company_fye_invalid_month(self):
        """Test adding company with invalid FYE month raises error."""
        mapper = FiscalYearMapper()

        with pytest.raises(ValueError, match="Invalid FYE month"):
            mapper.add_company_fye("0000012345", 0)

        with pytest.raises(ValueError, match="Invalid FYE month"):
            mapper.add_company_fye("0000012345", 13)

        with pytest.raises(ValueError, match="Invalid FYE month"):
            mapper.add_company_fye("0000012345", -1)

    def test_validate_fiscal_year_alignment_valid(self):
        """Test fiscal year alignment validation for valid data."""
        mapper = FiscalYearMapper()

        # Walmart FY2024 ends Jan 31, 2024 - valid
        valid, error = mapper.validate_fiscal_year_alignment(
            "0000104169", 2024, "2024-01-31"
        )
        assert valid is True
        assert error is None

        # Apple FY2023 ends Sep 30, 2023 - valid
        valid, error = mapper.validate_fiscal_year_alignment(
            "0000320193", 2023, "2023-09-30"
        )
        assert valid is True
        assert error is None

    def test_validate_fiscal_year_alignment_mismatch(self):
        """Test fiscal year alignment validation detects mismatches."""
        mapper = FiscalYearMapper()

        # Requesting FY2023 but period end is in 2024 (FY2024)
        valid, error = mapper.validate_fiscal_year_alignment(
            "0000104169", 2023, "2024-01-31"
        )
        assert valid is False
        assert "mismatch" in error.lower()
        assert "FY2023" in error
        assert "FY2024" in error

        # Requesting FY2024 but period end is in 2023 (FY2023)
        valid, error = mapper.validate_fiscal_year_alignment(
            "0000320193", 2024, "2023-09-30"
        )
        assert valid is False
        assert "mismatch" in error.lower()

    def test_validate_fiscal_year_alignment_invalid_date(self):
        """Test fiscal year alignment validation handles invalid dates."""
        mapper = FiscalYearMapper()

        valid, error = mapper.validate_fiscal_year_alignment(
            "0000104169", 2024, "invalid-date"
        )
        assert valid is False
        assert "Invalid period end date" in error

    def test_get_expected_period_end_range(self):
        """Test expected period end date range calculation."""
        mapper = FiscalYearMapper()

        # Walmart (Jan 31 FYE) - FY2024
        earliest, latest = mapper.get_expected_period_end_range("0000104169", 2024)
        assert earliest == "2024-01-01"
        assert latest == "2024-02-15"

        # Apple (Sep 30 FYE) - FY2023
        earliest, latest = mapper.get_expected_period_end_range("0000320193", 2023)
        assert earliest == "2023-09-01"
        assert latest == "2023-10-15"

        # Microsoft (Jun 30 FYE) - FY2023
        earliest, latest = mapper.get_expected_period_end_range("0000789019", 2023)
        assert earliest == "2023-06-01"
        assert latest == "2023-07-15"

        # Calendar year company (Dec 31 FYE) - FY2023
        earliest, latest = mapper.get_expected_period_end_range("0001018724", 2023)
        assert earliest == "2023-12-01"
        assert latest == "2023-12-31"

    def test_fiscal_year_consistency_across_years(self):
        """Test fiscal year mapping is consistent across multiple years."""
        mapper = FiscalYearMapper()

        # Test Walmart for 5 consecutive years
        walmart_cik = "0000104169"
        for year in [2020, 2021, 2022, 2023, 2024]:
            period_end = f"{year}-01-31"
            fy = mapper.get_fiscal_year(walmart_cik, period_end)
            assert fy == year, f"Walmart period end {period_end} should map to FY{year}"

        # Test Apple for 5 consecutive years
        apple_cik = "0000320193"
        for year in [2020, 2021, 2022, 2023, 2024]:
            period_end = f"{year}-09-30"
            fy = mapper.get_fiscal_year(apple_cik, period_end)
            assert fy == year, f"Apple period end {period_end} should map to FY{year}"

    def test_all_fortune_100_non_calendar_companies(self):
        """Test all tracked Fortune 100 non-calendar companies."""
        mapper = FiscalYearMapper()

        # Companies with Jan 31 FYE
        jan_companies = [
            ("0000104169", "Walmart"),
            ("0000027419", "Target"),
            ("0000354950", "Home Depot"),
        ]
        for cik, name in jan_companies:
            fy = mapper.get_fiscal_year(cik, "2023-01-31")
            assert fy == 2023, f"{name} FY2023 should map to 2023"

        # Companies with Sep FYE
        sep_companies = [
            ("0000320193", "Apple"),
            ("0000909832", "Costco"),
        ]
        for cik, name in sep_companies:
            fy = mapper.get_fiscal_year(cik, "2023-09-30")
            assert fy == 2023, f"{name} FY2023 should map to 2023"

        # Companies with Jun FYE
        jun_companies = [("0000789019", "Microsoft")]
        for cik, name in jun_companies:
            fy = mapper.get_fiscal_year(cik, "2023-06-30")
            assert fy == 2023, f"{name} FY2023 should map to 2023"

        # Companies with May FYE
        may_companies = [
            ("0001341439", "Oracle"),
            ("0000320187", "Nike"),
        ]
        for cik, name in may_companies:
            fy = mapper.get_fiscal_year(cik, "2023-05-31")
            assert fy == 2023, f"{name} FY2023 should map to 2023"
