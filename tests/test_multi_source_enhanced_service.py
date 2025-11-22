#!/usr/bin/env python3
"""
Test Multi-Source Enhanced Executive Compensation Service

This tests our comprehensive approach combining:
1. XBRL breakthrough discovery
2. Professional API services
3. AI-powered extraction capabilities
4. Fallback methods
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

from edgar_analyzer.services.multi_source_enhanced_service import MultiSourceEnhancedService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_multi_source_enhanced_service():
    """Test the Multi-Source Enhanced Service"""
    
    print("🚀 TESTING MULTI-SOURCE ENHANCED SERVICE")
    print("=" * 80)
    print("🎯 Combining XBRL breakthrough + Professional APIs + AI capabilities")
    print("📊 This should achieve 75%+ success rate for Fortune companies")
    
    # Initialize service
    service = MultiSourceEnhancedService(identity="test.user@example.com")
    
    # Test Fortune companies with different characteristics
    test_companies = [
        ("AAPL", "Apple Inc."),           # Known to have XBRL data
        ("MSFT", "Microsoft Corporation"), # Large tech company
        ("GOOGL", "Alphabet Inc."),       # Complex structure
        ("AMZN", "Amazon.com Inc."),      # E-commerce giant
        ("TSLA", "Tesla Inc."),           # Growth company
        ("NVDA", "NVIDIA Corporation"),   # AI/chip company
        ("META", "Meta Platforms Inc."),  # Social media
        ("BRK.A", "Berkshire Hathaway Inc.") # Conglomerate
    ]
    
    results = []
    
    for symbol, company_name in test_companies:
        print(f"\n📊 Testing {company_name} ({symbol})")
        print("-" * 60)
        
        try:
            # Extract using multi-source approach
            result = await service.extract_executive_compensation(symbol, company_name)
            
            if result['success']:
                print(f"   ✅ MULTI-SOURCE SUCCESS!")
                print(f"   📄 Data Source: {result.get('data_source', 'N/A')}")
                print(f"   🔧 Method: {result.get('extraction_method', 'N/A')}")
                print(f"   🎯 Quality Score: {result.get('quality_score', 0):.2f}")
                
                if result.get('filing_date'):
                    print(f"   📅 Filing Date: {result.get('filing_date', 'N/A')}")
                
                executives = result.get('executives', [])
                print(f"   👥 Executives Found: {len(executives)}")
                
                total_compensation = 0
                for i, exec_data in enumerate(executives, 1):
                    name = exec_data.get('name', 'Unknown')
                    title = exec_data.get('title', 'Unknown')
                    total_comp = exec_data.get('total_compensation', 0)
                    source = exec_data.get('data_source', 'unknown')
                    
                    print(f"      {i}. {name}")
                    print(f"         Title: {title}")
                    print(f"         Total Compensation: ${total_comp:,}")
                    print(f"         Source: {source}")
                    
                    total_compensation += total_comp
                
                print(f"   💰 Total Executive Compensation: ${total_compensation:,}")
                
            else:
                print(f"   ❌ All methods failed: {result.get('reason', 'Unknown')}")
                
                # Show what was attempted
                attempts = result.get('attempts', [])
                if attempts:
                    print(f"   🔍 Attempted methods:")
                    for method, attempt_result in attempts:
                        status = "✅" if attempt_result.get('success') else "❌"
                        print(f"      {status} {method}: {attempt_result.get('reason', attempt_result.get('error', 'Unknown'))}")
                
                # Show available sources
                available = result.get('available_sources', {})
                print(f"   📊 Available sources:")
                for source, available_flag in available.items():
                    status = "✅" if available_flag else "❌"
                    print(f"      {status} {source}")
            
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

async def analyze_multi_source_results(results: List[Dict]):
    """Analyze the multi-source test results"""
    
    print("\n" + "=" * 80)
    print("🚀 MULTI-SOURCE ENHANCED SERVICE RESULTS")
    print("=" * 80)
    
    total_tests = len(results)
    successful_extractions = len([r for r in results if r.get('success')])
    failed_extractions = total_tests - successful_extractions
    
    print(f"📈 **MULTI-SOURCE RESULTS:**")
    print(f"   Total Companies Tested: {total_tests}")
    print(f"   ✅ Successful Extractions: {successful_extractions} ({successful_extractions/total_tests*100:.1f}%)")
    print(f"   ❌ Failed Extractions: {failed_extractions} ({failed_extractions/total_tests*100:.1f}%)")
    
    # Calculate improvement over baseline and XBRL-only
    baseline_success_rate = 0.25  # 25% (original system)
    xbrl_success_rate = 0.50     # 50% (XBRL breakthrough)
    multi_source_success_rate = successful_extractions / total_tests
    
    print(f"\n📊 **SUCCESS RATE COMPARISON:**")
    print(f"   Original System: {baseline_success_rate*100:.1f}%")
    print(f"   XBRL Breakthrough: {xbrl_success_rate*100:.1f}%")
    print(f"   Multi-Source Enhanced: {multi_source_success_rate*100:.1f}%")
    
    if multi_source_success_rate > xbrl_success_rate:
        improvement = (multi_source_success_rate - xbrl_success_rate) / xbrl_success_rate * 100
        print(f"   🚀 **ADDITIONAL IMPROVEMENT: +{improvement:.1f}% over XBRL alone**")
    
    total_improvement = (multi_source_success_rate - baseline_success_rate) / baseline_success_rate * 100
    print(f"   🎯 **TOTAL IMPROVEMENT: +{total_improvement:.1f}% over original system**")
    
    # Analyze data sources used
    successful_results = [r for r in results if r.get('success')]
    if successful_results:
        print(f"\n✅ **SUCCESSFUL EXTRACTIONS BY SOURCE:**")
        
        source_counts = {}
        method_counts = {}
        total_executives = 0
        total_compensation = 0
        
        for result in successful_results:
            source = result.get('data_source', 'unknown')
            method = result.get('extraction_method', 'unknown')
            
            source_counts[source] = source_counts.get(source, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
            
            executives = result.get('executives', [])
            total_executives += len(executives)
            
            company_total = sum(exec_data.get('total_compensation', 0) for exec_data in executives)
            total_compensation += company_total
        
        print(f"   📊 **DATA SOURCES:**")
        for source, count in source_counts.items():
            print(f"      • {source}: {count} companies ({count/len(successful_results)*100:.1f}%)")
        
        print(f"   🔧 **EXTRACTION METHODS:**")
        for method, count in method_counts.items():
            print(f"      • {method}: {count} companies ({count/len(successful_results)*100:.1f}%)")
        
        print(f"\n💰 **AGGREGATE STATISTICS:**")
        print(f"   Total Executives Extracted: {total_executives}")
        print(f"   Average Executives per Company: {total_executives/len(successful_results):.1f}")
        print(f"   Total Executive Compensation: ${total_compensation/1_000_000_000:.1f}B")
        print(f"   Average Company Executive Pay: ${total_compensation/len(successful_results)/1_000_000:.1f}M")
    
    # Analyze failure patterns
    failed_results = [r for r in results if not r.get('success')]
    if failed_results:
        print(f"\n❌ **FAILURE ANALYSIS:**")
        
        failure_reasons = {}
        for result in failed_results:
            reason = result.get('reason', 'unknown')
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        print(f"   📊 **FAILURE REASONS:**")
        for reason, count in failure_reasons.items():
            print(f"      • {reason}: {count} companies")
        
        # Analyze what sources were attempted
        print(f"   🔍 **ATTEMPTED METHODS (for failed extractions):**")
        all_attempts = {}
        for result in failed_results:
            attempts = result.get('attempts', [])
            for method, attempt_result in attempts:
                if method not in all_attempts:
                    all_attempts[method] = {'total': 0, 'failed': 0}
                all_attempts[method]['total'] += 1
                if not attempt_result.get('success'):
                    all_attempts[method]['failed'] += 1
        
        for method, stats in all_attempts.items():
            failure_rate = stats['failed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"      • {method}: {stats['failed']}/{stats['total']} failed ({failure_rate:.1f}%)")
    
    # Overall assessment
    print(f"\n🎯 **MULTI-SOURCE SERVICE ASSESSMENT:**")
    if multi_source_success_rate >= 0.75:
        print(f"   🏆 **EXCELLENT**: 75%+ success rate achieved!")
        print(f"   🚀 **READY FOR PRODUCTION**: Professional-grade performance")
        print(f"   💎 **BUSINESS VALUE**: Suitable for Fortune 500+ analysis")
    elif multi_source_success_rate >= 0.60:
        print(f"   ✅ **GOOD**: 60%+ success rate achieved")
        print(f"   🔧 **READY FOR DEPLOYMENT**: With minor refinements")
        print(f"   📊 **SIGNIFICANT IMPROVEMENT**: Major upgrade over baseline")
    elif multi_source_success_rate >= 0.40:
        print(f"   🔧 **MODERATE**: 40%+ success rate achieved")
        print(f"   📈 **IMPROVEMENT CONFIRMED**: Better than baseline")
        print(f"   🎯 **NEEDS ENHANCEMENT**: Add more data sources")
    else:
        print(f"   ⚠️ **NEEDS WORK**: Below 40% success rate")
        print(f"   🔍 **INVESTIGATE**: Check API configurations and methods")
    
    return {
        'total_tests': total_tests,
        'successful_extractions': successful_extractions,
        'success_rate': multi_source_success_rate,
        'improvement_over_baseline': total_improvement,
        'improvement_over_xbrl': improvement if multi_source_success_rate > xbrl_success_rate else 0,
        'source_distribution': source_counts if successful_results else {},
        'method_distribution': method_counts if successful_results else {},
        'total_executives': total_executives if successful_results else 0,
        'total_compensation': total_compensation if successful_results else 0
    }

async def main():
    """Main test function"""
    
    # Run multi-source tests
    results = await test_multi_source_enhanced_service()
    
    # Analyze results
    analysis = await analyze_multi_source_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"tests/results/multi_source_enhanced_test_{timestamp}.json"
    
    os.makedirs("tests/results", exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'test_results': results,
            'analysis': analysis,
            'research_findings': {
                'sec_api_professional_service': True,
                'fmp_api_service': True,
                'ai_llm_extraction_capability': True,
                'xbrl_breakthrough_foundation': True,
                'multi_source_approach': True
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Next steps based on results
    print(f"\n🎯 NEXT STEPS:")
    if analysis['success_rate'] >= 0.75:
        print("🏆 1. EXCELLENCE ACHIEVED - Deploy to production")
        print("📊 2. Scale to Fortune 500+ analysis")
        print("💎 3. This is professional-grade business intelligence!")
    elif analysis['success_rate'] >= 0.60:
        print("✅ 1. GOOD PERFORMANCE - Ready for deployment")
        print("🔧 2. Configure professional API keys for full capability")
        print("📈 3. Monitor and optimize data source performance")
    else:
        print("🔧 1. Configure API keys for SEC-API.io and FMP")
        print("🤖 2. Implement AI-powered extraction for complex cases")
        print("📊 3. Analyze failure patterns and enhance methods")

if __name__ == "__main__":
    asyncio.run(main())
