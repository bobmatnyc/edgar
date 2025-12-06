#!/usr/bin/env python3
"""
Test enhanced validation system with web search
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.services.validation_service import EnhancedValidationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_validation_with_sample_data():
    """Test validation system with sample executive data"""

    print("🔍 Testing Enhanced Validation System")
    print("=" * 50)

    # Initialize services
    llm_service = LLMService()

    # Create web search client
    async def web_search_client(query, context=None):
        return await llm_service.web_search_request(query, context)

    validation_service = EnhancedValidationService(
        web_search_client=web_search_client, llm_client=llm_service
    )

    # Test cases with different data quality levels
    test_cases = [
        {
            "name": "Apple Inc.",
            "rank": 3,
            "executives": [
                {
                    "name": "Tim Cook",
                    "title": "Chief Executive Officer",
                    "total_compensation": 63209845,
                    "salary": 18962953,
                    "bonus": 12641969,
                    "stock_awards": 25283938,
                    "option_awards": 6320984,
                },
                {
                    "name": "Jeff Williams",
                    "title": "Chief Operating Officer",
                    "total_compensation": 26961226,
                    "salary": 8088367,
                    "bonus": 5392245,
                    "stock_awards": 10784490,
                    "option_awards": 2696122,
                },
            ],
        },
        {
            "name": "Walmart Inc.",
            "rank": 1,
            "executives": [
                {
                    "name": "Amy E. Hood",  # Wrong executive (Microsoft CFO)
                    "title": "Chief Executive Officer",
                    "total_compensation": 321184,
                    "salary": 96355,
                    "bonus": 64237,
                    "stock_awards": 128474,
                    "option_awards": 32118,
                }
            ],
        },
        {
            "name": "Test Company",
            "rank": 100,
            "executives": [
                {
                    "name": "Total Fees",  # Obviously invalid name
                    "title": "Chief Executive Officer",
                    "total_compensation": 46965000,
                    "salary": 14089500,
                    "bonus": 9393000,
                    "stock_awards": 18786000,
                    "option_awards": 4696500,
                }
            ],
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases):
        company_name = test_case["name"]
        rank = test_case["rank"]
        executives = test_case["executives"]

        print(f"\n🏢 Test Case {i+1}: {company_name}")
        print(f"   📊 {len(executives)} executives to validate")

        try:
            # Run validation
            validation_result = await validation_service.validate_executive_data(
                company_name, rank, executives
            )

            print(f"   ✅ Validation complete")
            print(f"   🎯 Confidence: {validation_result.confidence:.2f}")
            print(f"   ⚠️ Issues: {len(validation_result.issues)}")
            print(f"   💡 Suggestions: {len(validation_result.suggestions)}")

            # Show key issues
            if validation_result.issues:
                print("   🔍 Key Issues:")
                for issue in validation_result.issues[:3]:
                    print(f"     • {issue}")

            # Show key suggestions
            if validation_result.suggestions:
                print("   💡 Key Suggestions:")
                for suggestion in validation_result.suggestions[:2]:
                    print(f"     • {suggestion}")

            results.append(
                {
                    "company": company_name,
                    "rank": rank,
                    "executives_count": len(executives),
                    "validation": {
                        "confidence": validation_result.confidence,
                        "is_valid": validation_result.is_valid,
                        "issues_count": len(validation_result.issues),
                        "suggestions_count": len(validation_result.suggestions),
                        "issues": validation_result.issues,
                        "suggestions": validation_result.suggestions,
                        "web_search_performed": bool(
                            validation_result.web_search_results
                        ),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Validation failed for {company_name}: {e}")
            print(f"   ❌ Error: {str(e)}")
            results.append(
                {
                    "company": company_name,
                    "rank": rank,
                    "executives_count": len(executives),
                    "validation": {"error": str(e)},
                }
            )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tests/results/validation_test_results_{timestamp}.json"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("🎯 VALIDATION TEST SUMMARY")
    print("=" * 50)

    total_tests = len(results)
    successful_validations = sum(1 for r in results if "error" not in r["validation"])
    high_confidence = sum(
        1 for r in results if r["validation"].get("confidence", 0) > 0.7
    )

    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Successful Validations: {successful_validations}")
    print(f"🎯 High Confidence Results: {high_confidence}")
    print(f"💾 Results saved: {output_file}")

    print("\n🚀 Enhanced validation testing complete!")


if __name__ == "__main__":
    asyncio.run(test_validation_with_sample_data())
