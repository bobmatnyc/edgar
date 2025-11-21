#!/usr/bin/env python3
"""
Generate CSV reports from EDGAR CLI results
"""

import json
import pandas as pd
from datetime import datetime
import os

def create_csv_reports():
    """Create CSV reports from JSON results"""
    
    # Load the results
    results_file = "results/top_100_enhanced_results_20251121_180216.json"
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Processing {data['total_companies']} companies...")
    
    # Create executive data for CSV
    executive_data = []
    
    for company in data['companies']:
        if company['success'] and company['executives']:
            for exec in company['executives']:
                executive_data.append({
                    'Company_Rank': company['rank'],
                    'Company_Name': company['name'],
                    'CIK': company['cik'],
                    'Executive_Name': exec['name'],
                    'Title': exec['title'],
                    'Total_Compensation': exec['total_compensation'],
                    'Salary': exec['salary'],
                    'Bonus': exec['bonus'],
                    'Stock_Awards': exec['stock_awards'],
                    'Option_Awards': exec['option_awards'],
                    'Salary_Percent': (exec['salary'] / exec['total_compensation'] * 100) if exec['total_compensation'] > 0 else 0,
                    'Bonus_Percent': (exec['bonus'] / exec['total_compensation'] * 100) if exec['total_compensation'] > 0 else 0,
                    'Stock_Percent': (exec['stock_awards'] / exec['total_compensation'] * 100) if exec['total_compensation'] > 0 else 0,
                    'Options_Percent': (exec['option_awards'] / exec['total_compensation'] * 100) if exec['total_compensation'] > 0 else 0
                })
    
    # Create DataFrame
    executive_df = pd.DataFrame(executive_data)
    
    # Sort by total compensation descending
    executive_df = executive_df.sort_values('Total_Compensation', ascending=False)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save main CSV
    csv_file = f"tests/results/executive_compensation_{timestamp}.csv"
    executive_df.to_csv(csv_file, index=False)
    
    # Create top executives CSV (top 25)
    top_executives_file = f"tests/results/top_25_executives_{timestamp}.csv"
    executive_df.head(25).to_csv(top_executives_file, index=False)
    
    # Create company summary CSV
    company_summary = []
    for company in data['companies']:
        if company['success'] and company['executives']:
            total_comp = sum(exec['total_compensation'] for exec in company['executives'])
            avg_comp = total_comp / len(company['executives'])
            highest_paid = max(company['executives'], key=lambda x: x['total_compensation'])
            
            company_summary.append({
                'Rank': company['rank'],
                'Company': company['name'],
                'CIK': company['cik'],
                'Executives_Found': len(company['executives']),
                'Total_Executive_Compensation': total_comp,
                'Average_Executive_Compensation': avg_comp,
                'Highest_Paid_Executive': highest_paid['name'],
                'Highest_Compensation': highest_paid['total_compensation'],
                'CEO_Compensation': next((exec['total_compensation'] for exec in company['executives'] 
                                        if 'chief executive' in exec['title'].lower() or 'ceo' in exec['title'].lower()), 0)
            })
        else:
            company_summary.append({
                'Rank': company['rank'],
                'Company': company['name'],
                'CIK': company['cik'],
                'Executives_Found': 0,
                'Total_Executive_Compensation': 0,
                'Average_Executive_Compensation': 0,
                'Highest_Paid_Executive': 'N/A',
                'Highest_Compensation': 0,
                'CEO_Compensation': 0
            })
    
    company_df = pd.DataFrame(company_summary)
    company_summary_file = f"tests/results/company_summary_{timestamp}.csv"
    company_df.to_csv(company_summary_file, index=False)
    
    print(f"✅ CSV reports created:")
    print(f"   📊 All Executives: {csv_file} ({len(executive_df)} executives)")
    print(f"   🏆 Top 25 Executives: {top_executives_file}")
    print(f"   🏢 Company Summary: {company_summary_file} ({len(company_df)} companies)")
    
    # Print some quick stats
    if not executive_df.empty:
        print(f"\n📈 Quick Statistics:")
        print(f"   💰 Highest Paid Executive: {executive_df.iloc[0]['Executive_Name']} at {executive_df.iloc[0]['Company_Name']}")
        print(f"   💵 Highest Compensation: ${executive_df.iloc[0]['Total_Compensation']:,.0f}")
        print(f"   📊 Average Compensation: ${executive_df['Total_Compensation'].mean():,.0f}")
        print(f"   🎯 Median Compensation: ${executive_df['Total_Compensation'].median():,.0f}")

if __name__ == "__main__":
    create_csv_reports()
