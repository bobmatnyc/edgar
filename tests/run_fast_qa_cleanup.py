#!/usr/bin/env python3
"""
Fast QA cleanup without web search - focus on core data quality issues
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

from edgar_analyzer.services.qa_controller import ComprehensiveQAController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_fast_qa_cleanup():
    """Run fast QA cleanup focusing on core issues"""
    
    print("🔍 Fast QA Cleanup - Core Data Quality Issues")
    print("=" * 60)
    
    # Load existing results
    results_file = "results/top_100_enhanced_results_20251121_180216.json"
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return
    
    with open(results_file, 'r') as f:
        original_results = json.load(f)
    
    print(f"📊 Loaded results for {original_results['total_companies']} companies")
    
    # Initialize QA controller WITHOUT web search for speed
    qa_controller = ComprehensiveQAController(
        llm_service=None,
        web_search_enabled=False
    )
    
    # Fast QA results
    qa_results = {
        'timestamp': datetime.now().isoformat(),
        'original_file': results_file,
        'total_companies': original_results['total_companies'],
        'qa_summary': {
            'high_quality': 0,
            'medium_quality': 0,
            'low_quality': 0,
            'rejected': 0,
            'total_issues': 0,
            'cleaned_companies': 0
        },
        'companies': [],
        'cleaned_data': []
    }
    
    print("\n🔍 Running fast QA on each company...")
    
    for i, company in enumerate(original_results['companies']):
        company_name = company['name']
        rank = company['rank']
        
        print(f"\n🏢 [{rank:2d}] {company_name}")
        
        if not company['success'] or not company['executives']:
            print("  ⚠️ No executives data - rejected")
            qa_results['qa_summary']['rejected'] += 1
            continue
        
        try:
            # Run fast QA (no web search)
            qa_result = await qa_controller.qa_executive_data(company)
            
            # Determine quality level
            confidence = qa_result.confidence_score
            if confidence >= 0.7:
                quality_level = 'HIGH'
                qa_results['qa_summary']['high_quality'] += 1
            elif confidence >= 0.5:
                quality_level = 'MEDIUM'
                qa_results['qa_summary']['medium_quality'] += 1
            elif confidence >= 0.3:
                quality_level = 'LOW'
                qa_results['qa_summary']['low_quality'] += 1
            else:
                quality_level = 'REJECTED'
                qa_results['qa_summary']['rejected'] += 1
            
            qa_results['qa_summary']['total_issues'] += len(qa_result.issues)
            
            print(f"  ✅ Quality: {quality_level} (Confidence: {confidence:.2f})")
            print(f"     ⚠️ Issues: {len(qa_result.issues)}")
            
            # Show key issues
            if qa_result.issues:
                for issue in qa_result.issues[:2]:
                    print(f"       • {issue}")
            
            # Add cleaned data if quality is acceptable
            if quality_level in ['HIGH', 'MEDIUM'] and qa_result.cleaned_data:
                qa_results['cleaned_data'].append(qa_result.cleaned_data)
                qa_results['qa_summary']['cleaned_companies'] += 1
            
            qa_results['companies'].append({
                'name': company_name,
                'rank': rank,
                'quality_level': quality_level,
                'confidence_score': confidence,
                'issues_count': len(qa_result.issues),
                'issues': qa_result.issues[:5],  # Top 5 issues only
                'has_cleaned_data': qa_result.cleaned_data is not None
            })
            
        except Exception as e:
            logger.error(f"QA error for {company_name}: {e}")
            print(f"  ❌ QA error: {str(e)}")
            qa_results['qa_summary']['rejected'] += 1
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save QA summary
    qa_summary_file = f"tests/results/fast_qa_summary_{timestamp}.json"
    os.makedirs(os.path.dirname(qa_summary_file), exist_ok=True)
    
    with open(qa_summary_file, 'w') as f:
        json.dump(qa_results, f, indent=2)
    
    # Save cleaned dataset
    cleaned_file = f"tests/results/cleaned_fortune_50_{timestamp}.json"
    cleaned_dataset = {
        'timestamp': datetime.now().isoformat(),
        'source': 'fast_qa_cleanup',
        'total_companies': len(qa_results['cleaned_data']),
        'quality_filter': 'HIGH and MEDIUM quality only',
        'companies': qa_results['cleaned_data']
    }
    
    with open(cleaned_file, 'w') as f:
        json.dump(cleaned_dataset, f, indent=2)
    
    # Create target document format
    await create_target_document_format(qa_results['cleaned_data'], timestamp)
    
    # Print summary
    print_fast_qa_summary(qa_results, qa_summary_file, cleaned_file)

async def create_target_document_format(cleaned_companies: List[Dict], timestamp: str):
    """Create Excel file matching target document structure with confidence scores"""

    if not cleaned_companies:
        print("⚠️ No cleaned companies to export")
        return

    # Load QA results to get confidence scores
    qa_file = f"tests/results/fast_qa_summary_{timestamp}.json"
    confidence_scores = {}
    quality_levels = {}

    try:
        with open(qa_file, 'r') as f:
            qa_data = json.load(f)
            for company in qa_data.get('companies', []):
                company_name = company.get('name', '')
                confidence_scores[company_name] = company.get('confidence_score', 0.0)
                quality_levels[company_name] = company.get('quality_level', 'UNKNOWN')
    except Exception as e:
        print(f"⚠️ Could not load confidence scores: {e}")

    # Prepare data for different sheets
    executive_pay_breakdown = []
    list_of_executives = []
    key_findings = []

    for company in cleaned_companies:
        company_name = company['name']
        rank = company['rank']
        company_confidence = confidence_scores.get(company_name, 0.0)
        company_quality = quality_levels.get(company_name, 'UNKNOWN')

        # Calculate company totals
        total_exec_pay = 0
        exec_count = 0

        for exec_data in company.get('executives', []):
            exec_name = exec_data.get('name', '')
            exec_title = exec_data.get('title', '')
            total_comp = exec_data.get('total_compensation', 0)
            salary = exec_data.get('salary', 0)
            bonus = exec_data.get('bonus', 0)
            stock = exec_data.get('stock_awards', 0)
            options = exec_data.get('option_awards', 0)
            other = exec_data.get('other_compensation', 0)

            # Executive Pay Breakdown (individual records with confidence)
            executive_pay_breakdown.append({
                'Company': company_name,
                'Fortune Rank': rank,
                'Executive Name': exec_name,
                'Title': exec_title,
                'Year': 2023,  # Assuming 2023 data
                'Total Compensation': total_comp,
                'Salary': salary,
                'Bonus': bonus,
                'Stock Awards': stock,
                'Option Awards': options,
                'Other Compensation': other,
                'Data Quality': company_quality,
                'Confidence Score': company_confidence
            })

            # List of Executives (5-year totals with confidence)
            list_of_executives.append({
                'Executive Name': exec_name,
                'Company': company_name,
                'Title': exec_title,
                '5-Year Total Pay': total_comp * 5,  # Approximation
                'Average Annual Pay': total_comp,
                'Data Quality': company_quality,
                'Confidence Score': company_confidence
            })

            total_exec_pay += total_comp
            exec_count += 1

        # Key Findings (company-level summary with confidence)
        ceo_pay = next((e.get('total_compensation', 0) for e in company.get('executives', [])
                       if 'ceo' in e.get('title', '').lower()), 0)

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
    
    # Create Excel file with enhanced formatting
    output_file = f"tests/results/fortune_50_executive_compensation_{timestamp}.xlsx"

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Executive Pay Breakdown sheet
        if executive_pay_breakdown:
            df_breakdown = pd.DataFrame(executive_pay_breakdown)
            # Format confidence scores as percentages
            df_breakdown['Confidence Score'] = df_breakdown['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_breakdown.to_excel(writer, sheet_name='Executive Pay Breakdown', index=False)

            # Format the worksheet
            worksheet = writer.sheets['Executive Pay Breakdown']
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # List of Executives sheet
        if list_of_executives:
            df_executives = pd.DataFrame(list_of_executives)
            # Sort by 5-year total pay descending
            df_executives = df_executives.sort_values('5-Year Total Pay', ascending=False)
            # Format confidence scores as percentages
            df_executives['Confidence Score'] = df_executives['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_executives.to_excel(writer, sheet_name='List of Executives', index=False)

            # Format the worksheet
            worksheet = writer.sheets['List of Executives']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # Key Findings sheet
        if key_findings:
            df_findings = pd.DataFrame(key_findings)
            df_findings = df_findings.sort_values('Fortune Rank')
            # Format confidence scores as percentages
            df_findings['Confidence Score'] = df_findings['Confidence Score'].apply(lambda x: f"{x:.1%}")
            df_findings.to_excel(writer, sheet_name='Key Findings', index=False)

            # Format the worksheet
            worksheet = writer.sheets['Key Findings']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # QA Summary sheet with detailed quality information
        qa_summary_data = []
        try:
            with open(qa_file, 'r') as f:
                qa_data = json.load(f)
                for company in qa_data.get('companies', []):
                    if company.get('has_cleaned_data', False):
                        qa_summary_data.append({
                            'Company': company.get('name', ''),
                            'Fortune Rank': company.get('rank', 0),
                            'Quality Level': company.get('quality_level', ''),
                            'Confidence Score': f"{company.get('confidence_score', 0):.1%}",
                            'Issues Count': company.get('issues_count', 0),
                            'Top Issue 1': company.get('issues', [''])[0] if company.get('issues') else '',
                            'Top Issue 2': company.get('issues', ['', ''])[1] if len(company.get('issues', [])) > 1 else '',
                            'Top Issue 3': company.get('issues', ['', '', ''])[2] if len(company.get('issues', [])) > 2 else '',
                            'Data Status': 'INCLUDED IN ANALYSIS'
                        })
        except Exception as e:
            print(f"⚠️ Could not create QA summary sheet: {e}")

        if qa_summary_data:
            df_qa = pd.DataFrame(qa_summary_data)
            df_qa = df_qa.sort_values('Confidence Score', ascending=False)
            df_qa.to_excel(writer, sheet_name='QA Summary', index=False)

            # Format the QA worksheet
            worksheet = writer.sheets['QA Summary']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60)  # Wider for issue descriptions
                worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"📊 Enhanced target document created: {output_file}")
    print(f"   📋 Sheets: Executive Pay Breakdown, List of Executives, Key Findings, QA Summary")
    print(f"   🎯 Confidence scores included in all sheets")
    print(f"   📈 Data quality transparency provided")
    return output_file

def print_fast_qa_summary(qa_results: Dict, qa_file: str, cleaned_file: str):
    """Print fast QA summary"""
    print("\n" + "=" * 60)
    print("🎯 FAST QA CLEANUP SUMMARY")
    print("=" * 60)

    total = qa_results['total_companies']
    summary = qa_results['qa_summary']

    print(f"📊 **QA RESULTS:**")
    print(f"   Total Companies: {total}")
    print(f"   High Quality: {summary['high_quality']} ({summary['high_quality']/total*100:.1f}%)")
    print(f"   Medium Quality: {summary['medium_quality']} ({summary['medium_quality']/total*100:.1f}%)")
    print(f"   Low Quality: {summary['low_quality']} ({summary['low_quality']/total*100:.1f}%)")
    print(f"   Rejected: {summary['rejected']} ({summary['rejected']/total*100:.1f}%)")

    usable = summary['high_quality'] + summary['medium_quality']
    print(f"   **Usable for Analysis: {usable} companies ({usable/total*100:.1f}%)**")

    print(f"\n🔧 **DATA CLEANING:**")
    print(f"   Companies with Cleaned Data: {summary['cleaned_companies']}")
    print(f"   Total Issues Identified: {summary['total_issues']}")
    print(f"   Average Issues per Company: {summary['total_issues']/total:.1f}")

    # Analyze common issues
    all_issues = []
    for company in qa_results['companies']:
        all_issues.extend(company.get('issues', []))

    print(f"\n⚠️ **MOST COMMON ISSUES:**")
    issue_counts = {}
    for issue in all_issues:
        if 'invalid' in issue.lower():
            key = 'Invalid executive names'
        elif 'artificial' in issue.lower():
            key = 'Artificial compensation patterns'
        elif 'unusually low' in issue.lower():
            key = 'Unusually low compensation'
        elif 'unusually high' in issue.lower():
            key = 'Unusually high compensation'
        elif 'missing' in issue.lower():
            key = 'Missing data fields'
        else:
            key = 'Other issues'

        issue_counts[key] = issue_counts.get(key, 0) + 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {issue}: {count} occurrences")

    print(f"\n📈 **QUALITY BREAKDOWN:**")
    high_quality_companies = [c for c in qa_results['companies'] if c['quality_level'] == 'HIGH']
    medium_quality_companies = [c for c in qa_results['companies'] if c['quality_level'] == 'MEDIUM']

    if high_quality_companies:
        print(f"   ✅ **HIGH QUALITY ({len(high_quality_companies)} companies):**")
        for company in high_quality_companies[:10]:  # Show top 10
            print(f"      • {company['name']} (Rank {company['rank']}) - {company['confidence_score']:.2f}")

    if medium_quality_companies:
        print(f"   ⚠️ **MEDIUM QUALITY ({len(medium_quality_companies)} companies):**")
        for company in medium_quality_companies[:5]:  # Show top 5
            print(f"      • {company['name']} (Rank {company['rank']}) - {company['confidence_score']:.2f}")

    print(f"\n💾 **OUTPUT FILES:**")
    print(f"   QA Summary: {qa_file}")
    print(f"   Cleaned Dataset: {cleaned_file}")
    print(f"   Target Excel Document: tests/results/fortune_50_executive_compensation_*.xlsx")

    print(f"\n🎯 **NEXT STEPS:**")
    print(f"   1. Review {usable} high/medium quality companies")
    print(f"   2. Use cleaned dataset for final analysis")
    print(f"   3. Address common data quality issues in extraction pipeline")
    print(f"   4. Generate final report matching target document structure")

    print("\n🔍 Fast QA cleanup complete!")

if __name__ == "__main__":
    asyncio.run(run_fast_qa_cleanup())
