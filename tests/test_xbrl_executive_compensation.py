#!/usr/bin/env python3
"""
Test XBRL-based executive compensation extraction using edgartools
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_edgartools_installation():
    """Test if edgartools can be installed and used"""
    
    print("🔧 TESTING EDGARTOOLS INSTALLATION")
    print("=" * 60)
    
    try:
        # Try to import edgartools
        import edgar
        print("✅ edgartools imported successfully")
        
        # Set identity (required by SEC)
        edgar.set_identity("test.user@example.com")
        print("✅ SEC identity set")
        
        # Test basic functionality
        company = edgar.Company("AAPL")
        print(f"✅ Company object created: {company.name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ edgartools not installed: {e}")
        print("💡 Install with: pip install edgartools")
        return False
    except Exception as e:
        print(f"❌ Error testing edgartools: {e}")
        return False

async def test_xbrl_proxy_extraction():
    """Test XBRL extraction from proxy statements"""
    
    print("\n🔍 TESTING XBRL PROXY EXTRACTION")
    print("=" * 60)
    
    try:
        import edgar
        edgar.set_identity("test.user@example.com")
        
        # Test with Fortune 1-8 companies
        test_companies = [
            ("AAPL", "Apple Inc."),
            ("MSFT", "Microsoft Corporation"),
            ("GOOGL", "Alphabet Inc."),
            ("AMZN", "Amazon.com Inc.")
        ]
        
        results = []
        
        for symbol, name in test_companies:
            print(f"\n📊 Testing {name} ({symbol})")
            
            try:
                # Get company
                company = edgar.Company(symbol)
                
                # Get recent proxy filings (DEF 14A)
                proxy_filings = company.get_filings(form="DEF 14A")

                if len(proxy_filings) > 0:
                    proxy_filing = proxy_filings[0]  # Get the most recent
                    print(f"   📄 Found proxy filing: {proxy_filing.accession_number}")
                    print(f"   📅 Filing date: {proxy_filing.filing_date}")

                    # Try to get filing object
                    try:
                        filing_obj = proxy_filing.obj()

                        # Look for executive compensation data
                        # This is where we would extract XBRL structured data
                        result = {
                            'symbol': symbol,
                            'company_name': name,
                            'filing_date': str(proxy_filing.filing_date),
                            'accession_number': proxy_filing.accession_number,
                            'has_xbrl': hasattr(filing_obj, 'xbrl'),
                            'has_html': hasattr(filing_obj, 'html'),
                            'has_text': hasattr(filing_obj, 'text'),
                            'status': 'found_proxy'
                        }

                        print(f"   ✅ Proxy filing processed")

                    except Exception as obj_error:
                        print(f"   ⚠️ Could not process filing object: {obj_error}")
                        result = {
                            'symbol': symbol,
                            'company_name': name,
                            'filing_date': str(proxy_filing.filing_date),
                            'accession_number': proxy_filing.accession_number,
                            'status': 'found_proxy_no_obj',
                            'error': str(obj_error)
                        }
                    
                else:
                    result = {
                        'symbol': symbol,
                        'company_name': name,
                        'status': 'no_proxy_found'
                    }
                    print(f"   ⚠️ No recent proxy filings found")
                
                results.append(result)
                
            except Exception as e:
                print(f"   ❌ Error processing {symbol}: {e}")
                results.append({
                    'symbol': symbol,
                    'company_name': name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
        
    except Exception as e:
        print(f"❌ Error in XBRL proxy extraction test: {e}")
        return []

async def test_enhanced_edgar_extraction():
    """Test enhanced EDGAR extraction with multiple approaches"""
    
    print("\n🚀 TESTING ENHANCED EDGAR EXTRACTION")
    print("=" * 60)
    
    try:
        import edgar
        edgar.set_identity("test.user@example.com")
        
        # Test with Apple (known to have good proxy data)
        company = edgar.Company("AAPL")
        print(f"📊 Testing enhanced extraction for {company.name}")
        
        # Get latest proxy filing
        proxy_filings = company.get_filings(form="DEF 14A")

        if len(proxy_filings) > 0:
            proxy_filing = proxy_filings[0]  # Get the most recent
            print(f"   📄 Proxy filing: {proxy_filing.accession_number}")

            # Try to get filing object
            try:
                filing_obj = proxy_filing.obj()

                # Try different extraction methods
                extraction_methods = []

                # Method 1: Check for XBRL instance
                if hasattr(filing_obj, 'xbrl'):
                    extraction_methods.append("xbrl_instance")
                    print("   ✅ XBRL instance found")
                else:
                    print("   ⚠️ No XBRL instance found")

                # Method 2: HTML content analysis
                if hasattr(filing_obj, 'html'):
                    extraction_methods.append("html_content")
                    print("   ✅ HTML content available")

                # Method 3: Text extraction
                if hasattr(filing_obj, 'text'):
                    extraction_methods.append("text_extraction")
                    print("   ✅ Text extraction available")

                # Method 4: Document structure
                if hasattr(filing_obj, 'documents'):
                    extraction_methods.append("document_structure")
                    print(f"   ✅ Document structure: {len(filing_obj.documents)} documents")

                result = {
                    'company': company.name,
                    'symbol': 'AAPL',
                    'filing_date': str(proxy_filing.filing_date),
                    'accession_number': proxy_filing.accession_number,
                    'extraction_methods': extraction_methods,
                    'status': 'success'
                }

                return result

            except Exception as obj_error:
                print(f"   ❌ Could not process filing object: {obj_error}")
                return {
                    'company': company.name,
                    'symbol': 'AAPL',
                    'filing_date': str(proxy_filing.filing_date),
                    'accession_number': proxy_filing.accession_number,
                    'status': 'filing_obj_error',
                    'error': str(obj_error)
                }
            
        else:
            print("   ❌ No proxy filings found")
            return {'status': 'no_proxy_found'}
            
    except Exception as e:
        print(f"❌ Error in enhanced EDGAR extraction test: {e}")
        return {'status': 'error', 'error': str(e)}

async def main():
    """Main test function"""
    
    print("🚀 XBRL EXECUTIVE COMPENSATION EXTRACTION TESTS")
    print("=" * 70)
    print("🎯 Testing new XBRL-based approach for executive compensation")
    print("📊 Using edgartools library for SEC EDGAR access")
    
    # Test 1: Installation
    installation_success = await test_edgartools_installation()
    
    if not installation_success:
        print("\n❌ Cannot proceed without edgartools installation")
        return
    
    # Test 2: XBRL proxy extraction
    proxy_results = await test_xbrl_proxy_extraction()
    
    # Test 3: Enhanced EDGAR extraction
    enhanced_result = await test_enhanced_edgar_extraction()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"✅ Installation: {'Success' if installation_success else 'Failed'}")
    print(f"📄 Proxy filings tested: {len(proxy_results)}")
    
    successful_extractions = len([r for r in proxy_results if r.get('status') == 'found_proxy'])
    print(f"🎯 Successful proxy extractions: {successful_extractions}")
    
    if enhanced_result.get('status') == 'success':
        methods = enhanced_result.get('extraction_methods', [])
        print(f"🔧 Available extraction methods: {len(methods)}")
        for method in methods:
            print(f"   • {method}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"tests/results/xbrl_test_results_{timestamp}.json"
    
    os.makedirs("tests/results", exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'installation_success': installation_success,
            'proxy_results': proxy_results,
            'enhanced_result': enhanced_result
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Next steps
    print(f"\n🎯 NEXT STEPS:")
    if installation_success:
        print("✅ 1. edgartools is working - proceed with XBRL implementation")
        print("🔧 2. Develop XBRL executive compensation parser")
        print("📊 3. Test with Fortune 1-8 companies")
        print("🚀 4. Integrate into main pipeline")
    else:
        print("❌ 1. Install edgartools: pip install edgartools")
        print("🔧 2. Retry tests after installation")

if __name__ == "__main__":
    asyncio.run(main())
