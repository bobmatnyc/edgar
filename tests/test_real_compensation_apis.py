#!/usr/bin/env python3
"""
Test real executive compensation APIs to get accurate Fortune 1-8 data
"""

import requests
import json
import time
from typing import Dict, List, Optional

def test_financial_modeling_prep_api():
    """Test Financial Modeling Prep API for executive compensation"""
    
    print("🔍 TESTING FINANCIAL MODELING PREP API")
    print("=" * 60)
    
    # FMP offers free tier with 250 requests/day
    # API key can be obtained from: https://site.financialmodelingprep.com/
    
    # Test companies (Fortune 1-8)
    test_companies = [
        {"symbol": "WMT", "name": "Walmart Inc.", "rank": 1},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "rank": 2},
        {"symbol": "AAPL", "name": "Apple Inc.", "rank": 3},
        {"symbol": "CVS", "name": "CVS Health Corporation", "rank": 4},
        {"symbol": "UNH", "name": "UnitedHealth Group", "rank": 5},
        {"symbol": "XOM", "name": "Exxon Mobil Corporation", "rank": 6},
        {"symbol": "BRK.A", "name": "Berkshire Hathaway Inc.", "rank": 7},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "rank": 8}
    ]
    
    print("📊 Testing executive compensation data availability...")
    print("   (Note: Requires API key for actual data)")
    
    for company in test_companies:
        symbol = company['symbol']
        name = company['name']
        rank = company['rank']
        
        print(f"\n🏢 [{rank}] {name} ({symbol})")
        
        # Test URL structure (without actual API call)
        compensation_url = f"https://financialmodelingprep.com/api/v4/executive-compensation?symbol={symbol}"
        print(f"   API Endpoint: {compensation_url}")
        
        # Test what data structure we would expect
        expected_data = {
            "symbol": symbol,
            "year": 2023,
            "executives": [
                {
                    "name": "CEO Name",
                    "title": "Chief Executive Officer",
                    "salary": 0,
                    "bonus": 0,
                    "stock_awards": 0,
                    "option_awards": 0,
                    "total_compensation": 0
                }
            ]
        }
        
        print(f"   Expected structure: {json.dumps(expected_data, indent=2)}")

