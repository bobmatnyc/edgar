#!/usr/bin/env python3
"""
EDGAR Executive Compensation vs Tax Expense Analyzer
Prototype implementation for feasibility demonstration
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional
import time
from datetime import datetime, timedelta

class EDGARAnalyzer:
    """
    Prototype class for extracting executive compensation and tax expense data
    from SEC EDGAR filings for Fortune 500 companies.
    """

    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.headers = {
            'User-Agent': 'Company Analysis Tool contact@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.rate_limit_delay = 0.1  # 10 requests per second max

    def get_company_submissions(self, cik: str) -> Dict:
        """
        Retrieve company submission history from SEC API

        Args:
            cik: 10-digit Central Index Key

        Returns:
            Dictionary containing company filing history
        """
        # Ensure CIK is 10 digits with leading zeros
        cik_formatted = str(cik).zfill(10)
        url = f"{self.base_url}/submissions/CIK{cik_formatted}.json"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching submissions for CIK {cik}: {e}")
            return {}

    def get_company_facts(self, cik: str) -> Dict:
        """
        Retrieve company XBRL facts from SEC API

        Args:
            cik: 10-digit Central Index Key

        Returns:
            Dictionary containing XBRL financial data
        """
        cik_formatted = str(cik).zfill(10)
        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik_formatted}.json"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching facts for CIK {cik}: {e}")
            return {}

    def extract_tax_expense(self, company_facts: Dict, year: int) -> Optional[float]:
        """
        Extract income tax expense from company XBRL facts

        Args:
            company_facts: Company facts dictionary from SEC API
            year: Target year for data extraction

        Returns:
            Tax expense amount or None if not found
        """
        try:
            # Look for income tax expense in US-GAAP taxonomy
            us_gaap = company_facts.get('facts', {}).get('us-gaap', {})

            # Try different tax expense tags
            tax_tags = [
                'IncomeTaxExpenseBenefit',
                'CurrentIncomeTaxExpenseBenefit',
                'IncomeTaxesPaid'
            ]

            for tag in tax_tags:
                if tag in us_gaap:
                    units = us_gaap[tag].get('units', {})
                    if 'USD' in units:
                        for fact in units['USD']:
                            # Look for annual data (10-K filings)
                            if (fact.get('fy') == year and
                                fact.get('form') in ['10-K', '10-K/A']):
                                return fact.get('val')

            return None
        except Exception as e:
            print(f"Error extracting tax expense: {e}")
            return None

    def find_proxy_filings(self, submissions: Dict, year: int) -> List[Dict]:
        """
        Find proxy statement (DEF 14A) filings for executive compensation data

        Args:
            submissions: Company submissions dictionary
            year: Target year

        Returns:
            List of relevant proxy filings
        """
        try:
            filings = []
            recent_filings = submissions.get('filings', {}).get('recent', {})

            if not recent_filings:
                return filings

            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])

            for i, form in enumerate(forms):
                if form == 'DEF 14A':
                    filing_date = filing_dates[i]
                    if filing_date.startswith(str(year)):
                        filings.append({
                            'form': form,
                            'filingDate': filing_date,
                            'accessionNumber': accession_numbers[i]
                        })

            return filings
        except Exception as e:
            print(f"Error finding proxy filings: {e}")
            return []

# Sample Fortune 500 companies for testing
SAMPLE_COMPANIES = {
    'AAPL': '0000320193',  # Apple Inc.
    'MSFT': '0000789019',  # Microsoft Corporation
    'GOOGL': '0001652044', # Alphabet Inc.
    'AMZN': '0001018724', # Amazon.com Inc.
    'TSLA': '0001318605'  # Tesla Inc.
}

def main():
    """
    Demonstration of EDGAR data extraction capabilities
    """
    analyzer = EDGARAnalyzer()
    results = []

    print("EDGAR Executive Compensation vs Tax Expense Analysis")
    print("=" * 60)

    for symbol, cik in SAMPLE_COMPANIES.items():
        print(f"\nAnalyzing {symbol} (CIK: {cik})...")

        # Get company facts for tax data
        facts = analyzer.get_company_facts(cik)
        if facts:
            tax_expense_2023 = analyzer.extract_tax_expense(facts, 2023)
            print(f"  Tax Expense 2023: ${tax_expense_2023:,.0f}" if tax_expense_2023 else "  Tax Expense 2023: Not found")

        # Get submissions for proxy filings
        submissions = analyzer.get_company_submissions(cik)
        if submissions:
            company_name = submissions.get('name', symbol)
            proxy_filings = analyzer.find_proxy_filings(submissions, 2024)
            print(f"  Company: {company_name}")
            print(f"  Proxy filings found: {len(proxy_filings)}")

        results.append({
            'Symbol': symbol,
            'CIK': cik,
            'Company': company_name if 'company_name' in locals() else symbol,
            'Tax_Expense_2023': tax_expense_2023,
            'Proxy_Filings_2024': len(proxy_filings) if 'proxy_filings' in locals() else 0
        })

    # Create summary DataFrame
    df = pd.DataFrame(results)
    print(f"\nSummary Results:")
    print(df.to_string(index=False))

    return df

if __name__ == "__main__":
    main()