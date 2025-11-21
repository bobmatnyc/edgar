#!/usr/bin/env python3
"""
Run LLM-enhanced executive compensation extraction on top 100 Fortune 500 companies
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.edgar_api_service import EdgarApiService
from edgar_analyzer.services.company_service import CompanyService
from edgar_analyzer.services.cache_service import CacheService
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.config.settings import ConfigService

async def run_top_100_enhanced():
    """Run enhanced extraction on top 100 companies with LLM validation"""
    
    print("🚀 Starting LLM-Enhanced Executive Compensation Analysis")
    print("=" * 70)
    
    # Initialize services
    config = ConfigService()
    cache_service = CacheService(config)
    edgar_api = EdgarApiService(config, cache_service)
    company_service = CompanyService(config, edgar_api, cache_service)
    
    try:
        llm_service = LLMService()
        print("✅ Grok 4.1 Fast LLM service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LLM service: {e}")
        return
    
    data_extraction = DataExtractionService(edgar_api, company_service, cache_service, llm_service)
    
    # Load Fortune 500 companies
    companies_file = "data/companies/fortune_500_complete.json"
    try:
        with open(companies_file, 'r') as f:
            all_companies = json.load(f)
        print(f"📊 Loaded {len(all_companies)} companies from Fortune 500 list")
    except Exception as e:
        print(f"❌ Failed to load companies: {e}")
        return
    
    # Take top 100 companies
    top_100 = all_companies[:100]
    print(f"🎯 Processing top {len(top_100)} companies")
    
    # Results tracking
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_companies': len(top_100),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'llm_validations': 0,
        'authentic_data_count': 0,
        'fake_data_detected': 0,
        'quality_scores': [],
        'companies': []
    }
    
    year = 2024  # Most recent year
    
    print(f"\n🔍 Starting extraction for year {year}...")
    print("-" * 50)
    
    for i, company in enumerate(top_100, 1):
        company_name = company.get('name', 'Unknown')
        cik = company.get('cik', '')
        
        print(f"\n[{i:3d}/100] {company_name} (CIK: {cik})")
        
        company_result = {
            'rank': i,
            'name': company_name,
            'cik': cik,
            'success': False,
            'executives': [],
            'llm_validation': None,
            'error': None
        }
        
        try:
            # Extract executive compensation
            compensations = await data_extraction.extract_executive_compensation(cik, year)
            
            if compensations:
                results['successful_extractions'] += 1
                company_result['success'] = True
                
                # Convert to serializable format
                for comp in compensations:
                    exec_data = {
                        'name': comp.executive_name,
                        'title': comp.title,
                        'total_compensation': float(comp.total_compensation),
                        'salary': float(comp.salary) if comp.salary else 0,
                        'bonus': float(comp.bonus) if comp.bonus else 0,
                        'stock_awards': float(comp.stock_awards) if comp.stock_awards else 0,
                        'option_awards': float(comp.option_awards) if comp.option_awards else 0
                    }
                    company_result['executives'].append(exec_data)
                
                print(f"  ✅ Found {len(compensations)} executives")
                for comp in compensations[:3]:  # Show first 3
                    print(f"     • {comp.executive_name} ({comp.title}) - ${comp.total_compensation:,}")
                
                # Note: LLM validation results are already logged during extraction
                # We can track the validation results from the logs
                results['llm_validations'] += 1
                
            else:
                results['failed_extractions'] += 1
                print(f"  ❌ No compensation data found")
                
        except Exception as e:
            results['failed_extractions'] += 1
            company_result['error'] = str(e)
            print(f"  ❌ Error: {str(e)[:100]}...")
        
        results['companies'].append(company_result)
        
        # Progress update every 10 companies
        if i % 10 == 0:
            success_rate = (results['successful_extractions'] / i) * 100
            print(f"\n📈 Progress: {i}/100 companies processed")
            print(f"   Success rate: {success_rate:.1f}%")
            print(f"   Successful: {results['successful_extractions']}")
            print(f"   Failed: {results['failed_extractions']}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 LLM-Enhanced Analysis Complete!")
    print("=" * 70)
    
    success_rate = (results['successful_extractions'] / results['total_companies']) * 100
    print(f"📊 Final Results:")
    print(f"   Total Companies: {results['total_companies']}")
    print(f"   Successful Extractions: {results['successful_extractions']}")
    print(f"   Failed Extractions: {results['failed_extractions']}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   LLM Validations: {results['llm_validations']}")
    
    # Save results
    output_file = f"results/top_100_enhanced_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("results", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show some example successful extractions
    successful_companies = [c for c in results['companies'] if c['success']]
    if successful_companies:
        print(f"\n🌟 Sample Successful Extractions:")
        for company in successful_companies[:5]:  # Show first 5
            print(f"\n   {company['name']}:")
            for exec in company['executives'][:2]:  # Show top 2 executives
                print(f"     • {exec['name']} ({exec['title']}) - ${exec['total_compensation']:,.0f}")

if __name__ == "__main__":
    asyncio.run(run_top_100_enhanced())
