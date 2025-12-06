#!/usr/bin/env python3
"""
Test Breakthrough XBRL Executive Compensation Extraction Service
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

from edgar_analyzer.services.breakthrough_xbrl_service import BreakthroughXBRLService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_breakthrough_xbrl_service():
    """Test the Breakthrough XBRL Service"""

    print("🚀 TESTING BREAKTHROUGH XBRL SERVICE")
    print("=" * 70)
    print("🎯 Using newly discovered XBRL Pay vs Performance data")
    print("📊 This should achieve 90%+ success rate for Fortune 1-8")

    # Initialize service
    service = BreakthroughXBRLService(identity="test.user@example.com")

    # Test Fortune 1-8 companies
    test_companies = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corporation"),
        ("GOOGL", "Alphabet Inc."),
        ("AMZN", "Amazon.com Inc."),
        ("TSLA", "Tesla Inc."),
        ("NVDA", "NVIDIA Corporation"),
    ]

    results = []

    for symbol, company_name in test_companies:
        print(f"\n📊 Testing {company_name} ({symbol})")
        print("-" * 50)

        try:
            # Extract executive compensation using breakthrough method
            result = await service.extract_executive_compensation(symbol, company_name)

            if result["success"]:
                print(f"   ✅ BREAKTHROUGH SUCCESS!")
                print(f"   📄 Filing: {result.get('accession_number', 'N/A')}")
                print(f"   📅 Date: {result.get('filing_date', 'N/A')}")
                print(f"   🔧 Method: {result.get('extraction_method', 'N/A')}")
                print(f"   📊 Data Source: {result.get('data_source', 'N/A')}")
                print(f"   🎯 Quality Score: {result.get('quality_score', 0):.2f}")

                executives = result.get("executives", [])
                print(f"   👥 Executives Found: {len(executives)}")

                total_compensation = 0
                for i, exec_data in enumerate(executives, 1):
                    name = exec_data.get("name", "Unknown")
                    title = exec_data.get("title", "Unknown")
                    total_comp = exec_data.get("total_compensation", 0)
                    actually_paid = exec_data.get("actually_paid_compensation", 0)

                    print(f"      {i}. {name}")
                    print(f"         Title: {title}")
                    print(f"         Total Compensation: ${total_comp:,}")
                    if actually_paid > 0:
                        print(f"         Actually Paid: ${actually_paid:,}")

                    total_compensation += total_comp

                print(f"   💰 Total Executive Compensation: ${total_compensation:,}")

            else:
                print(f"   ❌ Extraction failed: {result.get('reason', 'Unknown')}")
                if result.get("error"):
                    print(f"   🔍 Error: {result['error']}")

            results.append(result)

        except Exception as e:
            print(f"   ❌ Exception during extraction: {e}")
            results.append(
                {
                    "success": False,
                    "symbol": symbol,
                    "company_name": company_name,
                    "reason": "exception",
                    "error": str(e),
                }
            )

    return results


async def analyze_breakthrough_results(results: List[Dict]):
    """Analyze the breakthrough test results"""

    print("\n" + "=" * 70)
    print("🚀 BREAKTHROUGH XBRL SERVICE RESULTS")
    print("=" * 70)

    total_tests = len(results)
    successful_extractions = len([r for r in results if r.get("success")])
    failed_extractions = total_tests - successful_extractions

    print(f"📈 **BREAKTHROUGH RESULTS:**")
    print(f"   Total Companies Tested: {total_tests}")
    print(
        f"   ✅ Successful Extractions: {successful_extractions} ({successful_extractions/total_tests*100:.1f}%)"
    )
    print(
        f"   ❌ Failed Extractions: {failed_extractions} ({failed_extractions/total_tests*100:.1f}%)"
    )

    # Calculate improvement over current system
    current_success_rate = 0.25  # 25% (2/8 Fortune 1-8 companies)
    breakthrough_success_rate = successful_extractions / total_tests

    if breakthrough_success_rate > current_success_rate:
        improvement = (
            (breakthrough_success_rate - current_success_rate)
            / current_success_rate
            * 100
        )
        print(f"   🚀 **IMPROVEMENT: +{improvement:.1f}% better than current system**")

    # Analyze successful extractions
    successful_results = [r for r in results if r.get("success")]
    if successful_results:
        print(f"\n✅ **SUCCESSFUL BREAKTHROUGH EXTRACTIONS:**")

        total_executives = 0
        total_compensation = 0

        for result in successful_results:
            company_name = result["company_name"]
            executives = result.get("executives", [])
            company_total = sum(
                exec_data.get("total_compensation", 0) for exec_data in executives
            )

            total_executives += len(executives)
            total_compensation += company_total

            print(
                f"   🏢 {company_name}: {len(executives)} executives, ${company_total/1_000_000:.1f}M total"
            )

        avg_executives = total_executives / len(successful_results)
        avg_compensation = total_compensation / len(successful_results)

        print(f"\n📊 **BREAKTHROUGH STATISTICS:**")
        print(f"   Total Executives Extracted: {total_executives}")
        print(f"   Average Executives per Company: {avg_executives:.1f}")
        print(
            f"   Total Executive Compensation: ${total_compensation/1_000_000_000:.1f}B"
        )
        print(f"   Average Company Executive Pay: ${avg_compensation/1_000_000:.1f}M")

    # Compare with current system
    print(f"\n📈 **SYSTEM COMPARISON:**")
    print(f"   Current System (Fortune 1-8): ~25% success rate")
    print(
        f"   Breakthrough XBRL System: {breakthrough_success_rate*100:.1f}% success rate"
    )

    if breakthrough_success_rate >= 0.75:
        print(f"   🎯 **BREAKTHROUGH ACHIEVED: 3x better success rate!**")
        print(f"   🚀 **READY FOR PRODUCTION DEPLOYMENT**")
    elif breakthrough_success_rate >= 0.50:
        print(f"   ✅ **SIGNIFICANT IMPROVEMENT: 2x better success rate**")
        print(f"   🔧 **READY FOR INTEGRATION WITH REFINEMENTS**")
    else:
        print(f"   🔧 **NEEDS IMPROVEMENT: Refine XBRL extraction logic**")

    return {
        "total_tests": total_tests,
        "successful_extractions": successful_extractions,
        "success_rate": breakthrough_success_rate,
        "improvement_over_current": (
            improvement if breakthrough_success_rate > current_success_rate else 0
        ),
        "total_executives": total_executives if successful_results else 0,
        "total_compensation": total_compensation if successful_results else 0,
    }


async def main():
    """Main test function"""

    # Run breakthrough tests
    results = await test_breakthrough_xbrl_service()

    # Analyze results
    analysis = await analyze_breakthrough_results(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"tests/results/breakthrough_xbrl_test_{timestamp}.json"

    os.makedirs("tests/results", exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "test_results": results,
                "analysis": analysis,
                "breakthrough_discovery": {
                    "xbrl_pay_vs_performance": True,
                    "structured_executive_data": True,
                    "sec_validated_data": True,
                    "success_rate_improvement": analysis.get(
                        "improvement_over_current", 0
                    ),
                },
            },
            f,
            indent=2,
        )

    print(f"\n💾 Results saved to: {results_file}")

    # Next steps based on results
    print(f"\n🎯 NEXT STEPS:")
    if analysis["success_rate"] >= 0.75:
        print("🚀 1. BREAKTHROUGH CONFIRMED - Integrate into main pipeline")
        print("📊 2. Deploy to Fortune 100 analysis with XBRL priority")
        print("🔧 3. Enhance individual executive compensation breakdown")
        print("💎 4. This solves the Fortune 1-8 data quality problem!")
    elif analysis["success_rate"] >= 0.50:
        print("✅ 1. Significant improvement confirmed - refine and integrate")
        print("🔧 2. Enhance XBRL fact parsing for better individual data")
        print("📊 3. Test with more Fortune companies")
    else:
        print("🔧 1. Debug XBRL extraction issues")
        print("📊 2. Analyze failed extractions for patterns")
        print("🔍 3. Enhance XBRL fact identification and parsing")


if __name__ == "__main__":
    asyncio.run(main())
