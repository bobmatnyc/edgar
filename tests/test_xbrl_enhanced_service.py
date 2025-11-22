#!/usr/bin/env python3
"""
Test XBRL Enhanced Executive Compensation Extraction Service
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from edgar_analyzer.services.xbrl_enhanced_extraction_service import XBRLEnhancedExtractionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_xbrl_enhanced_service():
    """Test the XBRL Enhanced Extraction Service"""
    
    print("🚀 TESTING XBRL ENHANCED EXTRACTION SERVICE")
    print("=" * 70)
    print("🎯 Testing new XBRL-enhanced approach for executive compensation")
    print("📊 Using edgartools with enhanced text parsing")
    
    # Initialize service
    service = XBRLEnhancedExtractionService(identity="test.user@example.com")
    
    # Test companies (Fortune 1-8)
    test_companies = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corporation"),
        ("GOOGL", "Alphabet Inc."),
        ("AMZN", "Amazon.com Inc.")
    ]
    
    results = []
    
    for symbol, company_name in test_companies:
        print(f"\n📊 Testing {company_name} ({symbol})")
        print("-" * 50)
        
        try:
            # Extract executive compensation
            result = await service.extract_executive_compensation(symbol, company_name)
            
            if result['success']:
                print(f"   ✅ Extraction successful")
                print(f"   📄 Filing: {result.get('accession_number', 'N/A')}")
                print(f"   📅 Date: {result.get('filing_date', 'N/A')}")
                print(f"   🔧 Method: {result.get('extraction_method', 'N/A')}")
                print(f"   📊 Data Source: {result.get('data_source', 'N/A')}")
                print(f"   🎯 Quality Score: {result.get('quality_score', 0):.2f}")
                
                executives = result.get('executives', [])
                print(f"   👥 Executives Found: {len(executives)}")
                
                for i, exec_data in enumerate(executives[:3], 1):  # Show first 3
                    name = exec_data.get('name', 'Unknown')
                    title = exec_data.get('title', 'Unknown')
                    total_comp = exec_data.get('total_compensation', 0)
                    print(f"      {i}. {name} - {title}: ${total_comp:,}")
                
            else:
                print(f"   ❌ Extraction failed: {result.get('reason', 'Unknown')}")
                if result.get('error'):
                    print(f"   🔍 Error: {result['error']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"   ❌ Exception during extraction: {e}")
            results.append({
                'success': False,
                'symbol': symbol,
                'company_name': company_name,
                'reason': 'exception',
                'error': str(e)
            })
    
    return results

async def analyze_results(results: List[Dict]):
    """Analyze the test results"""
    
    print("\n" + "=" * 70)
    print("📊 XBRL ENHANCED SERVICE TEST RESULTS")
    print("=" * 70)
    
    total_tests = len(results)
    successful_extractions = len([r for r in results if r.get('success')])
    failed_extractions = total_tests - successful_extractions
    
    print(f"📈 **EXTRACTION RESULTS:**")
    print(f"   Total Companies Tested: {total_tests}")
    print(f"   ✅ Successful Extractions: {successful_extractions} ({successful_extractions/total_tests*100:.1f}%)")
    print(f"   ❌ Failed Extractions: {failed_extractions} ({failed_extractions/total_tests*100:.1f}%)")
    
    # Analyze failure reasons
    if failed_extractions > 0:
        print(f"\n🔍 **FAILURE ANALYSIS:**")
        failure_reasons = {}
        for result in results:
            if not result.get('success'):
                reason = result.get('reason', 'unknown')
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        for reason, count in failure_reasons.items():
            print(f"   {reason}: {count} companies")
    
    # Analyze successful extractions
    successful_results = [r for r in results if r.get('success')]
    total_executives = 0
    avg_quality = 0

    if successful_results:
        print(f"\n✅ **SUCCESSFUL EXTRACTIONS:**")

        total_quality_score = 0
        data_sources = {}
        extraction_methods = {}

        for result in successful_results:
            executives = result.get('executives', [])
            total_executives += len(executives)
            total_quality_score += result.get('quality_score', 0)

            source = result.get('data_source', 'unknown')
            data_sources[source] = data_sources.get(source, 0) + 1

            method = result.get('extraction_method', 'unknown')
            extraction_methods[method] = extraction_methods.get(method, 0) + 1

        avg_quality = total_quality_score / len(successful_results)
        avg_executives = total_executives / len(successful_results)

        print(f"   Total Executives Found: {total_executives}")
        print(f"   Average Executives per Company: {avg_executives:.1f}")
        print(f"   Average Quality Score: {avg_quality:.2f}")

        print(f"\n📊 **DATA SOURCES:**")
        for source, count in data_sources.items():
            print(f"   {source}: {count} companies")

        print(f"\n🔧 **EXTRACTION METHODS:**")
        for method, count in extraction_methods.items():
            print(f"   {method}: {count} companies")
    else:
        print(f"\n❌ **NO SUCCESSFUL EXTRACTIONS**")
        print(f"   Need to improve text parsing algorithms")
    
    # Comparison with current system
    print(f"\n📈 **COMPARISON WITH CURRENT SYSTEM:**")
    print(f"   Current Fortune 1-8 Success Rate: ~25% (2/8 companies)")
    print(f"   XBRL Enhanced Success Rate: {successful_extractions/total_tests*100:.1f}% ({successful_extractions}/{total_tests} companies)")
    
    if successful_extractions/total_tests > 0.25:
        improvement = (successful_extractions/total_tests - 0.25) / 0.25 * 100
        print(f"   🚀 **IMPROVEMENT: +{improvement:.1f}% better success rate**")
    
    return {
        'total_tests': total_tests,
        'successful_extractions': successful_extractions,
        'success_rate': successful_extractions/total_tests,
        'average_quality_score': avg_quality if successful_results else 0,
        'total_executives': total_executives
    }

async def main():
    """Main test function"""
    
    # Run tests
    results = await test_xbrl_enhanced_service()
    
    # Analyze results
    analysis = await analyze_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"tests/results/xbrl_enhanced_service_test_{timestamp}.json"
    
    os.makedirs("tests/results", exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'test_results': results,
            'analysis': analysis
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Next steps
    print(f"\n🎯 NEXT STEPS:")
    if analysis['success_rate'] > 0.5:
        print("✅ 1. XBRL Enhanced Service shows promise - integrate into main pipeline")
        print("🔧 2. Enhance text parsing algorithms for better executive extraction")
        print("📊 3. Implement XBRL structured data parsing when available")
        print("🚀 4. Test with full Fortune 100 dataset")
    else:
        print("🔧 1. Improve text parsing algorithms")
        print("📊 2. Add more sophisticated executive compensation patterns")
        print("🔍 3. Debug extraction failures and enhance error handling")
        print("🚀 4. Consider hybrid approach with multiple data sources")

if __name__ == "__main__":
    asyncio.run(main())
