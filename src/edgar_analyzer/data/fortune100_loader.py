"""
Fortune 100 Company Registry Loader for Meta-Extractor.

This module provides a loader for Fortune 100 company data from JSON,
adapted from src/edgar/data/fortune100.py for the Meta-Extractor architecture.

Re-uses the original Company and Fortune100Registry dataclasses with a
simplified loader function for Meta-Extractor service layer.

Design Decision: Re-use vs Duplication
- **Re-export**: Maintain compatibility with original Fortune 100 models
- **Simplified API**: Single loader function for service layer
- **Path Resolution**: Automatic path to fortune100_2024.json in data/ dir

Example Usage:
    >>> from edgar_analyzer.data import load_fortune100_registry
    >>> registry = load_fortune100_registry()
    >>> companies = registry.get_by_rank_range(1, 10)
    >>> print(f"Top 10: {[c.name for c in companies]}")
"""

from pathlib import Path
from typing import List

# Re-export Company and Fortune100Registry from original module
from edgar.data.fortune100 import Company, Fortune100Registry

__all__ = [
    "Company",
    "Fortune100Registry",
    "load_fortune100_registry",
    "get_fortune100_companies_dict",
    "load_fortune_100_companies",
]


def load_fortune100_registry() -> Fortune100Registry:
    """
    Load Fortune 100 registry from default JSON file in Meta-Extractor data dir.

    Returns:
        Fortune100Registry instance loaded from fortune100_2024.json

    Raises:
        FileNotFoundError: If fortune100_2024.json not found
        ValueError: If JSON data is invalid

    Example:
        >>> registry = load_fortune100_registry()
        >>> assert len(registry.companies) == 100
        >>> walmart = registry.get_by_rank(1)
        >>> assert walmart.name == "Walmart Inc."
    """
    # Path to fortune100_2024.json in edgar_analyzer/data/
    data_dir = Path(__file__).parent
    json_path = data_dir / "fortune100_2024.json"

    if not json_path.exists():
        raise FileNotFoundError(
            f"Fortune 100 data file not found: {json_path}\n"
            "Expected location: src/edgar_analyzer/data/fortune100_2024.json"
        )

    # Use Fortune100Registry.from_json to load
    return Fortune100Registry.from_json(json_path)


def get_fortune100_companies_dict(
    rank_start: int = 1,
    rank_end: int = 100,
    sector: str | None = None,
) -> List[dict]:
    """
    Get Fortune 100 companies as list of dicts for service layer.

    Convenience function that loads registry and returns companies
    as dicts (for Fortune100Service compatibility).

    Args:
        rank_start: Starting rank (inclusive, default: 1)
        rank_end: Ending rank (inclusive, default: 100)
        sector: Filter by sector (optional, case-insensitive)

    Returns:
        List of company dicts with keys: name, cik, rank, ticker, sector

    Example:
        >>> companies = get_fortune100_companies_dict(rank_start=1, rank_end=10)
        >>> assert len(companies) == 10
        >>> assert companies[0]["rank"] == 1
        >>> assert "name" in companies[0]
        >>> assert "cik" in companies[0]

        >>> tech_companies = get_fortune100_companies_dict(sector="Technology")
        >>> assert all(c["sector"] == "Technology" for c in tech_companies)
    """
    registry = load_fortune100_registry()

    # Filter by rank range
    if sector:
        # Filter by sector first, then rank range
        companies = [
            c
            for c in registry.filter_by_sector(sector)
            if rank_start <= c.rank <= rank_end
        ]
    else:
        # Just rank range
        companies = registry.get_by_rank_range(rank_start, rank_end)

    # Convert to dicts for service layer
    return [
        {
            "name": c.name,
            "cik": c.cik,
            "rank": c.rank,
            "ticker": c.ticker,
            "sector": c.sector,
        }
        for c in companies
    ]


def load_fortune_100_companies(
    rank_start: int = 1,
    rank_end: int = 100,
    sector: str | None = None,
) -> List[dict]:
    """
    Load Fortune 100 companies for recipe execution.

    This is the entry point for recipe python steps.
    Wraps get_fortune100_companies_dict for recipe compatibility.

    Args:
        rank_start: Starting rank (inclusive)
        rank_end: Ending rank (inclusive)
        sector: Optional sector filter

    Returns:
        List of company dicts with name, cik, rank, ticker, sector

    Example:
        >>> companies = load_fortune_100_companies(rank_start=1, rank_end=10)
        >>> assert len(companies) == 10
    """
    return get_fortune100_companies_dict(
        rank_start=rank_start,
        rank_end=rank_end,
        sector=sector,
    )
