"""Fortune 100 Company Registry with SEC EDGAR CIKs.

This module provides a registry of Fortune 100 companies with their SEC identifiers,
enabling efficient lookup and filtering operations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class Company:
    """Fortune 100 company with SEC identifiers.

    Attributes:
        rank: Fortune 100 rank (1-100)
        name: Official company name
        ticker: Stock ticker symbol
        cik: SEC CIK (10-digit, zero-padded)
        sector: Industry sector
    """

    rank: int
    name: str
    ticker: str
    cik: str
    sector: str

    def __post_init__(self) -> None:
        """Validate company data."""
        if not 1 <= self.rank <= 100:
            raise ValueError(f"Rank must be 1-100, got {self.rank}")
        if len(self.cik) != 10:
            raise ValueError(f"CIK must be 10 digits zero-padded, got {self.cik}")
        if not self.cik.isdigit():
            raise ValueError(f"CIK must contain only digits, got {self.cik}")


@dataclass(frozen=True)
class Fortune100Registry:
    """Registry of Fortune 100 companies with SEC EDGAR CIKs.

    This registry provides efficient lookup operations for Fortune 100 companies
    by CIK, ticker symbol, rank, and sector.

    Attributes:
        companies: Tuple of Company instances (immutable)
    """

    companies: tuple[Company, ...]

    def __post_init__(self) -> None:
        """Validate registry data."""
        if len(self.companies) != 100:
            raise ValueError(
                f"Registry must contain exactly 100 companies, got {len(self.companies)}"
            )

        # Validate unique ranks
        ranks = {c.rank for c in self.companies}
        if len(ranks) != 100:
            raise ValueError("Company ranks must be unique")

        # Validate unique CIKs
        ciks = {c.cik for c in self.companies}
        if len(ciks) != 100:
            raise ValueError("Company CIKs must be unique")

    def get_by_cik(self, cik: str) -> Company | None:
        """Get company by SEC CIK number.

        Args:
            cik: SEC CIK (10-digit, zero-padded)

        Returns:
            Company if found, None otherwise

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> company = registry.get_by_cik("0000104169")
            >>> assert company.name == "Walmart Inc."
        """
        # Normalize CIK to 10 digits
        normalized_cik = cik.zfill(10) if cik.isdigit() else cik
        return next((c for c in self.companies if c.cik == normalized_cik), None)

    def get_by_ticker(self, ticker: str) -> Company | None:
        """Get company by stock ticker symbol.

        Args:
            ticker: Stock ticker symbol (case-insensitive)

        Returns:
            Company if found, None otherwise

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> company = registry.get_by_ticker("AAPL")
            >>> assert company.name == "Apple Inc."
        """
        ticker_upper = ticker.upper()
        return next((c for c in self.companies if c.ticker == ticker_upper), None)

    def get_by_rank(self, rank: int) -> Company | None:
        """Get company by Fortune 100 rank.

        Args:
            rank: Fortune 100 rank (1-100)

        Returns:
            Company if found, None otherwise

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> company = registry.get_by_rank(1)
            >>> assert company.name == "Walmart Inc."
        """
        return next((c for c in self.companies if c.rank == rank), None)

    def get_by_rank_range(self, start: int, end: int) -> list[Company]:
        """Get companies within a rank range (inclusive).

        Args:
            start: Starting rank (inclusive)
            end: Ending rank (inclusive)

        Returns:
            List of companies sorted by rank

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> top_10 = registry.get_by_rank_range(1, 10)
            >>> assert len(top_10) == 10
            >>> assert top_10[0].rank == 1
        """
        if start > end:
            raise ValueError(f"Start rank {start} must be <= end rank {end}")

        companies = [c for c in self.companies if start <= c.rank <= end]
        return sorted(companies, key=lambda c: c.rank)

    def filter_by_sector(self, sector: str) -> list[Company]:
        """Filter companies by industry sector.

        Args:
            sector: Industry sector (case-insensitive)

        Returns:
            List of companies in the sector, sorted by rank

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> tech = registry.filter_by_sector("Technology")
            >>> assert all(c.sector == "Technology" for c in tech)
        """
        sector_lower = sector.lower()
        companies = [c for c in self.companies if c.sector.lower() == sector_lower]
        return sorted(companies, key=lambda c: c.rank)

    def get_all(self) -> list[Company]:
        """Get all companies sorted by rank.

        Returns:
            List of all companies sorted by Fortune 100 rank

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> companies = registry.get_all()
            >>> assert len(companies) == 100
            >>> assert companies[0].rank == 1
        """
        return sorted(self.companies, key=lambda c: c.rank)

    @classmethod
    def load_default(cls) -> "Fortune100Registry":
        """Load Fortune 100 registry from default JSON file.

        Returns:
            Fortune100Registry instance loaded from fortune100_2024.json

        Raises:
            FileNotFoundError: If fortune100_2024.json not found
            ValueError: If JSON data is invalid

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> assert len(registry.companies) == 100
        """
        data_dir = Path(__file__).parent
        json_path = data_dir / "fortune100_2024.json"

        if not json_path.exists():
            raise FileNotFoundError(f"Fortune 100 data file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        companies = tuple(
            Company(
                rank=item["rank"],
                name=item["name"],
                ticker=item["ticker"],
                cik=item["cik"],
                sector=item["sector"],
            )
            for item in data["companies"]
        )

        return cls(companies=companies)

    @classmethod
    def from_json(cls, json_path: Path | str) -> "Fortune100Registry":
        """Load Fortune 100 registry from custom JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            Fortune100Registry instance

        Raises:
            FileNotFoundError: If file not found
            ValueError: If JSON data is invalid
        """
        path = Path(json_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        companies = tuple(
            Company(
                rank=item["rank"],
                name=item["name"],
                ticker=item["ticker"],
                cik=item["cik"],
                sector=item["sector"],
            )
            for item in data["companies"]
        )

        return cls(companies=companies)
