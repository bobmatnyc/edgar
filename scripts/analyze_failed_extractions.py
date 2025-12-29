#!/usr/bin/env python3
"""Analyze failed extractions to discover correct table patterns.

This script fetches the actual HTML from failed companies and analyzes
the table structures to identify why extraction failed and what patterns
we should look for.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bs4 import BeautifulSoup
from edgar.data.fortune100 import Fortune100Registry
from edgar.services.sec_edgar_client import SecEdgarClient


async def analyze_def14a_failures():
    """Analyze DEF 14A failures (Amazon, Berkshire, Exxon)."""
    print("=" * 80)
    print("ANALYZING DEF 14A FAILURES (SCT)")
    print("=" * 80)

    client = SecEdgarClient()
    registry = Fortune100Registry.load_default()

    failed_companies = [
        ("Amazon.com Inc.", "0001018724"),
        ("Berkshire Hathaway Inc.", "0001067983"),
        ("Exxon Mobil Corporation", "0000034088"),
    ]

    for company_name, cik in failed_companies:
        print(f"\n{'='*80}")
        print(f"Analyzing: {company_name} (CIK: {cik})")
        print(f"{'='*80}")

        try:
            # Fetch latest DEF 14A filing
            filing = await client.get_latest_filing(cik, "DEF 14A")
            print(f"  Filing Date: {filing['filing_date']}")
            print(f"  URL: {filing['url']}")

            # Fetch HTML
            html = await client.fetch_filing_html(filing["url"])
            soup = BeautifulSoup(html, "html.parser")

            # Search for compensation-related headers
            print("\n  Looking for compensation table headers...")
            comp_keywords = [
                "compensation",
                "summary compensation",
                "executive compensation",
                "named executive",
                "compensation table",
            ]

            found_headers = []
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
                text = tag.get_text(strip=True).lower()
                if any(keyword in text for keyword in comp_keywords):
                    found_headers.append((tag.name, text[:100]))

            print(f"  Found {len(found_headers)} potential headers:")
            for tag_name, header_text in found_headers[:5]:
                print(f"    [{tag_name}] {header_text}")

            # Find all tables and analyze them
            print("\n  Analyzing tables...")
            tables = soup.find_all("table")
            print(f"  Total tables found: {len(tables)}")

            # Look for tables with compensation keywords
            comp_tables = []
            for i, table in enumerate(tables):
                table_text = table.get_text().lower()
                if "salary" in table_text and ("stock" in table_text or "total" in table_text):
                    comp_tables.append((i, table))

            print(f"  Tables with compensation keywords: {len(comp_tables)}")

            for i, (table_idx, table) in enumerate(comp_tables[:3]):
                print(f"\n  Table #{table_idx} preview:")
                rows = table.find_all("tr")[:5]  # First 5 rows
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    cell_texts = [cell.get_text(strip=True)[:30] for cell in cells]
                    print(f"    | {' | '.join(cell_texts)}")

            # Save HTML snippet for manual inspection
            output_dir = Path("output/debug")
            output_dir.mkdir(parents=True, exist_ok=True)

            if comp_tables:
                # Save the most promising table
                _, best_table = comp_tables[0]
                output_file = output_dir / f"{company_name.replace(' ', '_')}_SCT_table.html"
                with open(output_file, "w") as f:
                    f.write(str(best_table.prettify()))
                print(f"\n  Saved table HTML to: {output_file}")

        except Exception as e:
            print(f"  ERROR: {e}")

        await asyncio.sleep(0.2)  # Rate limiting


async def analyze_10k_failures():
    """Analyze 10-K failures (companies with $0 tax)."""
    print("\n" * 2)
    print("=" * 80)
    print("ANALYZING 10-K FAILURES (Tax)")
    print("=" * 80)

    client = SecEdgarClient()
    registry = Fortune100Registry.load_default()

    # Sample some companies that might have $0 tax
    test_companies = [
        ("Apple Inc.", "0000320193"),
        ("Microsoft Corporation", "0000789019"),
        ("Alphabet Inc.", "0001652044"),
    ]

    for company_name, cik in test_companies:
        print(f"\n{'='*80}")
        print(f"Analyzing: {company_name} (CIK: {cik})")
        print(f"{'='*80}")

        try:
            # Fetch latest 10-K filing
            filing = await client.get_latest_filing(cik, "10-K")
            print(f"  Filing Date: {filing['filing_date']}")
            print(f"  URL: {filing['url']}")

            # Fetch HTML
            html = await client.fetch_filing_html(filing["url"])
            soup = BeautifulSoup(html, "html.parser")

            # Search for tax-related headers
            print("\n  Looking for tax table headers...")
            tax_keywords = [
                "provision for income taxes",
                "income tax expense",
                "components of income tax",
                "income taxes",
                "tax provision",
            ]

            found_headers = []
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
                text = tag.get_text(strip=True).lower()
                if any(keyword in text for keyword in tax_keywords):
                    if "narrative" not in text and "footnote" not in text:
                        found_headers.append((tag.name, text[:100]))

            print(f"  Found {len(found_headers)} potential headers:")
            for tag_name, header_text in found_headers[:5]:
                print(f"    [{tag_name}] {header_text}")

            # Find all tables and analyze them
            print("\n  Analyzing tables...")
            tables = soup.find_all("table")
            print(f"  Total tables found: {len(tables)}")

            # Look for tables with tax keywords
            tax_tables = []
            for i, table in enumerate(tables):
                table_text = table.get_text().lower()
                has_location = any(loc in table_text for loc in ["federal", "state", "foreign"])
                has_timing = any(timing in table_text for timing in ["current", "deferred"])

                if has_location or has_timing:
                    tax_tables.append((i, table, has_location, has_timing))

            print(f"  Tables with tax keywords: {len(tax_tables)}")

            for i, (table_idx, table, has_location, has_timing) in enumerate(tax_tables[:3]):
                print(f"\n  Table #{table_idx} (location={has_location}, timing={has_timing}):")
                rows = table.find_all("tr")[:7]  # First 7 rows
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    cell_texts = [cell.get_text(strip=True)[:30] for cell in cells]
                    print(f"    | {' | '.join(cell_texts)}")

            # Save HTML snippet for manual inspection
            output_dir = Path("output/debug")
            output_dir.mkdir(parents=True, exist_ok=True)

            if tax_tables:
                # Save the most promising table
                _, best_table, _, _ = tax_tables[0]
                output_file = output_dir / f"{company_name.replace(' ', '_')}_tax_table.html"
                with open(output_file, "w") as f:
                    f.write(str(best_table.prettify()))
                print(f"\n  Saved table HTML to: {output_file}")

        except Exception as e:
            print(f"  ERROR: {e}")

        await asyncio.sleep(0.2)  # Rate limiting


async def main():
    """Main entry point."""
    print("\nEDGAR Self-Refinement: Analyzing Failed Extractions")
    print("=" * 80)
    print("This script fetches actual HTML from failed companies to identify")
    print("the correct table patterns that we should be looking for.")
    print("=" * 80)

    # Analyze DEF 14A failures
    await analyze_def14a_failures()

    # Analyze 10-K failures
    await analyze_10k_failures()

    print("\n" * 2)
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("Check output/debug/ for saved table HTML snippets")
    print("Next step: Update extractors based on discovered patterns")


if __name__ == "__main__":
    asyncio.run(main())
