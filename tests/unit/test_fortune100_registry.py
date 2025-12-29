"""Tests for Fortune 100 Company Registry."""

import json
from pathlib import Path

import pytest

from edgar.data import Company, Fortune100Registry


class TestCompany:
    """Test suite for Company model."""

    def test_create_company(self) -> None:
        """Test creating a valid company."""
        company = Company(
            rank=1,
            name="Test Corp",
            ticker="TEST",
            cik="0000123456",
            sector="Technology",
        )
        assert company.rank == 1
        assert company.name == "Test Corp"
        assert company.ticker == "TEST"
        assert company.cik == "0000123456"
        assert company.sector == "Technology"

    def test_company_immutable(self) -> None:
        """Test that Company is immutable (frozen dataclass)."""
        company = Company(
            rank=1,
            name="Test Corp",
            ticker="TEST",
            cik="0000123456",
            sector="Technology",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            company.rank = 2  # type: ignore

    def test_invalid_rank_low(self) -> None:
        """Test error on rank below 1."""
        with pytest.raises(ValueError, match="Rank must be 1-100"):
            Company(
                rank=0,
                name="Test Corp",
                ticker="TEST",
                cik="0000123456",
                sector="Technology",
            )

    def test_invalid_rank_high(self) -> None:
        """Test error on rank above 100."""
        with pytest.raises(ValueError, match="Rank must be 1-100"):
            Company(
                rank=101,
                name="Test Corp",
                ticker="TEST",
                cik="0000123456",
                sector="Technology",
            )

    def test_invalid_cik_length(self) -> None:
        """Test error on CIK not 10 digits."""
        with pytest.raises(ValueError, match="CIK must be 10 digits"):
            Company(
                rank=1,
                name="Test Corp",
                ticker="TEST",
                cik="123456",  # Only 6 digits
                sector="Technology",
            )

    def test_invalid_cik_non_digit(self) -> None:
        """Test error on CIK with non-digit characters."""
        with pytest.raises(ValueError, match="CIK must contain only digits"):
            Company(
                rank=1,
                name="Test Corp",
                ticker="TEST",
                cik="000012345X",
                sector="Technology",
            )


class TestFortune100Registry:
    """Test suite for Fortune100Registry."""

    @pytest.fixture
    def registry(self) -> Fortune100Registry:
        """Load default Fortune 100 registry."""
        return Fortune100Registry.load_default()

    @pytest.fixture
    def sample_companies(self) -> tuple[Company, ...]:
        """Create sample companies for testing."""
        return tuple(
            Company(
                rank=i,
                name=f"Company {i}",
                ticker=f"C{i:02d}",
                cik=f"{i:010d}",
                sector="Technology" if i <= 50 else "Healthcare",
            )
            for i in range(1, 101)
        )

    @pytest.fixture
    def sample_registry(self, sample_companies: tuple[Company, ...]) -> Fortune100Registry:
        """Create sample registry for testing."""
        return Fortune100Registry(companies=sample_companies)

    def test_load_default_registry(self, registry: Fortune100Registry) -> None:
        """Test loading default Fortune 100 registry."""
        assert len(registry.companies) == 100

    def test_registry_has_100_companies(self, registry: Fortune100Registry) -> None:
        """Test registry contains exactly 100 companies."""
        assert len(registry.companies) == 100

    def test_registry_immutable(self, registry: Fortune100Registry) -> None:
        """Test that registry is immutable."""
        with pytest.raises(Exception):  # FrozenInstanceError
            registry.companies = ()  # type: ignore

    def test_invalid_registry_wrong_count(self, sample_companies: tuple[Company, ...]) -> None:
        """Test error when registry doesn't have 100 companies."""
        with pytest.raises(ValueError, match="Registry must contain exactly 100 companies"):
            Fortune100Registry(companies=sample_companies[:50])

    def test_invalid_registry_duplicate_ranks(self) -> None:
        """Test error when companies have duplicate ranks."""
        companies = tuple(
            Company(
                rank=1,  # All same rank
                name=f"Company {i}",
                ticker=f"C{i:02d}",
                cik=f"{i:010d}",
                sector="Technology",
            )
            for i in range(1, 101)
        )
        with pytest.raises(ValueError, match="Company ranks must be unique"):
            Fortune100Registry(companies=companies)

    def test_invalid_registry_duplicate_ciks(self) -> None:
        """Test error when companies have duplicate CIKs."""
        companies = tuple(
            Company(
                rank=i,
                name=f"Company {i}",
                ticker=f"C{i:02d}",
                cik="0000000001",  # All same CIK
                sector="Technology",
            )
            for i in range(1, 101)
        )
        with pytest.raises(ValueError, match="Company CIKs must be unique"):
            Fortune100Registry(companies=companies)

    def test_get_by_cik_walmart(self, registry: Fortune100Registry) -> None:
        """Test lookup Walmart by CIK."""
        company = registry.get_by_cik("0000104169")
        assert company is not None
        assert company.name == "Walmart Inc."
        assert company.ticker == "WMT"
        assert company.rank == 1

    def test_get_by_cik_apple(self, registry: Fortune100Registry) -> None:
        """Test lookup Apple by CIK."""
        company = registry.get_by_cik("0000320193")
        assert company is not None
        assert company.name == "Apple Inc."
        assert company.ticker == "AAPL"
        assert company.rank == 3

    def test_get_by_cik_not_found(self, registry: Fortune100Registry) -> None:
        """Test lookup non-existent CIK returns None."""
        company = registry.get_by_cik("9999999999")
        assert company is None

    def test_get_by_cik_normalizes_padding(self, sample_registry: Fortune100Registry) -> None:
        """Test CIK lookup normalizes zero-padding."""
        # CIK stored as "0000000001", query with "1"
        company = sample_registry.get_by_cik("1")
        assert company is not None
        assert company.rank == 1

    def test_get_by_ticker_apple(self, registry: Fortune100Registry) -> None:
        """Test lookup Apple by ticker."""
        company = registry.get_by_ticker("AAPL")
        assert company is not None
        assert company.name == "Apple Inc."
        assert company.cik == "0000320193"

    def test_get_by_ticker_case_insensitive(self, registry: Fortune100Registry) -> None:
        """Test ticker lookup is case-insensitive."""
        company_upper = registry.get_by_ticker("AAPL")
        company_lower = registry.get_by_ticker("aapl")
        company_mixed = registry.get_by_ticker("AaPl")

        assert company_upper is not None
        assert company_lower is not None
        assert company_mixed is not None
        assert company_upper.name == company_lower.name == company_mixed.name

    def test_get_by_ticker_not_found(self, registry: Fortune100Registry) -> None:
        """Test lookup non-existent ticker returns None."""
        company = registry.get_by_ticker("INVALID")
        assert company is None

    def test_get_by_rank_1(self, registry: Fortune100Registry) -> None:
        """Test lookup rank 1 (Walmart)."""
        company = registry.get_by_rank(1)
        assert company is not None
        assert company.name == "Walmart Inc."

    def test_get_by_rank_100(self, registry: Fortune100Registry) -> None:
        """Test lookup rank 100."""
        company = registry.get_by_rank(100)
        assert company is not None
        assert company.rank == 100

    def test_get_by_rank_not_found(self, registry: Fortune100Registry) -> None:
        """Test lookup invalid rank returns None."""
        company = registry.get_by_rank(101)
        assert company is None

    def test_get_by_rank_range_top_10(self, registry: Fortune100Registry) -> None:
        """Test get top 10 companies."""
        top_10 = registry.get_by_rank_range(1, 10)
        assert len(top_10) == 10
        assert top_10[0].rank == 1
        assert top_10[9].rank == 10
        # Verify sorted by rank
        assert [c.rank for c in top_10] == list(range(1, 11))

    def test_get_by_rank_range_middle(self, registry: Fortune100Registry) -> None:
        """Test get middle-ranked companies."""
        middle = registry.get_by_rank_range(45, 55)
        assert len(middle) == 11
        assert middle[0].rank == 45
        assert middle[-1].rank == 55

    def test_get_by_rank_range_single(self, registry: Fortune100Registry) -> None:
        """Test get single company via range."""
        single = registry.get_by_rank_range(50, 50)
        assert len(single) == 1
        assert single[0].rank == 50

    def test_get_by_rank_range_invalid_order(self, registry: Fortune100Registry) -> None:
        """Test error when start > end."""
        with pytest.raises(ValueError, match="Start rank .* must be <= end rank"):
            registry.get_by_rank_range(10, 5)

    def test_filter_by_sector_technology(self, registry: Fortune100Registry) -> None:
        """Test filter by Technology sector."""
        tech_companies = registry.filter_by_sector("Technology")
        assert len(tech_companies) > 0
        assert all(c.sector == "Technology" for c in tech_companies)
        # Verify sorted by rank
        ranks = [c.rank for c in tech_companies]
        assert ranks == sorted(ranks)

    def test_filter_by_sector_case_insensitive(self, registry: Fortune100Registry) -> None:
        """Test sector filter is case-insensitive."""
        tech_upper = registry.filter_by_sector("TECHNOLOGY")
        tech_lower = registry.filter_by_sector("technology")
        tech_mixed = registry.filter_by_sector("TechNology")

        assert len(tech_upper) == len(tech_lower) == len(tech_mixed)
        assert tech_upper == tech_lower == tech_mixed

    def test_filter_by_sector_healthcare(self, registry: Fortune100Registry) -> None:
        """Test filter by Healthcare sector."""
        healthcare = registry.filter_by_sector("Healthcare")
        assert len(healthcare) > 0
        assert all(c.sector == "Healthcare" for c in healthcare)

    def test_filter_by_sector_not_found(self, registry: Fortune100Registry) -> None:
        """Test filter by non-existent sector returns empty list."""
        companies = registry.filter_by_sector("NonExistentSector")
        assert companies == []

    def test_get_all_returns_100(self, registry: Fortune100Registry) -> None:
        """Test get_all returns all 100 companies."""
        all_companies = registry.get_all()
        assert len(all_companies) == 100

    def test_get_all_sorted_by_rank(self, registry: Fortune100Registry) -> None:
        """Test get_all returns companies sorted by rank."""
        all_companies = registry.get_all()
        ranks = [c.rank for c in all_companies]
        assert ranks == list(range(1, 101))

    def test_top_20_companies_present(self, registry: Fortune100Registry) -> None:
        """Test that all top 20 companies are present with correct data."""
        expected_top_20 = [
            ("Walmart Inc.", "WMT", "0000104169"),
            ("Amazon.com Inc.", "AMZN", "0001018724"),
            ("Apple Inc.", "AAPL", "0000320193"),
            ("UnitedHealth Group Inc.", "UNH", "0000731766"),
            ("Berkshire Hathaway Inc.", "BRK.B", "0001067983"),
            ("CVS Health Corp.", "CVS", "0000064803"),
            ("Exxon Mobil Corp.", "XOM", "0000034088"),
            ("Alphabet Inc.", "GOOGL", "0001652044"),
            ("McKesson Corp.", "MCK", "0000927653"),
            ("Cencora Inc.", "COR", "0001140859"),
            ("Costco Wholesale Corp.", "COST", "0000909832"),
            ("Microsoft Corp.", "MSFT", "0000789019"),
            ("Cigna Group", "CI", "0001739940"),
            ("Cardinal Health Inc.", "CAH", "0000721371"),
            ("Chevron Corp.", "CVX", "0000093410"),
            ("JPMorgan Chase & Co.", "JPM", "0000019617"),
            ("Kroger Co.", "KR", "0000056873"),
            ("Walgreens Boots Alliance Inc.", "WBA", "0001618921"),
            ("Bank of America Corp.", "BAC", "0000070858"),
            ("Ford Motor Co.", "F", "0000037996"),
        ]

        for rank, (name, ticker, cik) in enumerate(expected_top_20, start=1):
            company = registry.get_by_rank(rank)
            assert company is not None, f"Company at rank {rank} not found"
            assert company.name == name, f"Rank {rank}: expected {name}, got {company.name}"
            assert company.ticker == ticker, f"Rank {rank}: expected ticker {ticker}, got {company.ticker}"
            assert company.cik == cik, f"Rank {rank}: expected CIK {cik}, got {company.cik}"

    def test_from_json_custom_file(self, tmp_path: Path) -> None:
        """Test loading registry from custom JSON file."""
        # Create test data
        test_data = {
            "version": "test",
            "companies": [
                {
                    "rank": i,
                    "name": f"Company {i}",
                    "ticker": f"C{i:02d}",
                    "cik": f"{i:010d}",
                    "sector": "Technology",
                }
                for i in range(1, 101)
            ],
        }

        # Write to temp file
        test_file = tmp_path / "test_fortune100.json"
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        # Load from file
        registry = Fortune100Registry.from_json(test_file)
        assert len(registry.companies) == 100
        assert registry.get_by_rank(1).name == "Company 1"

    def test_from_json_file_not_found(self) -> None:
        """Test error when JSON file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            Fortune100Registry.from_json("/nonexistent/path/file.json")

    def test_sector_distribution(self, registry: Fortune100Registry) -> None:
        """Test that multiple sectors are represented."""
        all_sectors = {c.sector for c in registry.companies}
        # Should have multiple sectors (Technology, Healthcare, Retail, etc.)
        assert len(all_sectors) >= 5, f"Expected at least 5 sectors, got {len(all_sectors)}"

    def test_all_ciks_10_digits(self, registry: Fortune100Registry) -> None:
        """Test that all CIKs are 10-digit zero-padded strings."""
        for company in registry.companies:
            assert len(company.cik) == 10, f"CIK {company.cik} for {company.name} is not 10 digits"
            assert company.cik.isdigit(), f"CIK {company.cik} for {company.name} contains non-digits"

    def test_all_ranks_unique_and_sequential(self, registry: Fortune100Registry) -> None:
        """Test that ranks are unique and cover 1-100."""
        ranks = {c.rank for c in registry.companies}
        assert ranks == set(range(1, 101)), "Ranks must be unique and cover 1-100"

    def test_major_tech_companies_present(self, registry: Fortune100Registry) -> None:
        """Test that major tech companies are in the registry."""
        expected_tech = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
        for ticker in expected_tech:
            company = registry.get_by_ticker(ticker)
            assert company is not None, f"Expected tech company {ticker} not found"
            assert company.sector in ["Technology", "Automotive"], f"{ticker} has unexpected sector: {company.sector}"

    def test_major_healthcare_companies_present(self, registry: Fortune100Registry) -> None:
        """Test that major healthcare companies are in the registry."""
        expected_healthcare = ["UNH", "CVS", "MCK", "JNJ", "PFE"]
        for ticker in expected_healthcare:
            company = registry.get_by_ticker(ticker)
            assert company is not None, f"Expected healthcare company {ticker} not found"
            assert company.sector == "Healthcare", f"{ticker} has unexpected sector: {company.sector}"


class TestRegistryIntegration:
    """Integration tests for Fortune 100 registry."""

    def test_full_workflow_lookup_and_filter(self) -> None:
        """Test complete workflow: load, lookup, filter."""
        # Load registry
        registry = Fortune100Registry.load_default()

        # Get Apple by ticker
        apple = registry.get_by_ticker("AAPL")
        assert apple is not None

        # Get Apple by CIK
        apple_by_cik = registry.get_by_cik(apple.cik)
        assert apple_by_cik == apple

        # Get Apple by rank
        apple_by_rank = registry.get_by_rank(apple.rank)
        assert apple_by_rank == apple

        # Filter by sector
        tech_companies = registry.filter_by_sector(apple.sector)
        assert apple in tech_companies

    def test_top_10_all_lookup_methods(self) -> None:
        """Test that top 10 companies can be found via all lookup methods."""
        registry = Fortune100Registry.load_default()
        top_10 = registry.get_by_rank_range(1, 10)

        for company in top_10:
            # Verify CIK lookup
            assert registry.get_by_cik(company.cik) == company

            # Verify ticker lookup (skip N/A tickers)
            if company.ticker != "N/A":
                assert registry.get_by_ticker(company.ticker) == company

            # Verify rank lookup
            assert registry.get_by_rank(company.rank) == company
