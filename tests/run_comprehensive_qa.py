#!/usr/bin/env python3
"""
Comprehensive QA of existing Fortune 50 results
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

from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.services.qa_controller import ComprehensiveQAController

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_comprehensive_qa():
    """Run comprehensive QA on existing results"""

    print("🔍 Comprehensive QA Analysis")
    print("=" * 50)

    # Load existing results
    results_file = "results/top_100_enhanced_results_20251121_180216.json"

    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return

    with open(results_file, "r") as f:
        original_results = json.load(f)

    print(f"📊 Loaded results for {original_results['total_companies']} companies")

    # Initialize QA controller
    llm_service = LLMService()
    qa_controller = ComprehensiveQAController(
        llm_service=llm_service, web_search_enabled=True
    )

    # QA results
    qa_results = {
        "timestamp": datetime.now().isoformat(),
        "original_file": results_file,
        "total_companies": original_results["total_companies"],
        "qa_summary": {
            "high_quality": 0,
            "medium_quality": 0,
            "low_quality": 0,
            "rejected": 0,
            "total_issues": 0,
            "total_corrections": 0,
        },
        "companies": [],
    }

    print("\n🔍 Running QA on each company...")

    for i, company in enumerate(original_results["companies"]):
        company_name = company["name"]
        rank = company["rank"]

        print(f"\n🏢 [{rank}/{original_results['total_companies']}] {company_name}")

        if not company["success"] or not company["executives"]:
            print("  ⚠️ No executives data - marking as rejected")
            qa_results["companies"].append(
                {
                    **company,
                    "qa_result": {
                        "is_valid": False,
                        "confidence_score": 0.0,
                        "issues": ["No executive data"],
                        "corrections": {},
                        "quality_level": "REJECTED",
                    },
                }
            )
            qa_results["qa_summary"]["rejected"] += 1
            continue

        try:
            print(f"  🔍 QA analysis of {len(company['executives'])} executives...")

            # Run comprehensive QA
            qa_result = await qa_controller.qa_executive_data(company)

            # Determine quality level
            confidence = qa_result.confidence_score
            if confidence >= 0.8:
                quality_level = "HIGH"
                qa_results["qa_summary"]["high_quality"] += 1
            elif confidence >= 0.6:
                quality_level = "MEDIUM"
                qa_results["qa_summary"]["medium_quality"] += 1
            elif confidence >= 0.3:
                quality_level = "LOW"
                qa_results["qa_summary"]["low_quality"] += 1
            else:
                quality_level = "REJECTED"
                qa_results["qa_summary"]["rejected"] += 1

            qa_results["qa_summary"]["total_issues"] += len(qa_result.issues)
            qa_results["qa_summary"]["total_corrections"] += len(qa_result.corrections)

            print(
                f"  ✅ QA complete - Quality: {quality_level} (Confidence: {confidence:.2f})"
            )
            print(f"     ⚠️ Issues: {len(qa_result.issues)}")
            print(f"     🔧 Corrections: {len(qa_result.corrections)}")

            # Show key issues
            if qa_result.issues:
                print("     🔍 Key Issues:")
                for issue in qa_result.issues[:3]:
                    print(f"       • {issue}")

            # Add to results
            qa_results["companies"].append(
                {
                    **company,
                    "qa_result": {
                        "is_valid": qa_result.is_valid,
                        "confidence_score": qa_result.confidence_score,
                        "issues": qa_result.issues,
                        "corrections": qa_result.corrections,
                        "quality_level": quality_level,
                        "cleaned_data": qa_result.cleaned_data,
                    },
                }
            )

        except Exception as e:
            logger.error(f"QA error for {company_name}: {e}")
            print(f"  ❌ QA error: {str(e)}")
            qa_results["companies"].append(
                {
                    **company,
                    "qa_result": {
                        "is_valid": False,
                        "confidence_score": 0.0,
                        "issues": [f"QA failed: {str(e)}"],
                        "corrections": {},
                        "quality_level": "REJECTED",
                    },
                }
            )
            qa_results["qa_summary"]["rejected"] += 1

    # Save QA results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tests/results/comprehensive_qa_results_{timestamp}.json"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(qa_results, f, indent=2)

    # Create cleaned dataset
    cleaned_file = f"tests/results/cleaned_executive_data_{timestamp}.json"
    cleaned_data = create_cleaned_dataset(qa_results)

    with open(cleaned_file, "w") as f:
        json.dump(cleaned_data, f, indent=2)

    # Print comprehensive summary
    print_qa_summary(qa_results, output_file, cleaned_file)


def create_cleaned_dataset(qa_results: Dict) -> Dict:
    """Create cleaned dataset with only high-quality data"""
    cleaned_companies = []

    for company in qa_results["companies"]:
        qa_result = company.get("qa_result", {})

        if qa_result.get("quality_level") in ["HIGH", "MEDIUM"] and qa_result.get(
            "cleaned_data"
        ):
            cleaned_companies.append(qa_result["cleaned_data"])

    return {
        "timestamp": datetime.now().isoformat(),
        "source": "comprehensive_qa_cleaning",
        "total_companies": len(cleaned_companies),
        "quality_filter": "HIGH and MEDIUM quality only",
        "companies": cleaned_companies,
    }


def print_qa_summary(qa_results: Dict, output_file: str, cleaned_file: str):
    """Print comprehensive QA summary"""
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE QA SUMMARY")
    print("=" * 60)

    total = qa_results["total_companies"]
    summary = qa_results["qa_summary"]

    print(f"📊 **QA RESULTS:**")
    print(f"   Total Companies Analyzed: {total}")
    print(f"   High Quality (≥80%): {summary['high_quality']}")
    print(f"   Medium Quality (60-79%): {summary['medium_quality']}")
    print(f"   Low Quality (30-59%): {summary['low_quality']}")
    print(f"   Rejected (<30%): {summary['rejected']}")

    usable_companies = summary["high_quality"] + summary["medium_quality"]
    print(
        f"   Usable for Analysis: {usable_companies} ({usable_companies/total*100:.1f}%)"
    )

    print(f"\n🔍 **ISSUE ANALYSIS:**")
    print(f"   Total Issues Identified: {summary['total_issues']}")
    print(f"   Total Corrections Applied: {summary['total_corrections']}")
    print(f"   Average Issues per Company: {summary['total_issues']/total:.1f}")

    # Analyze common issues
    all_issues = []
    for company in qa_results["companies"]:
        qa_result = company.get("qa_result", {})
        all_issues.extend(qa_result.get("issues", []))

    print(f"\n⚠️ **MOST COMMON ISSUES:**")
    issue_counts = {}
    for issue in all_issues:
        # Group similar issues
        if "invalid" in issue.lower():
            key = "Invalid executive names"
        elif "artificial" in issue.lower():
            key = "Artificial compensation patterns"
        elif "not found" in issue.lower():
            key = "Executive not found at company"
        elif "missing" in issue.lower():
            key = "Missing data fields"
        elif "unusual" in issue.lower():
            key = "Unusual compensation amounts"
        else:
            key = issue.split(":")[0] if ":" in issue else issue[:50]

        issue_counts[key] = issue_counts.get(key, 0) + 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]:
        print(f"   • {issue}: {count} occurrences")

    print(f"\n📈 **DATA QUALITY INSIGHTS:**")
    high_quality = summary["high_quality"]
    medium_quality = summary["medium_quality"]
    low_quality = summary["low_quality"]
    rejected = summary["rejected"]

    if high_quality > 0:
        print(f"   ✅ {high_quality} companies have excellent data quality")
    if medium_quality > 0:
        print(f"   ⚠️ {medium_quality} companies have good data with minor issues")
    if low_quality > 0:
        print(f"   🔧 {low_quality} companies need significant data cleanup")
    if rejected > 0:
        print(f"   ❌ {rejected} companies have unusable data")

    print(f"\n💾 **OUTPUT FILES:**")
    print(f"   QA Analysis: {output_file}")
    print(f"   Cleaned Dataset: {cleaned_file}")
    print(f"   Ready for target document generation")

    print(f"\n🎯 **NEXT STEPS:**")
    print(f"   1. Use cleaned dataset for final report generation")
    print(f"   2. Address common data quality issues in extraction")
    print(f"   3. Generate target document format matching reference")
    print(f"   4. Implement data validation in production pipeline")

    print("\n🔍 Comprehensive QA analysis complete!")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_qa())
