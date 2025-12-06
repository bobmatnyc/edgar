#!/usr/bin/env python3
"""
Enhanced EDGAR analysis with web search validation and improved table parsing
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

from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.enhanced_table_parser import EnhancedTableParser
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.services.validation_service import EnhancedValidationService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EnhancedEdgarAnalyzer:
    """Enhanced EDGAR analyzer with validation and improved parsing"""

    def __init__(self):
        self.llm_service = LLMService()
        self.table_parser = EnhancedTableParser()
        self.data_extraction_service = DataExtractionService()

        # Create web search client using LLM service
        async def web_search_client(query, context=None):
            return await self.llm_service.web_search_request(query, context)

        self.validation_service = EnhancedValidationService(
            web_search_client=web_search_client, llm_client=self.llm_service
        )

    async def analyze_companies(self, companies: List[Dict], limit: int = 10) -> Dict:
        """Analyze companies with enhanced validation"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_companies": min(len(companies), limit),
            "successful_extractions": 0,
            "failed_extractions": 0,
            "companies": [],
        }

        print(f"🚀 Enhanced EDGAR Analysis Starting")
        print(f"📊 Processing {results['total_companies']} companies with validation")
        print("=" * 60)

        for i, company in enumerate(companies[:limit]):
            company_name = company["name"]
            cik = company["cik"]
            rank = i + 1

            print(
                f"\n🏢 [{rank}/{results['total_companies']}] {company_name} (CIK: {cik})"
            )

            try:
                # Step 1: Get proxy filing
                print("  📄 Fetching proxy filing...")
                proxy_content = await self._get_proxy_content(cik)

                if not proxy_content:
                    print("  ❌ No proxy content found")
                    results["companies"].append(
                        {
                            "rank": rank,
                            "name": company_name,
                            "cik": cik,
                            "success": False,
                            "error": "No proxy content found",
                            "executives": [],
                            "validation": None,
                        }
                    )
                    results["failed_extractions"] += 1
                    continue

                # Step 2: Enhanced table parsing
                print("  🔍 Parsing compensation tables...")
                executives = await self._extract_executives_enhanced(proxy_content)

                if not executives:
                    print("  ⚠️ No executives found")
                    results["companies"].append(
                        {
                            "rank": rank,
                            "name": company_name,
                            "cik": cik,
                            "success": False,
                            "error": "No executives extracted",
                            "executives": [],
                            "validation": None,
                        }
                    )
                    results["failed_extractions"] += 1
                    continue

                # Step 3: Enhanced validation with web search
                print(
                    f"  🔍 Validating {len(executives)} executives with web search..."
                )
                validation_result = (
                    await self.validation_service.validate_executive_data(
                        company_name, rank, executives
                    )
                )

                # Step 4: LLM quality assessment
                print("  🤖 LLM quality assessment...")
                llm_validation = await self._llm_validate_data(company_name, executives)

                print(f"  ✅ Success! Found {len(executives)} executives")
                print(
                    f"     🎯 Validation confidence: {validation_result.confidence:.2f}"
                )
                print(f"     ⚠️ Issues found: {len(validation_result.issues)}")

                results["companies"].append(
                    {
                        "rank": rank,
                        "name": company_name,
                        "cik": cik,
                        "success": True,
                        "executives": executives,
                        "validation": {
                            "confidence": validation_result.confidence,
                            "is_valid": validation_result.is_valid,
                            "issues": validation_result.issues,
                            "suggestions": validation_result.suggestions,
                            "web_search_results": validation_result.web_search_results,
                        },
                        "llm_validation": llm_validation,
                    }
                )
                results["successful_extractions"] += 1

                # Print validation summary
                if validation_result.issues:
                    print("     ⚠️ Validation Issues:")
                    for issue in validation_result.issues[:3]:  # Show first 3 issues
                        print(f"       • {issue}")

            except Exception as e:
                logger.error(f"Error processing {company_name}: {e}")
                print(f"  ❌ Error: {str(e)}")
                results["companies"].append(
                    {
                        "rank": rank,
                        "name": company_name,
                        "cik": cik,
                        "success": False,
                        "error": str(e),
                        "executives": [],
                        "validation": None,
                    }
                )
                results["failed_extractions"] += 1

        return results

    async def _get_proxy_content(self, cik: str) -> Optional[str]:
        """Get proxy filing content using data extraction service"""
        try:
            # Use the existing data extraction service to get proxy content
            result = await self.data_extraction_service.extract_executive_compensation(
                cik
            )
            if result and "proxy_content" in result:
                return result["proxy_content"]
        except Exception as e:
            logger.error(f"Error getting proxy content for CIK {cik}: {e}")
        return None

    async def _extract_executives_enhanced(self, html_content: str) -> List[Dict]:
        """Extract executives using enhanced table parsing"""
        try:
            # Find compensation tables
            tables = self.table_parser.find_compensation_tables(html_content)

            if not tables:
                return []

            # Use the highest confidence table
            best_table = tables[0]["table"]
            executives = self.table_parser.extract_compensation_data(best_table)

            return executives

        except Exception as e:
            logger.error(f"Error in enhanced extraction: {e}")
            return []

    async def _llm_validate_data(
        self, company_name: str, executives: List[Dict]
    ) -> Optional[Dict]:
        """LLM validation of extracted data"""
        try:
            prompt = f"""
            Analyze the following executive compensation data for {company_name}:
            
            {json.dumps(executives, indent=2)}
            
            Please assess:
            1. Data authenticity (are these real executives?)
            2. Compensation reasonableness
            3. Data consistency
            4. Any obvious errors or artificial patterns
            
            Provide a quality score (0-1) and detailed analysis.
            """

            response = await self.llm_service._make_llm_request(
                [{"role": "user", "content": prompt}], temperature=0.3
            )

            return {"llm_assessment": response, "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            return None


async def main():
    """Main execution function"""
    try:
        # Load Fortune 500 companies
        companies_file = "data/companies/fortune_500_complete.json"

        if not os.path.exists(companies_file):
            print(f"❌ Companies file not found: {companies_file}")
            return

        with open(companies_file, "r") as f:
            companies = json.load(f)

        print(f"📊 Loaded {len(companies)} companies")

        # Create analyzer
        analyzer = EnhancedEdgarAnalyzer()

        # Analyze first 10 companies with enhanced validation
        results = await analyzer.analyze_companies(companies, limit=10)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"tests/results/enhanced_validation_results_{timestamp}.json"

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("🎯 ENHANCED VALIDATION SUMMARY")
        print("=" * 60)
        print(f"📊 Total Companies: {results['total_companies']}")
        print(f"✅ Successful: {results['successful_extractions']}")
        print(f"❌ Failed: {results['failed_extractions']}")
        print(
            f"📈 Success Rate: {results['successful_extractions']/results['total_companies']*100:.1f}%"
        )
        print(f"💾 Results saved: {output_file}")

        # Print validation insights
        total_issues = 0
        high_confidence = 0

        for company in results["companies"]:
            if company["success"] and company["validation"]:
                total_issues += len(company["validation"]["issues"])
                if company["validation"]["confidence"] > 0.7:
                    high_confidence += 1

        if results["successful_extractions"] > 0:
            print(
                f"🔍 Average issues per company: {total_issues/results['successful_extractions']:.1f}"
            )
            print(
                f"🎯 High confidence results: {high_confidence}/{results['successful_extractions']}"
            )

        print("\n🚀 Enhanced validation complete!")

    except Exception as e:
        logger.error(f"Main execution error: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
