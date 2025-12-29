#!/usr/bin/env python3
"""Fortune 100 Company Registry Demo.

This script demonstrates how to use the Fortune 100 registry
to look up companies and filter by various criteria.
"""

from edgar.data import Fortune100Registry


def main() -> None:
    """Demonstrate Fortune 100 registry functionality."""
    # Load the default Fortune 100 registry
    registry = Fortune100Registry.load_default()
    print(f"Loaded {len(registry.companies)} Fortune 100 companies\n")

    # Example 1: Lookup by CIK
    print("=" * 60)
    print("Example 1: Lookup by CIK")
    print("=" * 60)
    apple = registry.get_by_cik("0000320193")
    if apple:
        print(f"Company: {apple.name}")
        print(f"Ticker: {apple.ticker}")
        print(f"Rank: #{apple.rank}")
        print(f"Sector: {apple.sector}")
        print(f"CIK: {apple.cik}\n")

    # Example 2: Lookup by ticker
    print("=" * 60)
    print("Example 2: Lookup by ticker (case-insensitive)")
    print("=" * 60)
    walmart = registry.get_by_ticker("wmt")
    if walmart:
        print(f"Company: {walmart.name}")
        print(f"Rank: #{walmart.rank}")
        print(f"CIK: {walmart.cik}\n")

    # Example 3: Get top 10 companies
    print("=" * 60)
    print("Example 3: Top 10 Fortune 100 Companies")
    print("=" * 60)
    top_10 = registry.get_by_rank_range(1, 10)
    for company in top_10:
        print(f"{company.rank:2d}. {company.name:40s} ({company.ticker:6s}) - {company.sector}")
    print()

    # Example 4: Filter by sector
    print("=" * 60)
    print("Example 4: Technology Companies")
    print("=" * 60)
    tech_companies = registry.filter_by_sector("Technology")
    print(f"Found {len(tech_companies)} technology companies:\n")
    for company in tech_companies[:5]:  # Show first 5
        print(f"#{company.rank:2d} - {company.name:35s} ({company.ticker})")
    if len(tech_companies) > 5:
        print(f"... and {len(tech_companies) - 5} more\n")

    # Example 5: Healthcare companies in top 50
    print("=" * 60)
    print("Example 5: Healthcare Companies in Top 50")
    print("=" * 60)
    healthcare = registry.filter_by_sector("Healthcare")
    top_50_healthcare = [c for c in healthcare if c.rank <= 50]
    print(f"Found {len(top_50_healthcare)} healthcare companies in top 50:\n")
    for company in top_50_healthcare:
        print(f"#{company.rank:2d} - {company.name:40s} ({company.ticker:6s})")
    print()

    # Example 6: Sector distribution
    print("=" * 60)
    print("Example 6: Sector Distribution")
    print("=" * 60)
    all_companies = registry.get_all()
    sectors: dict[str, int] = {}
    for company in all_companies:
        sectors[company.sector] = sectors.get(company.sector, 0) + 1

    for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
        print(f"{sector:25s}: {count:2d} companies")


if __name__ == "__main__":
    main()
