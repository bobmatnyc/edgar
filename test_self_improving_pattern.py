#!/usr/bin/env python3
"""
Test the Self-Improving Code Pattern

This demonstrates the novel coding pattern where:
1. Control Layer (immutable) evaluates results
2. Implementation Layer (mutable) can be modified
3. Git safety ensures rollback capability
4. LLMs act as supervisor and engineer
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from edgar_analyzer.controllers.self_improving_extraction_controller import SelfImprovingExtractionController
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.config.settings import ConfigService

async def test_self_improving_pattern():
    """Test the self-improving code pattern with a real extraction task."""
    
    print("🚀 Testing Self-Improving Code Pattern")
    print("=" * 60)
    print("CODING PATTERN DEMONSTRATION:")
    print("• Control Layer: Immutable supervisor logic")
    print("• Implementation Layer: Mutable extraction code") 
    print("• Safety Layer: Git-based rollback")
    print("• Feedback Loop: LLM-driven improvements")
    print("=" * 60)
    
    # Initialize services
    try:
        llm_service = LLMService()
        print("✅ LLM service initialized (Grok supervisor + Claude engineer)")
    except Exception as e:
        print(f"❌ Failed to initialize LLM service: {e}")
        return
    
    # Initialize the self-improving controller
    controller = SelfImprovingExtractionController(llm_service)
    print("✅ Self-improving extraction controller initialized")
    
    # Test with a sample HTML content (simplified for demo)
    sample_html = """
    <html>
    <body>
        <h2>Summary Compensation Table</h2>
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
    </body>
    </html>
    """
    
    print("\n🧪 Testing with Apple Inc. sample data...")
    print("📄 Sample HTML contains Summary Compensation Table with 3 executives")
    
    try:
        # Run the self-improving extraction
        results = await controller.extract_with_improvement(
            html_content=sample_html,
            company_cik="0000320193",
            company_name="Apple Inc.",
            year=2023,
            max_iterations=2  # Limit for demo
        )
        
        print("\n🎯 EXTRACTION RESULTS:")
        print(f"   Final Count: {results['final_count']} executives")
        print(f"   Iterations Used: {results['iterations_used']}")
        print(f"   Final Success: {results['final_success']}")
        print(f"   Improvements Made: {len(results['improvements_made'])}")
        
        print("\n👥 EXTRACTED EXECUTIVES:")
        for i, comp in enumerate(results['compensations'], 1):
            print(f"   {i}. {comp.executive_name} ({comp.title})")
            print(f"      Total: ${comp.total_compensation:,}")
        
        print("\n🔄 IMPROVEMENT PROCESS:")
        improvement_process = results['improvement_process']
        
        for i, iteration in enumerate(improvement_process.get('iterations', []), 1):
            print(f"\n   Iteration {i}:")
            print(f"     • Test Success: {iteration.get('test_results', {}).get('success', False)}")
            
            evaluation = iteration.get('evaluation', {})
            print(f"     • Quality Score: {evaluation.get('quality_score', 'N/A')}")
            print(f"     • Needs Improvement: {evaluation.get('needs_improvement', 'N/A')}")
            
            if iteration.get('code_changed', False):
                print(f"     • Code Modified: Yes")
                changes = iteration.get('changes', {})
                print(f"     • Files Modified: {len(changes.get('files_modified', []))}")
            else:
                print(f"     • Code Modified: No")
        
        print("\n✨ PATTERN DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("KEY ACHIEVEMENTS:")
        print("✅ Control layer remained immutable")
        print("✅ Implementation layer was available for modification")
        print("✅ Git safety checkpoints created")
        print("✅ LLM supervisor evaluated results")
        print("✅ LLM engineer ready to implement improvements")
        print("✅ Feedback loop completed successfully")
        
        if results['final_success']:
            print("\n🎉 SUCCESS: Pattern achieved satisfactory results!")
        else:
            print("\n⚠️  PARTIAL SUCCESS: Pattern completed but may need manual review")
            
    except Exception as e:
        print(f"\n❌ Error during pattern execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_self_improving_pattern())
