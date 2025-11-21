#!/usr/bin/env python3
"""
Test the LLM-enhanced proxy filing extraction logic
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.edgar_api_service import EdgarApiService
from edgar_analyzer.services.company_service import CompanyService
from edgar_analyzer.services.cache_service import CacheService
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.config.settings import ConfigService

async def test_llm_extraction():
    """Test LLM-enhanced proxy extraction with a real company"""
    
    # Initialize services with LLM support
    config = ConfigService()
    cache_service = CacheService(config)
    edgar_api = EdgarApiService(config, cache_service)
    company_service = CompanyService(config, edgar_api, cache_service)
    
    try:
        llm_service = LLMService()
        print("✅ LLM service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LLM service: {e}")
        print("Make sure OPENROUTER_API_KEY is set in .env.local")
        return
    
    data_extraction = DataExtractionService(edgar_api, company_service, cache_service, llm_service)
    
    # Test with Apple (CIK: 0000320193)
    cik = "0000320193"
    year = 2024
    
    print(f"Testing LLM-enhanced proxy extraction for CIK {cik}, year {year}")
    
    try:
        # Extract executive compensation with LLM enhancement
        compensations = await data_extraction.extract_executive_compensation(cik, year)
        
        print(f"\n🎯 Found {len(compensations)} executive compensations:")
        for i, comp in enumerate(compensations, 1):
            print(f"  {i}. {comp.executive_name} ({comp.title})")
            print(f"     Total Compensation: ${comp.total_compensation:,}")
            print(f"     Salary: ${comp.salary:,}")
            print(f"     Bonus: ${comp.bonus:,}")
            print(f"     Stock Awards: ${comp.stock_awards:,}")
            print(f"     Option Awards: ${comp.option_awards:,}")
            print()
            
        # Analyze the results
        if compensations:
            print("📊 Analysis:")
            
            # Check for known Apple executives
            known_apple_execs = ['Tim Cook', 'Luca Maestri', 'Katherine Adams', 'Jeff Williams']
            found_known_execs = []
            
            for comp in compensations:
                for known_exec in known_apple_execs:
                    if known_exec.lower() in comp.executive_name.lower():
                        found_known_execs.append(known_exec)
            
            if found_known_execs:
                print(f"✅ Found known Apple executives: {', '.join(found_known_execs)}")
            else:
                print("⚠️  No known Apple executives found - may need to check extraction logic")
            
            # Check compensation reasonableness
            total_comps = [float(comp.total_compensation) for comp in compensations]
            avg_comp = sum(total_comps) / len(total_comps)
            max_comp = max(total_comps)
            
            print(f"💰 Compensation Analysis:")
            print(f"   Average: ${avg_comp:,.0f}")
            print(f"   Highest: ${max_comp:,.0f}")
            
            if max_comp > 10_000_000:  # $10M+
                print("✅ CEO-level compensation detected (reasonable for Apple)")
            else:
                print("⚠️  Compensation levels seem low for Apple executives")
                
        else:
            print("❌ No compensation data extracted")
            
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_extraction())
