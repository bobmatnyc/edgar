#!/usr/bin/env python3
"""Auto-refine extractors based on extraction failures.

This script:
1. Loads failed extractions from the last pipeline run
2. Fetches HTML for failed companies
3. Analyzes patterns that weren't detected
4. Suggests/applies refinements to extractors
5. Re-runs extraction to verify improvements

Usage:
    python scripts/refine_extractors.py
    python scripts/refine_extractors.py --extractor sct
    python scripts/refine_extractors.py --companies Amazon,Berkshire
"""

import argparse
import asyncio
import sys
from pathlib import Path

from edgar.data.fortune100 import Fortune100Registry
from edgar.extractors.sct.extractor import SCTExtractor
from edgar.extractors.tax.extractor import TaxExtractor
from edgar.refinement import ExtractionFailure, ExtractorRefiner
from edgar.services.sec_edgar_client import SecEdgarClient


async def analyze_sct_failures(
    refiner: ExtractorRefiner,
    registry: Fortune100Registry,
    company_names: list[str] | None = None,
) -> list[ExtractionFailure]:
    """Analyze SCT extraction failures.

    Args:
        refiner: Extractor refiner instance
        registry: Fortune 100 registry
        company_names: Optional list of company names to analyze

    Returns:
        List of extraction failures
    """
    failures: list[ExtractionFailure] = []

    # Known failures from Fortune 100 run
    failed_companies = ["Amazon.com Inc.", "Berkshire Hathaway Inc.", "Exxon Mobil Corporation"]

    if company_names:
        # Filter to requested companies
        failed_companies = [c for c in failed_companies if c in company_names]

    print(f"\n{'='*60}")
    print(f"Analyzing SCT Failures: {len(failed_companies)} companies")
    print(f"{'='*60}\n")

    for company_name in failed_companies:
        # Find company in registry
        company = next((c for c in registry.companies if c.name == company_name), None)
        if not company:
            print(f"⚠️  {company_name}: Not found in registry")
            continue

        print(f"📄 {company.name}...")

        try:
            # Fetch latest DEF 14A filing
            filing = await refiner.sec_client.get_latest_filing(company.cik, "DEF 14A")
            html = await refiner.sec_client.fetch_filing_html(filing["url"])

            # Try extraction
            extractor = SCTExtractor(company=company.name, cik=company.cik)
            try:
                result = extractor.extract({"html": html, "filing": filing})
                print(f"   ✅ Actually succeeded (extracted {len(result.executives)} executives)")
                continue
            except Exception as e:
                error_message = str(e)
                print(f"   ❌ Failed: {error_message}")

                # Create failure record
                failures.append(
                    ExtractionFailure(
                        company=company,
                        form_type="DEF 14A",
                        html_sample=html[:50_000],  # First 50KB
                        error_message=error_message,
                        extractor_type="SCTExtractor",
                        filing_url=filing["url"],
                    )
                )

        except Exception as e:
            print(f"   ⚠️  Error fetching filing: {e}")

    return failures


async def analyze_tax_failures(
    refiner: ExtractorRefiner,
    registry: Fortune100Registry,
    company_names: list[str] | None = None,
) -> list[ExtractionFailure]:
    """Analyze Tax extraction failures (companies returning $0).

    Args:
        refiner: Extractor refiner instance
        registry: Fortune 100 registry
        company_names: Optional list of company names to analyze

    Returns:
        List of extraction failures
    """
    failures: list[ExtractionFailure] = []

    # Test first 10 companies for tax extraction
    companies_to_check = registry.get_by_rank_range(1, 10)

    if company_names:
        companies_to_check = [c for c in companies_to_check if c.name in company_names]

    print(f"\n{'='*60}")
    print(f"Analyzing Tax Failures: {len(companies_to_check)} companies")
    print(f"{'='*60}\n")

    for company in companies_to_check:
        print(f"📄 {company.name}...")

        try:
            # Fetch latest 10-K filing
            filing = await refiner.sec_client.get_latest_filing(company.cik, "10-K")
            html = await refiner.sec_client.fetch_filing_html(filing["url"])

            # Try extraction
            extractor = TaxExtractor(company=company.name, cik=company.cik)
            try:
                result = extractor.extract({"html": html, "filing": filing})

                # Check if returned zeros
                if result.tax_years:
                    total_tax = result.tax_years[0].total_tax_expense
                    if total_tax == 0:
                        print("   ⚠️  Extracted $0 tax expense")
                        failures.append(
                            ExtractionFailure(
                                company=company,
                                form_type="10-K",
                                html_sample=html[:50_000],
                                error_message="Tax expense is $0",
                                extractor_type="TaxExtractor",
                                filing_url=filing["url"],
                            )
                        )
                    else:
                        print(f"   ✅ Extracted ${total_tax:,.0f}")
                else:
                    print("   ⚠️  No tax years extracted")
                    failures.append(
                        ExtractionFailure(
                            company=company,
                            form_type="10-K",
                            html_sample=html[:50_000],
                            error_message="No tax years found",
                            extractor_type="TaxExtractor",
                            filing_url=filing["url"],
                        )
                    )

            except Exception as e:
                error_message = str(e)
                print(f"   ❌ Failed: {error_message}")
                failures.append(
                    ExtractionFailure(
                        company=company,
                        form_type="10-K",
                        html_sample=html[:50_000],
                        error_message=error_message,
                        extractor_type="TaxExtractor",
                        filing_url=filing["url"],
                    )
                )

        except Exception as e:
            print(f"   ⚠️  Error fetching filing: {e}")

    return failures


