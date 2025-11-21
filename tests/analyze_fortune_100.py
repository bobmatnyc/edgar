#!/usr/bin/env python3
"""
Analyze Fortune 100 results
"""

import pandas as pd

def analyze_fortune_100():
    """Analyze Fortune 100 executive compensation results"""
    
    # Read the Fortune 100 Excel file
    file_path = 'tests/results/fortune_100_executive_compensation_20251121_183903.xlsx'
    
    print('📊 FORTUNE 100 EXECUTIVE COMPENSATION ANALYSIS')
    print('=' * 70)
    
    # Read each sheet
    sheets = ['Executive Pay Breakdown', 'List of Executives', 'Key Findings', 'QA Summary']
    
    for sheet_name in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f'\n📋 {sheet_name.upper()}:')
            print(f'   Shape: {df.shape}')
            print(f'   Columns: {list(df.columns)}')
            if df.shape[0] > 0:
                print('   Sample data:')
                print(df.head(3).to_string(index=False))
        except Exception as e:
            print(f'   Error reading {sheet_name}: {e}')
    
    print()
    print('🎯 KEY STATISTICS:')
    
    # Analyze the data
    try:
        df_breakdown = pd.read_excel(file_path, sheet_name='Executive Pay Breakdown')
        df_findings = pd.read_excel(file_path, sheet_name='Key Findings')
        
        total_execs = len(df_breakdown)
        total_companies = len(df_findings)
        
        ceo_data = df_breakdown[df_breakdown['Title'].str.contains('Chief Executive', na=False)]
        avg_ceo_pay = ceo_data['Total Compensation'].mean()
        total_comp = df_breakdown['Total Compensation'].sum()
        
        print(f'   Total Executives: {total_execs}')
        print(f'   Total Companies: {total_companies}')
        print(f'   Average CEO Pay: ${avg_ceo_pay:,.0f}')
        print(f'   Total Executive Compensation: ${total_comp/1_000_000_000:.1f}B')
        
        # Data source breakdown
        source_counts = df_breakdown['Data Source'].value_counts()
        print(f'\n📊 DATA SOURCE BREAKDOWN:')
        for source, count in source_counts.items():
            print(f'   {source}: {count} executives')
        
        # Quality breakdown
        quality_counts = df_breakdown['Data Quality'].value_counts()
        print(f'\n🔍 QUALITY BREAKDOWN:')
        for quality, count in quality_counts.items():
            print(f'   {quality}: {count} executives')
        
        # Top 10 highest paid executives
        print(f'\n💰 TOP 10 HIGHEST PAID EXECUTIVES:')
        top_10 = df_breakdown.nlargest(10, 'Total Compensation')
        for i, (_, exec_row) in enumerate(top_10.iterrows(), 1):
            print(f'   {i:2d}. {exec_row["Executive Name"]} ({exec_row["Company"]}) - ${exec_row["Total Compensation"]:,.0f}')
        
        # Company rankings by total executive pay
        print(f'\n🏢 TOP 10 COMPANIES BY TOTAL EXECUTIVE PAY:')
        company_totals = df_findings.nlargest(10, 'Total Executive Pay')
        for i, (_, company_row) in enumerate(company_totals.iterrows(), 1):
            print(f'   {i:2d}. {company_row["Company"]} (Rank {company_row["Fortune Rank"]}) - ${company_row["Total Executive Pay"]:,.0f}')
        
        # Fortune ranking analysis
        print(f'\n📈 FORTUNE RANKING ANALYSIS:')
        fortune_1_50 = df_breakdown[df_breakdown['Fortune Rank'] <= 50]
        fortune_51_100 = df_breakdown[df_breakdown['Fortune Rank'] > 50]
        
        print(f'   Fortune 1-50:')
        print(f'     • Companies: {len(fortune_1_50["Company"].unique())}')
        print(f'     • Executives: {len(fortune_1_50)}')
        print(f'     • Avg Executive Pay: ${fortune_1_50["Total Compensation"].mean():,.0f}')
        print(f'     • Total Compensation: ${fortune_1_50["Total Compensation"].sum()/1_000_000_000:.1f}B')
        
        print(f'   Fortune 51-100:')
        print(f'     • Companies: {len(fortune_51_100["Company"].unique())}')
        print(f'     • Executives: {len(fortune_51_100)}')
        print(f'     • Avg Executive Pay: ${fortune_51_100["Total Compensation"].mean():,.0f}')
        print(f'     • Total Compensation: ${fortune_51_100["Total Compensation"].sum()/1_000_000_000:.1f}B')
        
    except Exception as e:
        print(f'Error analyzing data: {e}')
    
    print('\n🎯 Fortune 100 analysis complete!')

if __name__ == "__main__":
    analyze_fortune_100()
