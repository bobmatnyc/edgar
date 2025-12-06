#!/usr/bin/env python3
"""
Test FMP API integration with Fortune 1-8 companies
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edgar_analyzer.services.enhanced_data_extraction_service import (
    EnhancedDataExtractionService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Fortune 1-8 companies for testing
FORTUNE_1_8_COMPANIES = [
    {"rank": 1, "name": "Walmart Inc.", "cik": "0000104169"},
    {"rank": 2, "name": "Amazon.com Inc.", "cik": "0001018724"},
    {"rank": 3, "name": "Apple Inc.", "cik": "0000320193"},
    {"rank": 4, "name": "CVS Health Corporation", "cik": "0000064803"},
    {"rank": 5, "name": "UnitedHealth Group Incorporated", "cik": "0000731766"},
    {"rank": 6, "name": "Exxon Mobil Corporation", "cik": "0000034088"},
    {"rank": 7, "name": "Berkshire Hathaway Inc.", "cik": "0001067983"},
    {"rank": 8, "name": "Alphabet Inc.", "cik": "0001652044"},
]


async def test_fmp_api_integration():
    """Test FMP API integration with Fortune 1-8 companies"""

    print("🚀 TESTING FMP API INTEGRATION")
    print("=" * 60)
    print("📊 Testing Financial Modeling Prep API with Fortune 1-8 companies")
    print("🎯 Goal: Get real executive compensation data from SEC filings")

    # Initialize enhanced extraction service
    # Note: Using demo API key for testing - replace with real key for production
    fmp_api_key = os.getenv("FMP_API_KEY", "demo")

    if fmp_api_key == "demo":
        print("⚠️ Using demo API key - limited functionality")
        print("   Get free API key from: https://site.financialmodelingprep.com/")
    else:
        print("✅ Using provided API key")

    extraction_service = EnhancedDataExtractionService(fmp_api_key=fmp_api_key)

    print(f"\n🔍 Testing Fortune 1-8 companies...")

    results = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "FMP API Integration Test",
        "api_key_type": "demo" if fmp_api_key == "demo" else "provided",
        "companies_tested": len(FORTUNE_1_8_COMPANIES),
        "results": [],
    }

    # Test each Fortune 1-8 company
    for company in FORTUNE_1_8_COMPANIES:
        company_name = company["name"]
        rank = company["rank"]
        cik = company["cik"]

        print(f"\n🏢 [{rank}] {company_name}")

        try:
            # Extract compensation data
            result = await extraction_service.extract_executive_compensation(
                company_name=company_name, rank=rank, cik=cik, year=2023
            )

            if result and result.get("success"):
                executives = result.get("executives", [])
                data_source = result.get("data_source", "unknown")

                print(f"   ✅ Success: {len(executives)} executives found")
                print(f"   📊 Data source: {data_source}")

                # Show executive details
                for i, exec_data in enumerate(executives[:3], 1):  # Show top 3
                    name = exec_data.get("name", "Unknown")
                    title = exec_data.get("title", "Unknown")
                    total_comp = exec_data.get("total_compensation", 0)

                    print(f"   {i}. {name} ({title}): ${total_comp:,}")

                if len(executives) > 3:
                    print(f"   ... and {len(executives) - 3} more executives")

                # Calculate company totals
                total_compensation = sum(
                    e.get("total_compensation", 0) for e in executives
                )
                print(f"   💰 Total executive compensation: ${total_compensation:,}")

                results["results"].append(
                    {
                        "company": company_name,
                        "rank": rank,
                        "success": True,
                        "executives_count": len(executives),
                        "total_compensation": total_compensation,
                        "data_source": data_source,
                        "executives": executives,
                    }
                )

            else:
                error = (
                    result.get("error", "Unknown error")
                    if result
                    else "No result returned"
                )
                print(f"   ❌ Failed: {error}")

                results["results"].append(
                    {
                        "company": company_name,
                        "rank": rank,
                        "success": False,
                        "error": error,
                        "data_source": (
                            result.get("data_source", "none") if result else "none"
                        ),
                    }
                )

        except Exception as e:
            logger.error(f"Error testing {company_name}: {e}")
            print(f"   ❌ Exception: {str(e)}")

            results["results"].append(
                {
                    "company": company_name,
                    "rank": rank,
                    "success": False,
                    "error": str(e),
                    "data_source": "error",
                }
            )

    # Close services
    await extraction_service.close()

    # Generate summary
    await generate_test_summary(results)


async def generate_test_summary(results: Dict):
    """Generate comprehensive test summary"""

    print("\n" + "=" * 60)
    print("🎯 FMP API INTEGRATION TEST SUMMARY")
    print("=" * 60)

    total_companies = results["companies_tested"]
    successful = sum(1 for r in results["results"] if r["success"])
    failed = total_companies - successful

    print(f"📊 **TEST RESULTS:**")
    print(f"   Total Companies Tested: {total_companies}")
    print(
        f"   Successful Extractions: {successful} ({successful/total_companies*100:.1f}%)"
    )
    print(f"   Failed Extractions: {failed} ({failed/total_companies*100:.1f}%)")

    # Data source breakdown
    data_sources = {}
    for result in results["results"]:
        if result["success"]:
            source = result["data_source"]
            data_sources[source] = data_sources.get(source, 0) + 1

    if data_sources:
        print(f"\n📈 **DATA SOURCES:**")
        for source, count in data_sources.items():
            print(f"   {source}: {count} companies")

    # Show successful companies
    successful_results = [r for r in results["results"] if r["success"]]

    if successful_results:
        print(f"\n✅ **SUCCESSFUL COMPANIES:**")

        # Sort by total compensation
        successful_results.sort(
            key=lambda x: x.get("total_compensation", 0), reverse=True
        )

        for result in successful_results:
            company = result["company"]
            rank = result["rank"]
            exec_count = result["executives_count"]
            total_comp = result.get("total_compensation", 0)
            source = result["data_source"]

            print(f"   {rank:2d}. {company}")
            print(f"       • {exec_count} executives, ${total_comp:,} total ({source})")

        # Calculate totals
        total_executives = sum(r["executives_count"] for r in successful_results)
        total_compensation = sum(
            r.get("total_compensation", 0) for r in successful_results
        )

        print(f"\n💰 **TOTALS:**")
        print(f"   Total Executives: {total_executives}")
        print(f"   Total Compensation: ${total_compensation:,}")
        print(f"   Average per Executive: ${total_compensation/total_executives:,.0f}")

        # Show top executives
        all_executives = []
        for result in successful_results:
            for exec_data in result["executives"]:
                exec_data["company"] = result["company"]
                exec_data["rank"] = result["rank"]
                all_executives.append(exec_data)

        # Sort by compensation
        all_executives.sort(key=lambda x: x.get("total_compensation", 0), reverse=True)

        print(f"\n🏆 **TOP 10 EXECUTIVES:**")
        for i, exec_data in enumerate(all_executives[:10], 1):
            name = exec_data.get("name", "Unknown")
            company = exec_data.get("company", "Unknown")
            total_comp = exec_data.get("total_compensation", 0)

            print(f"   {i:2d}. {name} ({company}) - ${total_comp:,}")

    # Show failed companies
    failed_results = [r for r in results["results"] if not r["success"]]

    if failed_results:
        print(f"\n❌ **FAILED COMPANIES:**")
        for result in failed_results:
            company = result["company"]
            rank = result["rank"]
            error = result.get("error", "Unknown error")

            print(f"   {rank:2d}. {company}: {error}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"tests/results/fmp_integration_test_{timestamp}.json"

    os.makedirs(os.path.dirname(results_file), exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 **RESULTS SAVED:**")
    print(f"   File: {results_file}")

    # Next steps
    print(f"\n🚀 **NEXT STEPS:**")

    if successful >= 4:  # At least half successful
        print(f"   ✅ FMP API integration working well!")
        print(f"   1. Get production API key for full access")
        print(f"   2. Integrate into Fortune 100 analysis")
        print(f"   3. Replace artificial data with real SEC data")
    else:
        print(f"   ⚠️ Limited success with demo API key")
        print(f"   1. Get free API key from Financial Modeling Prep")
        print(f"   2. Test again with real API key")
        print(f"   3. Consider alternative data sources if needed")

    print(f"\n🎯 FMP API integration test complete!")


if __name__ == "__main__":
    asyncio.run(test_fmp_api_integration())
