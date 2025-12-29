"""
Test script for SCT (Summary Compensation Table) extraction.

Tests the SCTExtractorService on 3 sample companies with different
fiscal year ends to validate extraction accuracy.

Sample Companies:
1. Apple (AAPL) - September FYE, CIK 0000320193
2. Walmart (WMT) - January FYE, CIK 0000104169
3. JPMorgan Chase (JPM) - December FYE, CIK 0000019617

Usage:
    python scripts/test_sct_extraction.py

Requirements:
    - OPENROUTER_API_KEY environment variable set
    - Internet connection for SEC EDGAR access
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables from .env.local
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.local", override=True)

from edgar_analyzer.clients.openrouter_client import OpenRouterClient
from edgar_analyzer.services.sct_extractor_service import SCTExtractorService


# ============================================================================
# TEST CASES
# ============================================================================

TEST_COMPANIES = [
    {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "cik": "0000320193",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000130817924000010/laapl2024_def14a.htm",
        "fiscal_year_end": "September",
        "expected_ceo": "Tim Cook",
        "expected_executives": 5,
    },
    {
        "name": "Walmart Inc.",
        "ticker": "WMT",
        "cik": "0000104169",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/104169/000010416924000078/wmt-20240424.htm",
        "fiscal_year_end": "January",
        "expected_ceo": "C. Douglas McMillon",
        "expected_executives": 5,
    },
    {
        "name": "JPMorgan Chase & Co.",
        "ticker": "JPM",
        "cik": "0000019617",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/19617/000001961724000273/jpm-20240406.htm",
        "fiscal_year_end": "December",
        "expected_ceo": "Jamie Dimon",
        "expected_executives": 5,
    },
]


# ============================================================================
# TEST FUNCTIONS
# ============================================================================


async def test_single_extraction(
    service: SCTExtractorService,
    company: dict,
) -> dict:
    """
    Test SCT extraction for a single company.

    Args:
        service: SCTExtractorService instance
        company: Company info dict

    Returns:
        Test result dict with success/failure details
    """
    print(f"\n{'='*80}")
    print(f"Testing: {company['name']} ({company['ticker']})")
    print(f"CIK: {company['cik']}")
    print(f"Fiscal Year End: {company['fiscal_year_end']}")
    print(f"Filing URL: {company['filing_url']}")
    print(f"{'='*80}\n")

    result = await service.extract_sct(
        filing_url=company["filing_url"],
        cik=company["cik"],
        company_name=company["name"],
        ticker=company["ticker"],
    )

    test_result = {
        "company": company["name"],
        "ticker": company["ticker"],
        "cik": company["cik"],
        "success": result.success,
        "extraction_time_seconds": result.extraction_time_seconds,
        "model_used": result.model_used,
    }

    if result.success:
        data = result.data
        print(f"✅ Extraction SUCCESSFUL")
        print(f"   Extraction time: {result.extraction_time_seconds:.2f}s")
        print(f"   Model used: {result.model_used}")
        print(f"\nExtracted Data:")
        print(f"   Company: {data.company_name}")
        print(f"   Ticker: {data.ticker}")
        print(f"   CIK: {data.cik}")
        print(f"   Filing Date: {data.filing_date}")
        print(f"   Fiscal Years: {data.fiscal_years}")
        print(f"   Executives: {len(data.executives)}")

        # Validate CEO
        ceo = data.get_ceo()
        if ceo:
            print(f"\n   CEO: {ceo.name}")
            print(f"   CEO Position: {ceo.position}")
            print(f"   CEO Compensation (most recent year):")
            if ceo.compensation_by_year:
                latest = ceo.compensation_by_year[0]
                print(f"      Year: {latest.year}")
                print(f"      Salary: ${latest.salary:,}")
                print(f"      Stock Awards: ${latest.stock_awards:,}")
                print(f"      Total: ${latest.total:,}")

            # Check CEO name matches expected
            if ceo.name == company["expected_ceo"]:
                print(f"   ✅ CEO name matches expected: {company['expected_ceo']}")
                test_result["ceo_match"] = True
            else:
                print(f"   ⚠️  CEO name mismatch!")
                print(f"      Expected: {company['expected_ceo']}")
                print(f"      Got: {ceo.name}")
                test_result["ceo_match"] = False
        else:
            print(f"   ⚠️  No CEO identified")
            test_result["ceo_match"] = False

        # List all executives
        print(f"\n   All Executives:")
        for i, exec in enumerate(data.executives, 1):
            years_count = len(exec.compensation_by_year)
            latest_total = exec.compensation_by_year[0].total if exec.compensation_by_year else 0
            print(f"      {i}. {exec.name} - {exec.position}")
            print(f"         Years: {years_count}, Latest Total: ${latest_total:,}")

        # Check executive count
        if len(data.executives) == company["expected_executives"]:
            print(f"\n   ✅ Executive count matches expected: {company['expected_executives']}")
            test_result["executive_count_match"] = True
        else:
            print(f"\n   ⚠️  Executive count mismatch!")
            print(f"      Expected: {company['expected_executives']}")
            print(f"      Got: {len(data.executives)}")
            test_result["executive_count_match"] = False

        # Validate totals for spot check
        print(f"\n   Validation Checks:")
        total_errors = 0
        for exec in data.executives:
            for comp_year in exec.compensation_by_year:
                calculated = (
                    comp_year.salary +
                    comp_year.bonus +
                    comp_year.stock_awards +
                    comp_year.option_awards +
                    comp_year.non_equity_incentive +
                    comp_year.change_in_pension +
                    comp_year.all_other_compensation
                )
                if abs(calculated - comp_year.total) > 1:
                    print(f"      ❌ Total mismatch: {exec.name} ({comp_year.year})")
                    print(f"         Calculated: ${calculated:,}, Reported: ${comp_year.total:,}")
                    total_errors += 1

        if total_errors == 0:
            print(f"      ✅ All compensation totals validated")
            test_result["totals_valid"] = True
        else:
            print(f"      ❌ {total_errors} total validation errors")
            test_result["totals_valid"] = False

        # Save output to file
        output_dir = Path(__file__).parent.parent / "output" / "sct_extractions"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{company['ticker']}_sct.json"

        with open(output_file, "w") as f:
            json.dump(data.model_dump(), f, indent=2)

        print(f"\n   💾 Saved to: {output_file}")
        test_result["output_file"] = str(output_file)

    else:
        print(f"❌ Extraction FAILED")
        print(f"   Error: {result.error_message}")
        print(f"   Extraction time: {result.extraction_time_seconds:.2f}s")

        test_result["error_message"] = result.error_message

    return test_result


async def run_all_tests():
    """Run SCT extraction tests on all sample companies."""
    print("\n" + "="*80)
    print("SCT EXTRACTION TEST SUITE")
    print("="*80)

    # Initialize OpenRouter client
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENROUTER_API_KEY environment variable not set")
        print("   Set it with: export OPENROUTER_API_KEY='your-key-here'")
        sys.exit(1)

    print(f"\n✅ OpenRouter API key found")

    # Initialize service
    openrouter = OpenRouterClient(
        api_key=api_key,
        model="anthropic/claude-sonnet-4.5"
    )
    service = SCTExtractorService(openrouter)

    print(f"✅ SCTExtractorService initialized")
    print(f"   Model: {openrouter.model}")

    # Run tests
    results = []
    for company in TEST_COMPANIES:
        try:
            result = await test_single_extraction(service, company)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Unexpected error testing {company['name']}: {e}")
            results.append({
                "company": company["name"],
                "ticker": company["ticker"],
                "success": False,
                "error_message": str(e),
            })

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    successful = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"\nOverall: {successful}/{total} extractions successful ({successful/total*100:.1f}%)")

    print(f"\nDetailed Results:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"\n  {status} {result['company']} ({result['ticker']})")
        if result["success"]:
            print(f"     Time: {result['extraction_time_seconds']:.2f}s")
            if result.get("ceo_match"):
                print(f"     ✅ CEO name validated")
            if result.get("executive_count_match"):
                print(f"     ✅ Executive count validated")
            if result.get("totals_valid"):
                print(f"     ✅ Compensation totals validated")
            if result.get("output_file"):
                print(f"     💾 {result['output_file']}")
        else:
            print(f"     Error: {result.get('error_message', 'Unknown error')}")

    print("\n" + "="*80)

    # Exit code based on success
    if successful == total:
        print("\n🎉 All tests passed!")
        return 0
    elif successful > 0:
        print(f"\n⚠️  {total - successful} test(s) failed")
        return 1
    else:
        print("\n❌ All tests failed")
        return 2


# ============================================================================
# MAIN
# ============================================================================


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
