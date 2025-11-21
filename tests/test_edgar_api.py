#!/usr/bin/env python3
"""
Quick test of SEC EDGAR API functionality
"""

import requests
import json

def test_edgar_api():
    """Test basic EDGAR API access"""

    # Test XBRL facts API for Apple
    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json'
    headers = {'User-Agent': 'Test Tool test@example.com'}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f'Successfully accessed XBRL facts for: {data.get("entityName", "Unknown")}')

            # Look for tax expense data
            us_gaap = data.get('facts', {}).get('us-gaap', {})
            tax_tags = ['IncomeTaxExpenseBenefit', 'CurrentIncomeTaxExpenseBenefit']

            for tag in tax_tags:
                if tag in us_gaap:
                    print(f'Found tax data tag: {tag}')
                    units = us_gaap[tag].get('units', {})
                    if 'USD' in units:
                        recent_facts = units['USD'][-5:]  # Last 5 entries
                        for fact in recent_facts:
                            if fact.get('form') == '10-K':
                                print(f'  {fact.get("fy", "Unknown year")}: ${fact.get("val", 0):,.0f}')
                    break
        else:
            print(f'API request failed with status: {response.status_code}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_edgar_api()