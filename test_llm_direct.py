#!/usr/bin/env python3
"""
Test LLM direct parsing with a smaller, more focused HTML snippet
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from edgar_analyzer.services.llm_service import LLMService

async def test_llm_direct():
    """Test LLM parsing with a focused HTML snippet"""
    
    try:
        llm_service = LLMService()
        print("✅ LLM service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LLM service: {e}")
        return
    
    # Sample HTML that contains executive compensation data (simplified)
    sample_html = """
    <table>
        <tr>
            <th>Name and Principal Position</th>
            <th>Year</th>
            <th>Salary ($)</th>
            <th>Bonus ($)</th>
            <th>Stock Awards ($)</th>
            <th>Total ($)</th>
        </tr>
        <tr>
            <td>Timothy D. Cook<br/>Chief Executive Officer</td>
            <td>2023</td>
            <td>3,000,000</td>
            <td>0</td>
            <td>46,000,000</td>
            <td>63,209,845</td>
        </tr>
        <tr>
            <td>Luca Maestri<br/>Senior Vice President, Chief Financial Officer</td>
            <td>2023</td>
            <td>1,000,000</td>
            <td>2,800,000</td>
            <td>22,000,000</td>
            <td>26,961,226</td>
        </tr>
        <tr>
            <td>Katherine L. Adams<br/>Senior Vice President, General Counsel</td>
            <td>2023</td>
            <td>1,000,000</td>
            <td>2,800,000</td>
            <td>22,000,000</td>
            <td>26,961,226</td>
        </tr>
    </table>
    """
    
    print("Testing LLM with focused compensation table HTML...")
    
    try:
        executives = await llm_service.parse_proxy_compensation_table(
            sample_html, "Apple Inc.", 2023
        )
        
        print(f"\n🎯 LLM extracted {len(executives)} executives:")
        
        for i, exec_data in enumerate(executives, 1):
            print(f"  {i}. {exec_data['name']} ({exec_data['title']})")
            print(f"     Total: ${exec_data['total_compensation']:,}")
            print(f"     Confidence: {exec_data.get('confidence', 'N/A')}")
            print()
            
        if executives:
            print("✅ LLM successfully parsed the compensation table!")
            
            # Test validation
            print("\n🔍 Testing LLM validation...")
            
            # Convert to mock ExecutiveCompensation objects for validation
            from edgar_analyzer.models.company import ExecutiveCompensation
            from decimal import Decimal
            
            mock_compensations = []
            for exec_data in executives:
                # Handle null values properly
                def safe_decimal(value):
                    if value is None:
                        return Decimal('0')
                    return Decimal(str(value))

                comp = ExecutiveCompensation(
                    company_cik="0000320193",
                    fiscal_year=2023,
                    executive_name=exec_data['name'],
                    title=exec_data['title'],
                    total_compensation=safe_decimal(exec_data['total_compensation']),
                    salary=safe_decimal(exec_data.get('salary', 0)),
                    bonus=safe_decimal(exec_data.get('bonus', 0)),
                    stock_awards=safe_decimal(exec_data.get('stock_awards', 0)),
                    option_awards=safe_decimal(exec_data.get('option_awards', 0)),
                )
                mock_compensations.append(comp)
            
            validation = await llm_service.validate_compensation_data(
                mock_compensations, "Apple Inc.", 2023
            )
            
            print(f"📊 Validation Results:")
            print(f"   Quality Score: {validation.get('overall_quality_score', 0):.2f}")
            print(f"   Data Appears Authentic: {validation.get('data_appears_authentic', False)}")
            print(f"   Issues Found: {len(validation.get('issues_found', []))}")
            
            if validation.get('issues_found'):
                print(f"   Issues: {validation['issues_found']}")
            
            print(f"   Summary: {validation.get('summary', 'N/A')}")
            
        else:
            print("❌ LLM failed to extract any executives")
            
    except Exception as e:
        print(f"Error during LLM testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_direct())
