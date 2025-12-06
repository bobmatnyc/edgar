#!/usr/bin/env python3
"""
Enhanced Fortune 50 analysis with validation improvements
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.services.validation_service import EnhancedValidationService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def analyze_with_validation():
    """Analyze existing results with enhanced validation"""

    print("🔍 Enhanced Fortune 50 Analysis with Validation")
    print("=" * 60)

    # Load existing results
    results_file = "results/top_100_enhanced_results_20251121_180216.json"

    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return

    with open(results_file, "r") as f:
        original_results = json.load(f)

    print(f"📊 Loaded results for {original_results['total_companies']} companies")

    # Initialize validation service
    llm_service = LLMService()

    async def web_search_client(query, context=None):
        return await llm_service.web_search_request(query, context)

    validation_service = EnhancedValidationService(
        web_search_client=web_search_client, llm_client=llm_service
    )

    # Enhanced results with validation
    enhanced_results = {
        "timestamp": datetime.now().isoformat(),
        "original_timestamp": original_results["timestamp"],
        "total_companies": original_results["total_companies"],
        "successful_extractions": 0,
        "failed_extractions": 0,
        "validation_summary": {
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "total_issues": 0,
            "total_suggestions": 0,
        },
        "companies": [],
    }

    # Process each company with validation
    for i, company in enumerate(original_results["companies"]):
        company_name = company["name"]
        rank = company["rank"]

        print(f"\n🏢 [{rank}/{original_results['total_companies']}] {company_name}")

        if not company["success"] or not company["executives"]:
            print("  ⚠️ No executives data - skipping validation")
            enhanced_results["companies"].append(
                {**company, "validation": None, "enhanced_llm_validation": None}
            )
            enhanced_results["failed_extractions"] += 1
            continue

        try:
            executives = company["executives"]
            print(f"  🔍 Validating {len(executives)} executives...")

            # Enhanced validation
            validation_result = await validation_service.validate_executive_data(
                company_name, rank, executives
            )

            # Enhanced LLM validation
            print("  🤖 Enhanced LLM assessment...")
            llm_validation = await enhanced_llm_validation(
                llm_service, company_name, executives, validation_result
            )

            # Categorize confidence
            confidence = validation_result.confidence
            if confidence >= 0.8:
                enhanced_results["validation_summary"]["high_confidence"] += 1
                confidence_level = "HIGH"
            elif confidence >= 0.5:
                enhanced_results["validation_summary"]["medium_confidence"] += 1
                confidence_level = "MEDIUM"
            else:
                enhanced_results["validation_summary"]["low_confidence"] += 1
                confidence_level = "LOW"

            enhanced_results["validation_summary"]["total_issues"] += len(
                validation_result.issues
            )
            enhanced_results["validation_summary"]["total_suggestions"] += len(
                validation_result.suggestions
            )

            print(
                f"  ✅ Validation complete - Confidence: {confidence:.2f} ({confidence_level})"
            )
            print(f"     ⚠️ Issues: {len(validation_result.issues)}")
            print(f"     💡 Suggestions: {len(validation_result.suggestions)}")

            # Show key issues
            if validation_result.issues:
                print("     🔍 Key Issues:")
                for issue in validation_result.issues[:2]:
                    print(f"       • {issue}")

            enhanced_results["companies"].append(
                {
                    **company,
                    "validation": {
                        "confidence": validation_result.confidence,
                        "confidence_level": confidence_level,
                        "is_valid": validation_result.is_valid,
                        "issues": validation_result.issues,
                        "suggestions": validation_result.suggestions,
                        "web_search_performed": bool(
                            validation_result.web_search_results
                        ),
                    },
                    "enhanced_llm_validation": llm_validation,
                }
            )
            enhanced_results["successful_extractions"] += 1

        except Exception as e:
            logger.error(f"Validation error for {company_name}: {e}")
            print(f"  ❌ Validation error: {str(e)}")
            enhanced_results["companies"].append(
                {
                    **company,
                    "validation": {"error": str(e)},
                    "enhanced_llm_validation": None,
                }
            )
            enhanced_results["failed_extractions"] += 1

    # Save enhanced results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tests/results/enhanced_validated_results_{timestamp}.json"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(enhanced_results, f, indent=2)

    # Print comprehensive summary
    print_validation_summary(enhanced_results, output_file)


async def enhanced_llm_validation(
    llm_service: LLMService,
    company_name: str,
    executives: List[Dict],
    validation_result,
) -> Dict:
    """Enhanced LLM validation with validation context"""
    try:
        prompt = f"""
        Analyze executive compensation data for {company_name} with validation context:
        
        EXECUTIVE DATA:
        {json.dumps(executives, indent=2)}
        
        VALIDATION RESULTS:
        - Confidence: {validation_result.confidence:.2f}
        - Issues Found: {len(validation_result.issues)}
        - Key Issues: {validation_result.issues[:3]}
        - Suggestions: {validation_result.suggestions[:3]}
        
        Please provide:
        1. Overall data quality assessment (0-1 score)
        2. Authenticity analysis (are these real executives?)
        3. Compensation reasonableness for company size/industry
        4. Specific recommendations for data improvement
        5. Confidence in using this data for analysis
        
        Format as structured analysis with clear scores and recommendations.
        """

        response = await llm_service._make_llm_request(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            enable_web_search=True,
        )

        return {
            "llm_assessment": response,
            "timestamp": datetime.now().isoformat(),
            "validation_context_included": True,
        }

    except Exception as e:
        logger.error(f"Enhanced LLM validation error: {e}")
        return {"error": str(e)}


def print_validation_summary(results: Dict, output_file: str):
    """Print comprehensive validation summary"""
    print("\n" + "=" * 60)
    print("🎯 ENHANCED VALIDATION SUMMARY")
    print("=" * 60)

    total = results["total_companies"]
    successful = results["successful_extractions"]
    failed = results["failed_extractions"]

    print(f"📊 **PROCESSING RESULTS:**")
    print(f"   Total Companies: {total}")
    print(f"   Successful Extractions: {successful}")
    print(f"   Failed Extractions: {failed}")
    print(f"   Success Rate: {successful/total*100:.1f}%")

    validation_summary = results["validation_summary"]
    print(f"\n🔍 **VALIDATION QUALITY:**")
    print(f"   High Confidence (≥80%): {validation_summary['high_confidence']}")
    print(f"   Medium Confidence (50-79%): {validation_summary['medium_confidence']}")
    print(f"   Low Confidence (<50%): {validation_summary['low_confidence']}")
    print(
        f"   Average Issues per Company: {validation_summary['total_issues']/successful:.1f}"
    )
    print(
        f"   Average Suggestions per Company: {validation_summary['total_suggestions']/successful:.1f}"
    )

    # Top issues analysis
    all_issues = []
    all_suggestions = []

    for company in results["companies"]:
        if company.get("validation") and "issues" in company["validation"]:
            all_issues.extend(company["validation"]["issues"])
        if company.get("validation") and "suggestions" in company["validation"]:
            all_suggestions.extend(company["validation"]["suggestions"])

    print(f"\n⚠️ **COMMON ISSUES IDENTIFIED:**")
    issue_counts = {}
    for issue in all_issues:
        key = issue.split(":")[0] if ":" in issue else issue[:50]
        issue_counts[key] = issue_counts.get(key, 0) + 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]:
        print(f"   • {issue}: {count} companies")

    print(f"\n💡 **COMMON SUGGESTIONS:**")
    suggestion_counts = {}
    for suggestion in all_suggestions:
        key = suggestion.split(":")[0] if ":" in suggestion else suggestion[:50]
        suggestion_counts[key] = suggestion_counts.get(key, 0) + 1

    for suggestion, count in sorted(
        suggestion_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]:
        print(f"   • {suggestion}: {count} companies")

    print(f"\n📈 **DATA QUALITY INSIGHTS:**")
    high_quality = validation_summary["high_confidence"]
    medium_quality = validation_summary["medium_confidence"]
    low_quality = validation_summary["low_confidence"]

    if high_quality > 0:
        print(
            f"   ✅ {high_quality} companies have high-quality data suitable for analysis"
        )
    if medium_quality > 0:
        print(f"   ⚠️ {medium_quality} companies need data verification before use")
    if low_quality > 0:
        print(f"   ❌ {low_quality} companies require significant data cleanup")

    print(f"\n💾 **OUTPUT:**")
    print(f"   Enhanced results saved: {output_file}")
    print(f"   Includes validation scores, issues, and LLM assessments")

    print(f"\n🚀 **NEXT STEPS:**")
    print(f"   1. Review high-confidence companies for immediate analysis")
    print(f"   2. Address common validation issues identified")
    print(f"   3. Implement suggested improvements for data quality")
    print(f"   4. Use validation scores to filter reliable data")

    print("\n🎯 Enhanced validation analysis complete!")


if __name__ == "__main__":
    asyncio.run(analyze_with_validation())
