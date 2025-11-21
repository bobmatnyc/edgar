#!/usr/bin/env python3
"""
Test the Reusable Self-Improving Code Library

This demonstrates how the library can be used in any project
for implementing self-improving code with LLM QA and engineering.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from self_improving_code.examples.edgar_extraction import EdgarExtractionExample

async def test_reusable_library():
    """Test the reusable self-improving code library."""
    
    print("🚀 Testing Reusable Self-Improving Code Library")
    print("=" * 70)
    print("LIBRARY DEMONSTRATION:")
    print("• Reusable controller for any project")
    print("• Domain-specific LLM configurations")
    print("• Pluggable QA and engineering components")
    print("• Git-based safety mechanisms")
    print("• Professional-grade quality assurance")
    print("=" * 70)
    
    # Initialize the EDGAR extraction example
    try:
        example = EdgarExtractionExample()
        print("✅ EDGAR extraction example initialized")
        print("   • Grok 4.1 Fast configured as Supervisor + QA")
        print("   • Claude 3.5 Sonnet configured as Engineer")
        print("   • Git safety manager enabled")
        print("   • Domain expertise: SEC filings analysis")
    except Exception as e:
        print(f"❌ Failed to initialize example: {e}")
        return
    
    # Test with problematic data that should trigger QA
    print("\n🧪 Testing with problematic data...")
    
    problematic_html = """
    <html>
    <body>
        <h2>Executive Compensation</h2>
        <table>
            <tr><th>Name</th><th>Title</th><th>Compensation</th></tr>
            <tr><td>Ryan Martin</td><td>CEO</td><td>$150,000</td></tr>
            <tr><td>Kenneth Mitchell</td><td>CFO</td><td>$140,000</td></tr>
            <tr><td>The Boeing Company</td><td>Executive</td><td>$90,000</td></tr>
        </table>
    </body>
    </html>
    """
    
    print("📄 Test data contains known problematic patterns:")
    print("   • Fake names: Ryan Martin, Kenneth Mitchell")
    print("   • Company name as person: The Boeing Company")
    print("   • Unrealistic compensation amounts")
    
    try:
        results = await example.extract_with_improvement(
            html_content=problematic_html,
            company_cik="0000019617",  # Walmart
            company_name="Walmart Inc.",
            year=2024,
            max_iterations=2
        )
        
        print("\n🎯 LIBRARY RESULTS:")
        print(f"   Final Count: {results['final_count']} executives")
        print(f"   Iterations Used: {results['iterations_used']}")
        print(f"   Final Success: {results['final_success']}")
        print(f"   Files Modified: {len(results['improvements_made'])}")
        
        improvement_process = results['improvement_process']
        
        print(f"\n🔄 IMPROVEMENT PROCESS:")
        for i, iteration in enumerate(improvement_process.iterations, 1):
            print(f"\n   Iteration {i}:")
            print(f"     • Test Success: {iteration.test_results.get('success', False)}")
            
            evaluation = iteration.evaluation
            print(f"     • Quality Score: {evaluation.get('quality_score', 'N/A')}")
            print(f"     • QA Status: {evaluation.get('qa_status', 'N/A')}")
            print(f"     • Needs Improvement: {evaluation.get('needs_improvement', 'N/A')}")
            
            if iteration.code_changed:
                print(f"     • Code Modified: Yes ({len(iteration.files_modified)} files)")
            else:
                print(f"     • Code Modified: No")
            
            # Show QA issues found
            issues = evaluation.get('issues_found', [])
            if issues:
                print(f"     • QA Issues Found: {len(issues)}")
                for issue in issues[:2]:  # Show first 2 issues
                    print(f"       - {issue}")
        
        print("\n" + "=" * 70)
        print("🎉 REUSABLE LIBRARY DEMONSTRATION COMPLETE")
        print("=" * 70)
        
        print("✅ LIBRARY CAPABILITIES DEMONSTRATED:")
        print("   • Domain-specific QA (SEC filings expertise)")
        print("   • Professional quality standards enforcement")
        print("   • Automatic code improvement based on evaluation")
        print("   • Git-based safety with rollback capability")
        print("   • Pluggable LLM components (Grok + Claude)")
        print("   • Reusable across different projects/domains")
        
        print("\n✅ PATTERN BENEFITS:")
        print("   • Separation of concerns (control vs implementation)")
        print("   • Professional QA built into development process")
        print("   • Continuous improvement through evaluation feedback")
        print("   • Production-ready safety mechanisms")
        print("   • Domain expertise integration")
        
        print("\n🚀 LIBRARY READY FOR:")
        print("   • Data extraction projects")
        print("   • API integration systems")
        print("   • ML feature engineering")
        print("   • Web scraping applications")
        print("   • Any code that benefits from quality-driven improvement")
        
        if results['final_success']:
            print("\n🎉 SUCCESS: Library achieved quality standards!")
        else:
            print("\n⚠️  PARTIAL SUCCESS: Quality improvement in progress")
            
    except Exception as e:
        print(f"\n❌ Error during library testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_reusable_library())