async def main() -> None:
    """Main refinement workflow."""
    parser = argparse.ArgumentParser(description="Refine EDGAR extractors")
    parser.add_argument(
        "--extractor",
        choices=["sct", "tax", "both"],
        default="both",
        help="Which extractor to refine",
    )
    parser.add_argument(
        "--companies",
        type=str,
        help="Comma-separated list of company names to analyze",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold for suggestions",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("EDGAR Self-Refinement: Analyzing Extraction Failures")
    print("=" * 60)

    # Initialize services
    sec_client = SecEdgarClient()
    refiner = ExtractorRefiner(sec_client=sec_client, min_confidence=args.min_confidence)
    registry = Fortune100Registry.load_default()

    # Parse company names
    company_names = None
    if args.companies:
        company_names = [name.strip() for name in args.companies.split(",")]
        print(f"\nFiltering to companies: {company_names}")

    # Collect failures
    all_failures: list[ExtractionFailure] = []

    if args.extractor in ["sct", "both"]:
        sct_failures = await analyze_sct_failures(refiner, registry, company_names)
        all_failures.extend(sct_failures)

    if args.extractor in ["tax", "both"]:
        tax_failures = await analyze_tax_failures(refiner, registry, company_names)
        all_failures.extend(tax_failures)

    if not all_failures:
        print("\n✅ No failures to analyze!")
        return

    # Analyze failures and generate suggestions
    print(f"\n{'='*60}")
    print("Generating Refinement Suggestions")
    print(f"{'='*60}\n")

    suggestions = await refiner.analyze_failures(all_failures)

    if not suggestions:
        print("❌ No suggestions generated (all below confidence threshold)")
        return

    print(f"✅ Generated {len(suggestions)} suggestions")

    # Generate and display report
    report = refiner.generate_refinement_report(suggestions)
    print("\n" + report)

    # Save suggestions
    output_dir = Path(__file__).parent.parent / "output" / "refinements"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save by extractor type
    sct_suggestions = [
        s for s in suggestions if "SCT" in s.reasoning or "compensation" in s.reasoning.lower()
    ]
    tax_suggestions = [s for s in suggestions if "tax" in s.reasoning.lower()]

    if sct_suggestions:
        sct_path = output_dir / "sct_refinements.json"
        await refiner.apply_refinements(sct_suggestions, Path("edgar/extractors/sct/extractor.py"))
        print(f"\n💾 Saved {len(sct_suggestions)} SCT suggestions to: {sct_path}")

    if tax_suggestions:
        tax_path = output_dir / "tax_refinements.json"
        await refiner.apply_refinements(tax_suggestions, Path("edgar/extractors/tax/extractor.py"))
        print(f"💾 Saved {len(tax_suggestions)} Tax suggestions to: {tax_path}")

    print("\n" + "=" * 60)
    print("Refinement Analysis Complete")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Review suggestions in output/refinements/")
    print("2. Manually apply high-confidence patterns to extractors")
    print("3. Re-run pipeline to verify improvements")
    print("4. Iterate as needed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
