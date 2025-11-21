#!/usr/bin/env python3
"""
Test SEC EDGAR submissions API to understand proxy filing data structure
"""

import requests
import json

def test_submissions_api():
    """Test submissions API to see proxy filing structure"""
    
    # Test with Apple's CIK
    cik = "0000320193"  # Apple Inc.
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    headers = {'User-Agent': 'Test Tool test@example.com'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f'Successfully accessed submissions for: {data.get("name", "Unknown")}')
            
            # Look at recent filings structure
            recent_filings = data.get('filings', {}).get('recent', {})
            
            if recent_filings:
                forms = recent_filings.get('form', [])
                filing_dates = recent_filings.get('filingDate', [])
                accession_numbers = recent_filings.get('accessionNumber', [])
                primary_documents = recent_filings.get('primaryDocument', [])
                
                print(f"\nAvailable fields in recent filings:")
                for key in recent_filings.keys():
                    print(f"  - {key}")
                
                # Find DEF 14A filings
                print(f"\nLooking for DEF 14A filings:")
                for i, form in enumerate(forms):
                    if form == 'DEF 14A':
                        print(f"  Found DEF 14A:")
                        print(f"    Date: {filing_dates[i] if i < len(filing_dates) else 'N/A'}")
                        print(f"    Accession: {accession_numbers[i] if i < len(accession_numbers) else 'N/A'}")
                        print(f"    Primary Doc: {primary_documents[i] if i < len(primary_documents) else 'N/A'}")
                        
                        # Construct URL
                        if i < len(accession_numbers) and i < len(primary_documents):
                            accession = accession_numbers[i].replace('-', '')
                            primary_doc = primary_documents[i]
                            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{primary_doc}"
                            print(f"    URL: {filing_url}")
                        print()
                        
                        # Only show first few
                        if i > 2:
                            break
            else:
                print("No recent filings found")
                
        else:
            print(f'API request failed with status: {response.status_code}')
            print(f'Response: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_submissions_api()
