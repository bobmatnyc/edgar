#!/usr/bin/env python3
"""Verify that extractor fixes work on previously failed companies.

This script re-runs extraction on companies that failed before the fixes
to verify that the updated extractors now work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar.data.fortune100 import Company
from edgar.extractors.sct import SCTExtractor
from edgar.extractors.tax import TaxExtractor
from edgar.services.sec_edgar_client import SecEdgarClient


async def test_sct_extraction():
    """Test SCT extraction on previously failed companies."""
    print("=" * 80)
    print("TESTING SCT EXTRACTOR FIXES")
    print("=" * 80)

    client = SecEdgarClient()

    test_companies = [
        ("Berkshire Hathaway Inc.", "0001067983"),  # Simplified table (4 columns)
        ("Amazon.com Inc.", "0001018724"),  # Complex table
        ("Apple Inc.", "0000320193"),  # Should still work (no regression)
    ]

    for company_name, cik in test_companies:
        print(f"\n{'='*80}")
        print(f"Testing: {company_name} (CIK: {cik})")
        print(f"{'='*80}")

        try:
            # Fetch latest DEF 14A filing
            filing = await client.get_latest_filing(cik, "DEF 14A")
            print(f"  Filing Date: {filing['filing_date']}")

            # Fetch HTML
            html = await client.fetch_filing_html(filing["url"])

            # Extract data
            extractor = SCTExtractor(company=company_name, cik=cik)
            sct_data = extractor.extract({"html": html, "filing": filing})

            # Print results
            print(f"  ✅ SUCCESS: Extracted {len(sct_data.executives)} executives")
            for exec in sct_data.executives[:2]:  # Show first 2
                print(f"    - {exec.name}: {len(exec.compensation)} years")
                for comp in exec.compensation[:1]:  # Show most recent year
                    print(
                        f"      {comp.year}: Salary=${comp.salary:,.0f}, "
                        f"Stock=${comp.stock_awards:,.0f}, Total=${comp.total:,.0f}"
                    )

        except Exception as e:
            print(f"  ❌ FAILED: {e}")

        await asyncio.sleep(0.2)  # Rate limiting

    print("\n")


async def test_tax_extraction():
    """Test Tax extraction on previously failed companies."""
    print("=" * 80)
    print("TESTING TAX EXTRACTOR FIXES")
    print("=" * 80)

    client = SecEdgarClient()

    test_companies = [
        ("Apple Inc.", "0000320193"),  # Simplified summary table
        ("Microsoft Corporation", "0000789019"),  # Should work
        ("Alphabet Inc.", "0001652044"),  # Simplified summary table
    ]

    for company_name, cik in test_companies:
        print(f"\n{'='*80}")
        print(f"Testing: {company_name} (CIK: {cik})")
        print(f"{'='*80}")

        try:
            # Fetch latest 10-K filing
            filing = await client.get_latest_filing(cik, "10-K")
            print(f"  Filing Date: {filing['filing_date']}")

            # Fetch HTML
            html = await client.fetch_filing_html(filing["url"])

            # Extract data
            extractor = TaxExtractor(company=company_name, cik=cik)
            tax_data = extractor.extract({"html": html, "filing": filing})

            # Print results
            print(f"  ✅ SUCCESS: Extracted {len(tax_data.tax_years)} years")
            for tax_year in tax_data.tax_years[:2]:  # Show first 2 years
                print(f"    - {tax_year.year}:")
                print(f"      Total Tax Expense: ${tax_year.total_tax_expense:,.0f}")
                if tax_year.total_current > 0:
                    print(f"      Current: ${tax_year.total_current:,.0f}")
                if tax_year.total_deferred > 0:
                    print(f"      Deferred: ${tax_year.total_deferred:,.0f}")
                if tax_year.effective_tax_rate > 0:
                    print(f"      Effective Rate: {tax_year.effective_tax_rate:.2%}")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")

        await asyncio.sleep(0.2)  # Rate limiting

    print("\n")


async def main():
    """Main entry point."""
    print("\nEDGAR Extractor Verification")
    print("=" * 80)
    print("Testing updated extractors on previously failed companies")
    print("=" * 80)
    print()

    # Test SCT extractor
    await test_sct_extraction()

    # Test Tax extractor
    await test_tax_extraction()

    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("Next step: Run full Fortune 100 pipeline to measure improvement")
    print("  python3 scripts/fortune100_analysis.py --companies 1-20 -v")


if __name__ == "__main__":
    asyncio.run(main())
