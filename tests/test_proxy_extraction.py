#!/usr/bin/env python3
"""
Test the improved proxy filing extraction logic
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
from edgar_analyzer.config.settings import ConfigService

async def test_proxy_extraction():
    """Test proxy extraction with a real company"""

    # Initialize services with proper dependencies
    config = ConfigService()
    cache_service = CacheService(config)
    edgar_api = EdgarApiService(config, cache_service)
    company_service = CompanyService(config, edgar_api, cache_service)
    data_extraction = DataExtractionService(edgar_api, company_service, cache_service)
    
    # Test with Apple (CIK: 0000320193)
    cik = "0000320193"
    year = 2024
    
    print(f"Testing proxy extraction for CIK {cik}, year {year}")
    
    try:
        # Extract executive compensation
        compensations = await data_extraction.extract_executive_compensation(cik, year)
        
        print(f"\nFound {len(compensations)} executive compensations:")
        for comp in compensations:
            print(f"  - {comp.executive_name} ({comp.title}): ${comp.total_compensation:,}")
            
        # Check if we got real names (not fake ones)
        if compensations:
            first_exec = compensations[0]
            fake_name_indicators = [
                "James", "Michael", "Robert", "John", "David", "William", "Richard", "Thomas", 
                "Christopher", "Daniel", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth"
            ]
            
            first_name = first_exec.executive_name.split()[0] if first_exec.executive_name else ""
            if first_name in fake_name_indicators:
                print(f"\n⚠️  WARNING: Executive name '{first_exec.executive_name}' appears to be generated (fake)")
                print("This suggests the proxy extraction is still failing and falling back to placeholder data")
            else:
                print(f"\n✅ SUCCESS: Executive name '{first_exec.executive_name}' appears to be real")
                
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_proxy_extraction())
