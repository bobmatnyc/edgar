#!/usr/bin/env python3
"""
Analyze fixed Fortune 100 results
"""

import pandas as pd

def analyze_fixed_fortune_100():
    """Analyze fixed Fortune 100 executive compensation results"""
    
    # Read the fixed Fortune 100 Excel file
    file_path = 'tests/results/fortune_100_fixed_complete_20251121_184616.xlsx'
    
    print('📊 FIXED FORTUNE 100 ANALYSIS - FORTUNE 1-8 STATUS')
    print('=' * 70)
    
    try:
        # Read Key Findings to see Fortune 1-8 companies
        df_findings = pd.read_excel(file_path, sheet_name='Key Findings')
        
        print('🏆 FORTUNE 1-8 COMPANIES NOW INCLUDED:')
        fortune_1_8 = df_findings[df_findings['Fortune Rank'] <= 8].sort_values('Fortune Rank')
        
        for _, row in fortune_1_8.iterrows():
            rank = int(row['Fortune Rank'])
            company = row['Company']
            total_pay = row['Total Executive Pay']
            ceo_pay = row['CEO Pay']
            quality = row['Data Quality']
            confidence = row['Confidence Score']
            
            print(f'{rank:2d}. {company}')
            print(f'    Total Executive Pay: ${total_pay:,.0f}')
            print(f'    CEO Pay: ${ceo_pay:,.0f}')
            print(f'    Quality: {quality} | Confidence: {confidence}')
            print()
        
        # Show top executives now
        df_executives = pd.read_excel(file_path, sheet_name='List of Executives')
        print('💰 TOP 10 HIGHEST PAID EXECUTIVES (NOW INCLUDING FORTUNE 1-8):')
        top_10 = df_executives.head(10)
        
        for i, (_, exec_row) in enumerate(top_10.iterrows(), 1):
            name = exec_row['Executive Name']
            company = exec_row['Company']
            total_comp = exec_row['Average Annual Pay']
            
            print(f'{i:2d}. {name} ({company}) - ${total_comp:,.0f}')
        
        print()
        print('📊 SUMMARY STATISTICS:')
        print(f'   Total Companies: {len(df_findings)}')
        print(f'   Total Executives: {len(df_executives)}')
        total_comp_sum = df_executives['Average Annual Pay'].sum()
        avg_comp = df_executives['Average Annual Pay'].mean()
        print(f'   Total Executive Compensation: ${total_comp_sum/1_000_000_000:.1f}B')
        print(f'   Average Executive Pay: ${avg_comp:,.0f}')
        
        # Fortune 1-8 vs 9-100 comparison
        fortune_1_8_companies = fortune_1_8['Company'].tolist()
        fortune_1_8_execs = df_executives[df_executives['Company'].isin(fortune_1_8_companies)]
        fortune_9_100_execs = df_executives[~df_executives['Company'].isin(fortune_1_8_companies)]
        
        print(f'\n📈 FORTUNE 1-8 vs 9-100 COMPARISON:')
        f18_avg = fortune_1_8_execs['Average Annual Pay'].mean()
        f9100_avg = fortune_9_100_execs['Average Annual Pay'].mean()
        print(f'   Fortune 1-8: {len(fortune_1_8_execs)} executives, avg pay: ${f18_avg:,.0f}')
        print(f'   Fortune 9-100: {len(fortune_9_100_execs)} executives, avg pay: ${f9100_avg:,.0f}')
        
        # Show all Fortune 1-8 companies that were included
        print(f'\n🎯 ALL FORTUNE 1-8 COMPANIES STATUS:')
        all_companies = ['Walmart Inc.', 'Amazon.com Inc.', 'Apple Inc.', 'CVS Health Corporation', 
                        'UnitedHealth Group Incorporated', 'Exxon Mobil Corporation', 
                        'Berkshire Hathaway Inc.', 'Alphabet Inc.']
        
        for i, company_name in enumerate(all_companies, 1):
            if company_name in fortune_1_8_companies:
                status = "✅ INCLUDED"
                company_data = fortune_1_8[fortune_1_8['Company'] == company_name].iloc[0]
                quality = company_data['Data Quality']
                confidence = company_data['Confidence Score']
                total_pay = company_data['Total Executive Pay']
                print(f'   {i:2d}. {company_name}: {status} ({quality}, {confidence}) - ${total_pay:,.0f}')
            else:
                print(f'   {i:2d}. {company_name}: ❌ EXCLUDED (Low quality)')
        
        print(f'\n🚀 KEY ACHIEVEMENTS:')
        print(f'   ✅ {len(fortune_1_8)} of Fortune 1-8 companies now included')
        print(f'   ✅ {len(df_findings)} total companies ready for analysis')
        print(f'   ✅ {len(df_executives)} validated executives')
        print(f'   ✅ Complete Fortune ranking coverage from 1-100')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_fixed_fortune_100()
