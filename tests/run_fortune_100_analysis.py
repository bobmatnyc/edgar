#!/usr/bin/env python3
"""
Fortune 100 Executive Compensation Analysis with Enhanced QA
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.qa_controller import ComprehensiveQAController
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.services.edgar_api_service import EdgarApiService
from edgar_analyzer.services.company_service import CompanyService
from edgar_analyzer.config.settings import ConfigService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fortune 100 companies (expanding from Fortune 50)
FORTUNE_100_COMPANIES = [
    # Fortune 1-50 (existing)
    {"rank": 1, "name": "Walmart Inc.", "cik": "0000104169"},
    {"rank": 2, "name": "Amazon.com Inc.", "cik": "0001018724"},
    {"rank": 3, "name": "Apple Inc.", "cik": "0000320193"},
    {"rank": 4, "name": "CVS Health Corporation", "cik": "0000064803"},
    {"rank": 5, "name": "UnitedHealth Group Incorporated", "cik": "0000731766"},
    {"rank": 6, "name": "Exxon Mobil Corporation", "cik": "0000034088"},
    {"rank": 7, "name": "Berkshire Hathaway Inc.", "cik": "0001067983"},
    {"rank": 8, "name": "Alphabet Inc.", "cik": "0001652044"},
    {"rank": 9, "name": "McKesson Corporation", "cik": "0000927653"},
    {"rank": 10, "name": "Cencora Inc.", "cik": "0001140859"},
    {"rank": 11, "name": "Costco Wholesale Corporation", "cik": "0000909832"},
    {"rank": 12, "name": "JPMorgan Chase & Co.", "cik": "0000019617"},
    {"rank": 13, "name": "Microsoft Corporation", "cik": "0000789019"},
    {"rank": 14, "name": "Cardinal Health, Inc.", "cik": "0000721371"},
    {"rank": 15, "name": "Chevron Corporation", "cik": "0000093410"},
    {"rank": 16, "name": "Ford Motor Company", "cik": "0000037996"},
    {"rank": 17, "name": "General Motors Company", "cik": "0001467858"},
    {"rank": 18, "name": "Elevance Health, Inc.", "cik": "0001156375"},
    {"rank": 19, "name": "Fannie Mae", "cik": "0000310522"},
    {"rank": 20, "name": "Home Depot, Inc.", "cik": "0000354950"},
    {"rank": 21, "name": "Marathon Petroleum Corporation", "cik": "0001510295"},
    {"rank": 22, "name": "Phillips 66", "cik": "0001534701"},
    {"rank": 23, "name": "Valero Energy Corporation", "cik": "0001035002"},
    {"rank": 24, "name": "Kroger Co.", "cik": "0000056873"},
    {"rank": 25, "name": "Bank of America Corporation", "cik": "0000070858"},
    {"rank": 26, "name": "Centene Corporation", "cik": "0001071739"},
    {"rank": 27, "name": "Verizon Communications Inc.", "cik": "0000732712"},
    {"rank": 28, "name": "Cigna Group", "cik": "0000701221"},
    {"rank": 29, "name": "AT&T Inc.", "cik": "0000732717"},
    {"rank": 30, "name": "General Electric Company", "cik": "0000040545"},
    {"rank": 31, "name": "Tesla, Inc.", "cik": "0001318605"},
    {"rank": 32, "name": "Walgreens Boots Alliance, Inc.", "cik": "0001618921"},
    {"rank": 33, "name": "Meta Platforms, Inc.", "cik": "0001326801"},
    {"rank": 34, "name": "Comcast Corporation", "cik": "0001166691"},
    {"rank": 35, "name": "Freddie Mac", "cik": "0000794367"},
    {"rank": 36, "name": "IBM Corporation", "cik": "0000051143"},
    {"rank": 37, "name": "Energy Transfer LP", "cik": "0001276187"},
    {"rank": 38, "name": "Procter & Gamble Company", "cik": "0000080424"},
    {"rank": 39, "name": "Archer-Daniels-Midland Company", "cik": "0000007084"},
    {"rank": 40, "name": "Johnson & Johnson", "cik": "0000200406"},
    {"rank": 41, "name": "Dell Technologies Inc.", "cik": "0001571996"},
    {"rank": 42, "name": "FedEx Corporation", "cik": "0001048911"},
    {"rank": 43, "name": "UPS, Inc.", "cik": "0001090727"},
    {"rank": 44, "name": "Lowe's Companies, Inc.", "cik": "0000060667"},
    {"rank": 45, "name": "Wells Fargo & Company", "cik": "0000072971"},
    {"rank": 46, "name": "Target Corporation", "cik": "0000027419"},
    {"rank": 47, "name": "Humana Inc.", "cik": "0000049071"},
    {"rank": 48, "name": "Lockheed Martin Corporation", "cik": "0000936468"},
    {"rank": 49, "name": "AbbVie Inc.", "cik": "0001551152"},
    {"rank": 50, "name": "Caterpillar Inc.", "cik": "0000018230"},
    
    # Fortune 51-100 (new additions)
    {"rank": 51, "name": "State Farm Insurance Companies", "cik": "0000896159"},
    {"rank": 52, "name": "Raytheon Technologies Corporation", "cik": "0000101829"},
    {"rank": 53, "name": "Pfizer Inc.", "cik": "0000078003"},
    {"rank": 54, "name": "Intel Corporation", "cik": "0000050863"},
    {"rank": 55, "name": "Boeing Company", "cik": "0000012927"},
    {"rank": 56, "name": "Nike, Inc.", "cik": "0000320187"},
    {"rank": 57, "name": "Starbucks Corporation", "cik": "0000829224"},
    {"rank": 58, "name": "Goldman Sachs Group, Inc.", "cik": "0000886982"},
    {"rank": 59, "name": "Morgan Stanley", "cik": "0000895421"},
    {"rank": 60, "name": "Citigroup Inc.", "cik": "0000831001"},
    {"rank": 61, "name": "American Express Company", "cik": "0000004962"},
    {"rank": 62, "name": "Honeywell International Inc.", "cik": "0000773840"},
    {"rank": 63, "name": "3M Company", "cik": "0000066740"},
    {"rank": 64, "name": "Coca-Cola Company", "cik": "0000021344"},
    {"rank": 65, "name": "PepsiCo, Inc.", "cik": "0000077476"},
    {"rank": 66, "name": "Oracle Corporation", "cik": "0001341439"},
    {"rank": 67, "name": "Salesforce, Inc.", "cik": "0001108524"},
    {"rank": 68, "name": "Netflix, Inc.", "cik": "0001065280"},
    {"rank": 69, "name": "Adobe Inc.", "cik": "0000796343"},
    {"rank": 70, "name": "Cisco Systems, Inc.", "cik": "0000858877"},
    {"rank": 71, "name": "Mastercard Incorporated", "cik": "0001141391"},
    {"rank": 72, "name": "Visa Inc.", "cik": "0001403161"},
    {"rank": 73, "name": "PayPal Holdings, Inc.", "cik": "0001633917"},
    {"rank": 74, "name": "Broadcom Inc.", "cik": "0001730168"},
    {"rank": 75, "name": "QUALCOMM Incorporated", "cik": "0000804328"},
    {"rank": 76, "name": "Texas Instruments Incorporated", "cik": "0000097476"},
    {"rank": 77, "name": "Advanced Micro Devices, Inc.", "cik": "0000002488"},
    {"rank": 78, "name": "NVIDIA Corporation", "cik": "0001045810"},
    {"rank": 79, "name": "Micron Technology, Inc.", "cik": "0000723125"},
    {"rank": 80, "name": "Applied Materials, Inc.", "cik": "0000006951"},
    {"rank": 81, "name": "Lam Research Corporation", "cik": "0000707549"},
    {"rank": 82, "name": "KLA Corporation", "cik": "0000319201"},
    {"rank": 83, "name": "Analog Devices, Inc.", "cik": "0000006281"},
    {"rank": 84, "name": "Marvell Technology, Inc.", "cik": "0001058057"},
    {"rank": 85, "name": "Mondelez International, Inc.", "cik": "0001103982"},
    {"rank": 86, "name": "General Mills, Inc.", "cik": "0000040704"},
    {"rank": 87, "name": "Kellogg Company", "cik": "0000055067"},
    {"rank": 88, "name": "Campbell Soup Company", "cik": "0000016732"},
    {"rank": 89, "name": "Tyson Foods, Inc.", "cik": "0000100493"},
    {"rank": 90, "name": "Hormel Foods Corporation", "cik": "0000047079"},
    {"rank": 91, "name": "ConAgra Brands, Inc.", "cik": "0000023217"},
    {"rank": 92, "name": "Kraft Heinz Company", "cik": "0001637459"},
    {"rank": 93, "name": "McCormick & Company, Incorporated", "cik": "0000063754"},
    {"rank": 94, "name": "Hershey Company", "cik": "0000047111"},
    {"rank": 95, "name": "Colgate-Palmolive Company", "cik": "0000021665"},
    {"rank": 96, "name": "Clorox Company", "cik": "0000021076"},
    {"rank": 97, "name": "Kimberly-Clark Corporation", "cik": "0000055785"},
    {"rank": 98, "name": "Church & Dwight Co., Inc.", "cik": "0000313927"},
    {"rank": 99, "name": "Estee Lauder Companies Inc.", "cik": "0000001001"},
    {"rank": 100, "name": "L'Oreal USA, Inc.", "cik": "0000950170"}
]

async def run_fortune_100_analysis():
    """Run comprehensive Fortune 100 analysis with QA"""
    
    print("🚀 FORTUNE 100 EXECUTIVE COMPENSATION ANALYSIS")
    print("=" * 60)
    print(f"📊 Analyzing {len(FORTUNE_100_COMPANIES)} Fortune 100 companies")
    print(f"🔍 Enhanced QA validation and confidence scoring")
    print(f"📈 Professional Excel output with quality transparency")
    
    # Initialize services
    config_service = ConfigService()
    edgar_api_service = EdgarApiService(config_service)
    company_service = CompanyService(config_service, edgar_api_service)
    data_extraction_service = DataExtractionService(edgar_api_service, company_service)
    llm_service = LLMService()
    qa_controller = ComprehensiveQAController(
        llm_service=llm_service,
        web_search_enabled=False  # Fast processing
    )
    
    # Results tracking
    results = {
        'timestamp': datetime.now().isoformat(),
        'analysis_type': 'Fortune 100 Executive Compensation',
        'total_companies': len(FORTUNE_100_COMPANIES),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'qa_summary': {
            'high_quality': 0,
            'medium_quality': 0,
            'low_quality': 0,
            'rejected': 0,
            'total_issues': 0
        },
        'companies': [],
        'cleaned_data': []
    }
    
    print(f"\n🔍 Starting Fortune 100 analysis...")
    
    # Process each company
    for i, company in enumerate(FORTUNE_100_COMPANIES):
        company_name = company['name']
        rank = company['rank']
        cik = company['cik']
        
        print(f"\n🏢 [{rank:3d}/100] {company_name}")
        
        try:
            # Extract executive compensation data
            print(f"  📊 Extracting executive compensation data...")
            extraction_result = await data_extraction_service.extract_executive_compensation(cik)
            
            if not extraction_result or not extraction_result.get('executives'):
                print(f"  ⚠️ No executive data found")
                results['companies'].append({
                    'name': company_name,
                    'rank': rank,
                    'cik': cik,
                    'success': False,
                    'executives': [],
                    'error': 'No executive data found'
                })
                results['failed_extractions'] += 1
                continue
            
            # Prepare company data for QA
            company_data = {
                'name': company_name,
                'rank': rank,
                'cik': cik,
                'success': True,
                'executives': extraction_result['executives']
            }
            
            print(f"  🔍 Running QA validation on {len(extraction_result['executives'])} executives...")
            
            # Run QA validation
            qa_result = await qa_controller.qa_executive_data(company_data)
            
            # Determine quality level
            confidence = qa_result.confidence_score
            if confidence >= 0.7:
                quality_level = 'HIGH'
                results['qa_summary']['high_quality'] += 1
            elif confidence >= 0.5:
                quality_level = 'MEDIUM'
                results['qa_summary']['medium_quality'] += 1
            elif confidence >= 0.3:
                quality_level = 'LOW'
                results['qa_summary']['low_quality'] += 1
            else:
                quality_level = 'REJECTED'
                results['qa_summary']['rejected'] += 1
            
            results['qa_summary']['total_issues'] += len(qa_result.issues)
            
            print(f"  ✅ Quality: {quality_level} (Confidence: {confidence:.2f})")
            print(f"     ⚠️ Issues: {len(qa_result.issues)}")
            
            # Show key issues
            if qa_result.issues:
                for issue in qa_result.issues[:2]:
                    print(f"       • {issue}")
            
            # Add to results
            results['companies'].append({
                **company_data,
                'qa_result': {
                    'quality_level': quality_level,
                    'confidence_score': confidence,
                    'issues': qa_result.issues,
                    'corrections': qa_result.corrections
                }
            })
            
            # Add cleaned data if quality is acceptable
            if quality_level in ['HIGH', 'MEDIUM'] and qa_result.cleaned_data:
                results['cleaned_data'].append(qa_result.cleaned_data)
            
            results['successful_extractions'] += 1
            
        except Exception as e:
            logger.error(f"Error processing {company_name}: {e}")
            print(f"  ❌ Error: {str(e)}")
            results['companies'].append({
                'name': company_name,
                'rank': rank,
                'cik': cik,
                'success': False,
                'executives': [],
                'error': str(e)
            })
            results['failed_extractions'] += 1
    
    # Save results and generate reports
    await save_results_and_generate_reports(results)

async def save_results_and_generate_reports(results: Dict):
    """Save results and generate comprehensive reports"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw results
    raw_results_file = f"tests/results/fortune_100_raw_results_{timestamp}.json"
    os.makedirs(os.path.dirname(raw_results_file), exist_ok=True)
    
    with open(raw_results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate enhanced Excel report
    excel_file = await generate_enhanced_excel_report(results, timestamp)
    
    # Print comprehensive summary
    print_fortune_100_summary(results, raw_results_file, excel_file)

async def generate_enhanced_excel_report(results: Dict, timestamp: str) -> str:
    """Generate enhanced Excel report with confidence scores"""

    if not results['cleaned_data']:
        print("⚠️ No cleaned data to export")
        return None

    # Prepare data for different sheets
    executive_pay_breakdown = []
    list_of_executives = []
    key_findings = []
    qa_summary_data = []

    # Process cleaned companies
    for company in results['cleaned_data']:
        company_name = company['name']
        rank = company['rank']

        # Find QA result for confidence score
        qa_result = None
        for comp in results['companies']:
            if comp['name'] == company_name:
                qa_result = comp.get('qa_result', {})
                break

        company_confidence = qa_result.get('confidence_score', 0.0) if qa_result else 0.0
        company_quality = qa_result.get('quality_level', 'UNKNOWN') if qa_result else 'UNKNOWN'

        # Calculate company totals
        total_exec_pay = 0
        exec_count = 0
        ceo_pay = 0

        for exec_data in company.get('executives', []):
            exec_name = exec_data.get('name', '')
            exec_title = exec_data.get('title', '')
            total_comp = exec_data.get('total_compensation', 0)
            salary = exec_data.get('salary', 0)
            bonus = exec_data.get('bonus', 0)
            stock = exec_data.get('stock_awards', 0)
            options = exec_data.get('option_awards', 0)
            other = exec_data.get('other_compensation', 0)

            # Executive Pay Breakdown
            executive_pay_breakdown.append({
                'Company': company_name,
                'Fortune Rank': rank,
                'Executive Name': exec_name,
                'Title': exec_title,
                'Year': 2023,
                'Total Compensation': total_comp,
                'Salary': salary,
                'Bonus': bonus,
                'Stock Awards': stock,
                'Option Awards': options,
                'Other Compensation': other,
                'Data Quality': company_quality,
                'Confidence Score': company_confidence
            })

            # List of Executives
            list_of_executives.append({
                'Executive Name': exec_name,
                'Company': company_name,
                'Title': exec_title,
                '5-Year Total Pay': total_comp * 5,
                'Average Annual Pay': total_comp,
                'Data Quality': company_quality,
                'Confidence Score': company_confidence
            })

            total_exec_pay += total_comp
            exec_count += 1

            # Identify CEO pay
            if 'ceo' in exec_title.lower() or 'chief executive' in exec_title.lower():
                ceo_pay = total_comp

        # Key Findings
        key_findings.append({
            'Company': company_name,
            'Fortune Rank': rank,
            'Total Executive Pay': total_exec_pay,
            'Number of Executives': exec_count,
            'Average Executive Pay': total_exec_pay / exec_count if exec_count > 0 else 0,
            'CEO Pay': ceo_pay,
            'Data Quality': company_quality,
            'Confidence Score': company_confidence
        })

    # QA Summary for all companies
    for company in results['companies']:
        qa_result = company.get('qa_result', {})
        if qa_result:
            qa_summary_data.append({
                'Company': company['name'],
                'Fortune Rank': company['rank'],
                'Quality Level': qa_result.get('quality_level', 'UNKNOWN'),
                'Confidence Score': qa_result.get('confidence_score', 0.0),
                'Issues Count': len(qa_result.get('issues', [])),
                'Top Issue 1': qa_result.get('issues', [''])[0] if qa_result.get('issues') else '',
                'Top Issue 2': qa_result.get('issues', ['', ''])[1] if len(qa_result.get('issues', [])) > 1 else '',
                'Top Issue 3': qa_result.get('issues', ['', '', ''])[2] if len(qa_result.get('issues', [])) > 2 else '',
                'Data Status': 'INCLUDED' if qa_result.get('quality_level') in ['HIGH', 'MEDIUM'] else 'EXCLUDED'
            })

    # Create Excel file
    output_file = f"tests/results/fortune_100_executive_compensation_{timestamp}.xlsx"

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Executive Pay Breakdown sheet
        if executive_pay_breakdown:
            df_breakdown = pd.DataFrame(executive_pay_breakdown)
            df_breakdown['Confidence Score'] = df_breakdown['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_breakdown.to_excel(writer, sheet_name='Executive Pay Breakdown', index=False)

        # List of Executives sheet
        if list_of_executives:
            df_executives = pd.DataFrame(list_of_executives)
            df_executives = df_executives.sort_values('5-Year Total Pay', ascending=False)
            df_executives['Confidence Score'] = df_executives['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_executives.to_excel(writer, sheet_name='List of Executives', index=False)

        # Key Findings sheet
        if key_findings:
            df_findings = pd.DataFrame(key_findings)
            df_findings = df_findings.sort_values('Fortune Rank')
            df_findings['Confidence Score'] = df_findings['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_findings.to_excel(writer, sheet_name='Key Findings', index=False)

        # QA Summary sheet
        if qa_summary_data:
            df_qa = pd.DataFrame(qa_summary_data)
            df_qa = df_qa.sort_values('Fortune Rank')
            df_qa['Confidence Score'] = df_qa['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_qa.to_excel(writer, sheet_name='QA Summary', index=False)

    print(f"📊 Fortune 100 Excel report created: {output_file}")
    return output_file

def print_fortune_100_summary(results: Dict, raw_file: str, excel_file: str):
    """Print comprehensive Fortune 100 summary"""
    print("\n" + "=" * 70)
    print("🎯 FORTUNE 100 ANALYSIS SUMMARY")
    print("=" * 70)

    total = results['total_companies']
    successful = results['successful_extractions']
    failed = results['failed_extractions']
    qa_summary = results['qa_summary']

    print(f"📊 **PROCESSING RESULTS:**")
    print(f"   Total Companies: {total}")
    print(f"   Successful Extractions: {successful} ({successful/total*100:.1f}%)")
    print(f"   Failed Extractions: {failed} ({failed/total*100:.1f}%)")

    print(f"\n🔍 **DATA QUALITY RESULTS:**")
    print(f"   High Quality (≥70%): {qa_summary['high_quality']} ({qa_summary['high_quality']/total*100:.1f}%)")
    print(f"   Medium Quality (50-69%): {qa_summary['medium_quality']} ({qa_summary['medium_quality']/total*100:.1f}%)")
    print(f"   Low Quality (30-49%): {qa_summary['low_quality']} ({qa_summary['low_quality']/total*100:.1f}%)")
    print(f"   Rejected (<30%): {qa_summary['rejected']} ({qa_summary['rejected']/total*100:.1f}%)")

    usable = qa_summary['high_quality'] + qa_summary['medium_quality']
    print(f"   **USABLE FOR ANALYSIS: {usable} companies ({usable/total*100:.1f}%)**")

    print(f"\n📈 **CLEANED DATASET:**")
    print(f"   Companies with Clean Data: {len(results['cleaned_data'])}")
    print(f"   Total Issues Identified: {qa_summary['total_issues']}")
    print(f"   Average Issues per Company: {qa_summary['total_issues']/total:.1f}")

    # Calculate total executives and compensation
    total_executives = 0
    total_compensation = 0

    for company in results['cleaned_data']:
        for exec_data in company.get('executives', []):
            total_executives += 1
            total_compensation += exec_data.get('total_compensation', 0)

    print(f"   Total Validated Executives: {total_executives}")
    print(f"   Total Executive Compensation: ${total_compensation/1_000_000_000:.1f}B")

    print(f"\n💾 **OUTPUT FILES:**")
    print(f"   Raw Results: {raw_file}")
    print(f"   Excel Report: {excel_file}")
    print(f"   Enhanced with confidence scores and QA transparency")

    print(f"\n🚀 **NEXT STEPS:**")
    print(f"   1. Review {usable} high/medium quality companies")
    print(f"   2. Use Excel report for executive compensation analysis")
    print(f"   3. Compare Fortune 100 vs Fortune 50 results")
    print(f"   4. Generate insights on executive compensation trends")

    print("\n🎯 Fortune 100 analysis complete!")

if __name__ == "__main__":
    asyncio.run(run_fortune_100_analysis())