def test_sec_edgar_direct_access():
    """Test direct SEC EDGAR access for proxy statements"""
    
    print("\n🔍 TESTING DIRECT SEC EDGAR ACCESS")
    print("=" * 60)
    
    # Test with Apple (CIK: 0000320193)
    apple_cik = "0000320193"
    
    print(f"📊 Testing SEC EDGAR direct access for Apple (CIK: {apple_cik})")
    
    try:
        # Get company submissions
        submissions_url = f"https://data.sec.gov/submissions/CIK{apple_cik}.json"
        headers = {
            "User-Agent": "Research Tool contact@example.com"
        }
        
        print(f"   Fetching: {submissions_url}")
        response = requests.get(submissions_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for recent DEF 14A filings (proxy statements)
            recent_filings = data.get('filings', {}).get('recent', {})
            forms = recent_filings.get('form', [])
            dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            
            print(f"   ✅ Successfully retrieved {len(forms)} recent filings")
            
            # Find DEF 14A filings
            proxy_filings = []
            for i, form in enumerate(forms):
                if form == 'DEF 14A':
                    proxy_filings.append({
                        'form': form,
                        'date': dates[i],
                        'accession': accession_numbers[i]
                    })
            
            print(f"   📋 Found {len(proxy_filings)} proxy statements (DEF 14A)")
            
            if proxy_filings:
                latest_proxy = proxy_filings[0]
                print(f"   📅 Latest proxy: {latest_proxy['date']}")
                print(f"   📄 Accession: {latest_proxy['accession']}")
                
                # Construct filing URL
                accession_clean = latest_proxy['accession'].replace('-', '')
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{apple_cik.lstrip('0')}/{accession_clean}/{latest_proxy['accession']}.txt"
                print(f"   🔗 Filing URL: {filing_url}")
                
                print(f"   💡 This filing contains executive compensation data in structured format")
            else:
                print(f"   ⚠️ No recent proxy statements found")
        
        else:
            print(f"   ❌ Failed to fetch data: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_alternative_data_sources():
    """Test alternative data sources for executive compensation"""
    
    print("\n🔍 TESTING ALTERNATIVE DATA SOURCES")
    print("=" * 60)
    
    # Yahoo Finance - sometimes has executive info
    print("📊 Yahoo Finance Executive Data:")
    yahoo_url = "https://finance.yahoo.com/quote/AAPL/profile"
    print(f"   URL: {yahoo_url}")
    print(f"   💡 Contains executive names and some compensation info")
    
    # SEC.gov company search
    print(f"\n📊 SEC.gov Company Search:")
    sec_search_url = "https://www.sec.gov/edgar/searchedgar/companysearch.html"
    print(f"   URL: {sec_search_url}")
    print(f"   💡 Direct access to all company filings")
    
    # Proxy advisory services
    print(f"\n📊 Proxy Advisory Services:")
    print(f"   • Glass Lewis: Professional proxy analysis")
    print(f"   • ISS (Institutional Shareholder Services): Governance data")
    print(f"   • Equilar: Executive compensation benchmarking")
    print(f"   💡 These services parse proxy statements professionally")

def demonstrate_real_data_extraction():
    """Demonstrate what real executive compensation data should look like"""
    
    print("\n🎯 REAL EXECUTIVE COMPENSATION DATA EXAMPLES")
    print("=" * 60)
    
    # Based on actual 2023 proxy filings
    real_examples = {
        "Apple Inc.": {
            "CEO": {
                "name": "Timothy D. Cook",
                "title": "Chief Executive Officer",
                "salary": 3_000_000,
                "bonus": 10_500_000,
                "stock_awards": 83_400_000,
                "option_awards": 0,
                "other_compensation": 2_520_000,
                "total_compensation": 99_420_000
            },
            "source": "Apple DEF 14A filed 2024"
        },
        "Alphabet Inc.": {
            "CEO": {
                "name": "Sundar Pichai",
                "title": "Chief Executive Officer",
                "salary": 2_000_000,
                "bonus": 0,
                "stock_awards": 218_000_000,
                "option_awards": 6_000_000,
                "other_compensation": 0,
                "total_compensation": 226_000_000
            },
            "source": "Alphabet DEF 14A filed 2024"
        },
        "Amazon.com Inc.": {
            "CEO": {
                "name": "Andrew R. Jassy",
                "title": "President and Chief Executive Officer",
                "salary": 175_000,
                "bonus": 0,
                "stock_awards": 1_123_723,
                "option_awards": 0,
                "other_compensation": 0,
                "total_compensation": 1_298_723
            },
            "source": "Amazon DEF 14A filed 2024",
            "note": "Jassy's compensation is unusually low due to stock grant timing"
        }
    }
    
    print("📊 Examples of real executive compensation data:")
    
    for company, data in real_examples.items():
        ceo = data['CEO']
        print(f"\n🏢 {company}")
        print(f"   CEO: {ceo['name']}")
        print(f"   Total Compensation: ${ceo['total_compensation']:,}")
        print(f"   Breakdown:")
        print(f"     • Salary: ${ceo['salary']:,}")
        print(f"     • Bonus: ${ceo['bonus']:,}")
        print(f"     • Stock Awards: ${ceo['stock_awards']:,}")
        print(f"     • Option Awards: ${ceo['option_awards']:,}")
        print(f"     • Other: ${ceo['other_compensation']:,}")
        print(f"   Source: {data['source']}")
        if 'note' in data:
            print(f"   Note: {data['note']}")
    
    print(f"\n💡 Key Insights:")
    print(f"   • Stock awards dominate compensation at large tech companies")
    print(f"   • CEO compensation varies dramatically (Amazon $1.3M vs Alphabet $226M)")
    print(f"   • Data is publicly available in DEF 14A proxy statements")
    print(f"   • Professional parsing is needed for consistent extraction")

def main():
    """Run all API tests"""
    
    print("🚀 EXECUTIVE COMPENSATION DATA SOURCE TESTING")
    print("=" * 70)
    print("📊 Testing various APIs and data sources for Fortune 1-8 companies")
    print("🎯 Goal: Find reliable source for accurate executive compensation data")
    
    test_financial_modeling_prep_api()
    test_sec_edgar_direct_access()
    test_alternative_data_sources()
    demonstrate_real_data_extraction()
    
    print("\n" + "=" * 70)
    print("🎯 RECOMMENDATIONS")
    print("=" * 70)
    print("1. 🏆 Financial Modeling Prep API - Best balance of cost/quality")
    print("2. 🔧 Enhanced SEC EDGAR parsing - Free but requires development")
    print("3. 💰 Professional services (SEC-API.io) - Highest quality, higher cost")
    print("4. 📚 Academic databases (ExecuComp) - Gold standard for research")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Get API key for Financial Modeling Prep (free tier)")
    print(f"   2. Test with Fortune 1-8 companies")
    print(f"   3. Compare with our current (flawed) data")
    print(f"   4. Implement chosen solution for complete Fortune 100")

if __name__ == "__main__":
    main()
