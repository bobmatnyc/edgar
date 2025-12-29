#!/usr/bin/env python3
"""Debug table detection to understand why SCT tables aren't being found."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bs4 import BeautifulSoup
from edgar.services.sec_edgar_client import SecEdgarClient


async def debug_berkshire_sct():
    """Debug Berkshire Hathaway SCT detection."""
    print("=" * 80)
    print("DEBUGGING BERKSHIRE HATHAWAY SCT DETECTION")
    print("=" * 80)

    client = SecEdgarClient()

    # Fetch filing
    filing = await client.get_latest_filing("0001067983", "DEF 14A")
    html = await client.fetch_filing_html(filing["url"])
    soup = BeautifulSoup(html, "html.parser")

    # Look for SCT header
    sct_patterns = [
        "summary compensation table",
        "summary of compensation",
    ]

    print("\nSearching for SCT headers...")
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
        text = tag.get_text(strip=True).lower()
        if any(pattern in text for pattern in sct_patterns):
            if "narrative" not in text and "footnote" not in text:
                print(f"\n✅ Found header: {text[:100]}")
                print(f"   Tag: {tag.name}")

                # Find next table
                table = tag.find_next("table")
                if table:
                    print(f"   ✅ Found table after header")

                    # Check if it looks like SCT
                    table_text = table.get_text().lower()
                    indicators = ["salary", "stock", "total"]
                    matches = sum(1 for i in indicators if i in table_text)
                    print(f"   Indicators found: {matches}/3 (salary, stock, total)")

                    if matches >= 2:
                        print(f"   ✅ Table SHOULD pass _looks_like_sct()")
                    else:
                        print(f"   ❌ Table FAILS _looks_like_sct() - needs >= 2 indicators")
                        print(f"   Table preview:")
                        rows = table.find_all("tr")[:3]
                        for row in rows:
                            cells = row.find_all(["td", "th"])
                            cell_texts = [cell.get_text(strip=True)[:20] for cell in cells]
                            print(f"     | {' | '.join(cell_texts)}")
                else:
                    print(f"   ❌ No table found after header")


async def debug_apple_tax():
    """Debug Apple tax table extraction."""
    print("\n" * 2)
    print("=" * 80)
    print("DEBUGGING APPLE TAX EXTRACTION")
    print("=" * 80)

    client = SecEdgarClient()

    # Fetch filing
    filing = await client.get_latest_filing("0000320193", "10-K")
    html = await client.fetch_filing_html(filing["url"])
    soup = BeautifulSoup(html, "html.parser")

    # Look for tax header
    tax_patterns = [
        "provision for income taxes",
        "income tax expense",
    ]

    print("\nSearching for tax headers...")
    found_count = 0
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
        text = tag.get_text(strip=True).lower()
        if any(pattern in text for pattern in tax_patterns):
            if "narrative" not in text and "footnote" not in text and "note" not in text:
                found_count += 1
                if found_count <= 3:
                    print(f"\n✅ Found header #{found_count}: {text[:80]}")
                    print(f"   Tag: {tag.name}")

                    # Find next table
                    table = tag.find_next("table")
                    if table:
                        print(f"   ✅ Found table after header")

                        # Check the table content
                        rows = table.find_all("tr")
                        print(f"   Table has {len(rows)} rows")
                        print(f"   First 5 rows:")
                        for i, row in enumerate(rows[:5]):
                            cells = row.find_all(["td", "th"])
                            cell_texts = [cell.get_text(strip=True)[:30] for cell in cells]
                            print(f"     Row {i}: | {' | '.join(cell_texts)}")

                        # Check for provision row
                        table_text = table.get_text().lower()
                        if "provision for income tax" in table_text:
                            print(f"   ✅ Table contains 'provision for income tax'")

                            # Look for years
                            import re

                            years_found = re.findall(r"20[12][0-9]", table.get_text())
                            print(f"   Years found: {years_found[:5]}")

                    else:
                        print(f"   ❌ No table found after header")

    print(f"\nTotal headers found: {found_count}")


async def main():
    """Main entry point."""
    await debug_berkshire_sct()
    await debug_apple_tax()


if __name__ == "__main__":
    asyncio.run(main())
